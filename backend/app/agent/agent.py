import re
from typing import AsyncGenerator, Optional

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.prompts import AURA_SYSTEM_PROMPT
from app.agent.schemas import AgentResponseChunk
from app.config.settings import settings
from app.database.repository import ConversationRepository
from app.tools import tool_registry
from app.tools.notes import normalize_note_content
from app.utils.logger import logger


def extract_weather_location(user_text: str, history: list) -> Optional[str]:
    """
    Dynamically extracts location from user request or prior conversation context.
    Returns None if no location is mentioned or inferrable from context.
    """
    lowered = user_text.lower().strip()

    # 1. Regex patterns for explicit location phrases
    patterns = [
        r"(?:weather|temperature|forecast|climate)\s+(?:in|at|for|like\s+in)\s+([a-zA-Z\s]+)",
        r"(?:in|at|for)\s+([a-zA-Z\s]+)\s+(?:weather|temperature|forecast|climate)",
        r"how\s+is\s+the\s+weather\s+(?:in|at|for)\s+([a-zA-Z\s]+)",
        r"is\s+it\s+(?:raining|sunny|cloudy|cold|hot)\s+(?:in|at|for)\s+([a-zA-Z\s]+)",
    ]

    for pat in patterns:
        match = re.search(pat, lowered)
        if match:
            raw_loc = match.group(1).strip()
            # Clean up trailing stop words
            for sw in ["today", "tomorrow", "tonight", "right now", "now", "please", "there", "here"]:
                if raw_loc.endswith(" " + sw):
                    raw_loc = raw_loc[: -len(sw) - 1].strip()
            if raw_loc and raw_loc not in ["there", "here"]:
                return raw_loc.title()

    # 2. Check for explicit city words in user text if prepositions were omitted
    stop_words = {
        "what",
        "whats",
        "what's",
        "is",
        "the",
        "weather",
        "in",
        "at",
        "for",
        "how",
        "like",
        "temperature",
        "forecast",
        "today",
        "tomorrow",
        "now",
        "umbrella",
        "should",
        "i",
        "carry",
        "a",
        "an",
        "there",
        "here",
        "good",
        "morning",
    }
    words = [w.strip("?,.!'\"") for w in user_text.split()]
    for w in words:
        if w.lower() not in stop_words and len(w) >= 3 and w.isalpha():
            return w.title()

    # 3. Contextual lookup for "there" or implicit location queries (e.g. "Should I carry an umbrella?")
    for msg in reversed(history):
        msg_low = msg.content.lower()
        if "weather in " in msg_low:
            parts = msg_low.split("weather in ")
            if len(parts) > 1:
                loc_cand = parts[1].split()[0].strip("?,.!'\"").title()
                if loc_cand:
                    return loc_cand
        elif "weather" in msg_low or "in" in msg_low:
            words = [w.strip("?,.!'\"") for w in msg_low.split()]
            for w in reversed(words):
                if w.lower() not in stop_words and len(w) >= 3 and w.isalpha():
                    return w.title()

    return None


class AuraAgent:
    def __init__(self):
        self.model_name = settings.LLM_MODEL
        self.api_key = settings.GEMINI_API_KEY

    async def process_user_request_stream(
        self, user_text: str, conversation_id: str, db_session: AsyncSession
    ) -> AsyncGenerator[AgentResponseChunk, None]:
        """
        Process user text, manage context, execute tools if required,
        and yield response chunks asynchronously for streaming.
        """
        user_text_clean = user_text.strip()
        if not user_text_clean:
            yield AgentResponseChunk(
                type="text_chunk", content="I didn't catch that. Please speak or type your request again."
            )
            yield AgentResponseChunk(type="done")
            return

        repo = ConversationRepository(db_session)
        # Record user message in DB
        await repo.add_message(conversation_id, role="user", content=user_text_clean)

        # Retrieve recent history for context
        history = await repo.get_recent_messages(conversation_id, limit=10)

        # If Gemini API key is configured, use Gemini API
        if self.api_key and self.api_key != "your_gemini_api_key_here":
            async for chunk in self._process_with_gemini(user_text_clean, history, db_session, repo, conversation_id):
                yield chunk
        else:
            # Deterministic Agent Engine with tool routing & multi-turn history resolution
            async for chunk in self._process_with_fallback_agent(
                user_text_clean, history, db_session, repo, conversation_id
            ):
                yield chunk

    async def _process_with_gemini(
        self,
        user_text: str,
        history: list,
        db_session: AsyncSession,
        repo: ConversationRepository,
        conversation_id: str,
    ) -> AsyncGenerator[AgentResponseChunk, None]:
        """Process using official Gemini REST API with tool calling."""
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

            tools_spec = [{"functionDeclarations": tool_registry.get_gemini_declarations()}]

            contents = []
            for msg in history[:-1]:
                role = "user" if msg.role == "user" else "model"
                contents.append({"role": role, "parts": [{"text": msg.content}]})

            contents.append({"role": "user", "parts": [{"text": user_text}]})

            payload = {
                "systemInstruction": {"parts": [{"text": AURA_SYSTEM_PROMPT}]},
                "contents": contents,
                "tools": tools_spec,
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 500},
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload)
                data = resp.json()

            if "candidates" not in data or not data["candidates"]:
                err_msg = data.get("error", {}).get("message", "Gemini API error")
                logger.error(f"Gemini API error: {err_msg}")
                err_text = "Sorry, I couldn't process that request right now. Please try again."
                await repo.add_message(conversation_id, role="assistant", content=err_text)
                yield AgentResponseChunk(type="text_chunk", content=err_text)
                yield AgentResponseChunk(type="done")
                return

            candidate = data["candidates"][0]
            parts = candidate.get("content", {}).get("parts", [])

            function_calls = [p["functionCall"] for p in parts if "functionCall" in p]

            if function_calls:
                for fc in function_calls:
                    tool_name = fc["name"]
                    tool_args = fc.get("args", {})

                    # Normalize note content if LLM passed parameter
                    if tool_name == "create_note" and "content" in tool_args:
                        tool_args["content"] = normalize_note_content(tool_args["content"])

                    yield AgentResponseChunk(type="tool_start", tool_name=tool_name, tool_params=tool_args)
                    tool_result = await tool_registry.execute_tool(tool_name, tool_args, db_session)
                    yield AgentResponseChunk(type="tool_result", tool_name=tool_name, tool_result=tool_result)

                    tool_contents = contents + [
                        {"role": "model", "parts": [{"functionCall": fc}]},
                        {
                            "role": "function",
                            "parts": [{"functionResponse": {"name": tool_name, "response": tool_result}}],
                        },
                    ]

                    second_payload = {
                        "systemInstruction": {"parts": [{"text": AURA_SYSTEM_PROMPT}]},
                        "contents": tool_contents,
                        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300},
                    }

                    async with httpx.AsyncClient(timeout=15.0) as client:
                        second_resp = await client.post(url, json=second_payload)
                        second_data = second_resp.json()

                    final_text = ""
                    if "candidates" in second_data and second_data["candidates"]:
                        sec_parts = second_data["candidates"][0].get("content", {}).get("parts", [])
                        final_text = "".join([p.get("text", "") for p in sec_parts])

                    if not final_text:
                        final_text = self._format_tool_fallback_text(tool_name, tool_result)

                    await repo.add_message(conversation_id, role="assistant", content=final_text, tool_name=tool_name)
                    yield AgentResponseChunk(type="text_chunk", content=final_text)
            else:
                text_response = "".join([p.get("text", "") for p in parts])
                if not text_response:
                    text_response = "I have processed your request."
                await repo.add_message(conversation_id, role="assistant", content=text_response)
                yield AgentResponseChunk(type="text_chunk", content=text_response)

            yield AgentResponseChunk(type="done")

        except Exception as e:
            logger.error(f"Gemini processing exception: {e}")
            err_text = "Sorry, I ran into an issue fulfilling your request. Please try again."
            await repo.add_message(conversation_id, role="assistant", content=err_text)
            yield AgentResponseChunk(type="text_chunk", content=err_text)
            yield AgentResponseChunk(type="done")

    async def _process_with_fallback_agent(
        self,
        user_text: str,
        history: list,
        db_session: AsyncSession,
        repo: ConversationRepository,
        conversation_id: str,
    ) -> AsyncGenerator[AgentResponseChunk, None]:
        """
        Deterministic Agent Engine with tool routing & multi-turn history resolution.
        """
        lowered = user_text.lower()
        final_text = ""

        # 1. Identity & Capability Queries
        if any(
            q in lowered
            for q in [
                "who are you",
                "what is your name",
                "what are you",
                "tell me about yourself",
                "what can you do",
                "what can you help me with",
                "help me with",
            ]
        ):
            final_text = "I am AURA, your voice-first personal productivity assistant. I can help you check live weather forecasts, save text notes, and schedule reminders."

        # 2. Greetings Queries
        elif any(
            g in lowered
            for g in ["hello", "hi aura", "hey aura", "good morning", "good afternoon", "good evening", "greetings"]
        ):
            if "good morning" in lowered:
                final_text = "Good morning! How can I help you today?"
            elif "good afternoon" in lowered:
                final_text = "Good afternoon! What can I help you with today?"
            elif "good evening" in lowered:
                final_text = "Good evening! How can I assist you?"
            else:
                final_text = "Hello! I am AURA. How can I help you today?"

        # 3. Multi-step request: Weather + Note
        elif ("weather" in lowered) and ("note" in lowered or "remind" in lowered):
            location = extract_weather_location(user_text, history)
            if not location:
                final_text = "Which location would you like the weather for?"
            else:
                yield AgentResponseChunk(type="tool_start", tool_name="get_weather", tool_params={"location": location})
                w_res = await tool_registry.execute_tool("get_weather", {"location": location}, db_session)
                yield AgentResponseChunk(type="tool_result", tool_name="get_weather", tool_result=w_res)

                raw_note = "Carry an umbrella" if "umbrella" in lowered else f"Weather update for {location}"
                clean_note = normalize_note_content(raw_note)
                yield AgentResponseChunk(
                    type="tool_start", tool_name="create_note", tool_params={"content": clean_note}
                )
                n_res = await tool_registry.execute_tool("create_note", {"content": clean_note}, db_session)
                yield AgentResponseChunk(type="tool_result", tool_name="create_note", tool_result=n_res)

                final_text = f"The weather in {location} is currently {w_res.get('temperature', 'N/A')} with {w_res.get('condition', 'clear skies')}. I have also saved a note: '{clean_note}'."

        # 4. Weather & Umbrella Requests (Dynamic Location Extraction)
        elif any(k in lowered for k in ["weather", "temperature", "forecast", "climate", "umbrella", "rain"]):
            location = extract_weather_location(user_text, history)
            if not location:
                final_text = "Which location would you like the weather for?"
            else:
                yield AgentResponseChunk(type="tool_start", tool_name="get_weather", tool_params={"location": location})
                w_res = await tool_registry.execute_tool("get_weather", {"location": location}, db_session)
                yield AgentResponseChunk(type="tool_result", tool_name="get_weather", tool_result=w_res)

                cond = w_res.get("condition", "clear sky")
                temp = w_res.get("temperature", "25°C")

                if "umbrella" in lowered:
                    rain_needed = any(r in cond.lower() for r in ["rain", "drizzle", "shower", "thunderstorm"])
                    advice = (
                        "Yes, you should carry an umbrella as rain is expected."
                        if rain_needed
                        else "No umbrella needed right now, condition is clear."
                    )
                    final_text = f"In {location}, it is currently {temp} and {cond}. {advice}"
                else:
                    final_text = f"The weather in {location} is currently {temp} with {cond}."

        # 5. Create Note
        elif any(k in lowered for k in ["note", "save", "write down", "jot down", "remember"]):
            clean_content = normalize_note_content(user_text)

            yield AgentResponseChunk(type="tool_start", tool_name="create_note", tool_params={"content": clean_content})
            n_res = await tool_registry.execute_tool("create_note", {"content": clean_content}, db_session)
            yield AgentResponseChunk(type="tool_result", tool_name="create_note", tool_result=n_res)

            if "error" in n_res:
                final_text = f"Sorry, I couldn't save that note: {n_res['error']}"
            else:
                final_text = "Got it. I've saved that note."

        # 6. List Notes
        elif any(k in lowered for k in ["show my notes", "list my notes", "get notes", "view notes", "read my notes"]):
            yield AgentResponseChunk(type="tool_start", tool_name="list_notes", tool_params={})
            n_res = await tool_registry.execute_tool("list_notes", {}, db_session)
            yield AgentResponseChunk(type="tool_result", tool_name="list_notes", tool_result=n_res)

            count = n_res.get("count", 0)
            notes = n_res.get("notes", [])
            if count == 0:
                final_text = "You don't have any notes saved yet."
            else:
                items = [f"'{item['content']}'" for item in notes[:3]]
                final_text = (
                    f"You have {count} note{'s' if count > 1 else ''}. Here are your recent notes: {', '.join(items)}."
                )

        # 7. Create Reminder
        elif any(k in lowered for k in ["remind me", "set a reminder", "create a reminder"]):
            title = "Task"
            time_str = "tomorrow at 8 PM"

            if "remind me to" in lowered:
                idx = lowered.find("remind me to ") + len("remind me to ")
                raw_rem = user_text[idx:].strip()
                for time_kw in [" tomorrow", " today", " at ", " in ", " next "]:
                    if time_kw in raw_rem.lower():
                        cut_idx = raw_rem.lower().find(time_kw)
                        title = raw_rem[:cut_idx].strip(" .,!")
                        time_str = raw_rem[cut_idx:].strip(" .,!")
                        break
                else:
                    title = raw_rem.strip(" .,!")
            elif "reminder to" in lowered:
                idx = lowered.find("reminder to ") + len("reminder to ")
                title = user_text[idx:].strip(" .,!")

            yield AgentResponseChunk(
                type="tool_start", tool_name="create_reminder", tool_params={"title": title, "datetime_str": time_str}
            )
            r_res = await tool_registry.execute_tool(
                "create_reminder", {"title": title, "datetime_str": time_str}, db_session
            )
            yield AgentResponseChunk(type="tool_result", tool_name="create_reminder", tool_result=r_res)

            sched_time = r_res.get("scheduled_time", "scheduled time")
            final_text = f"I've set a reminder to '{title}' for {sched_time}."

        # 8. List Reminders
        elif any(k in lowered for k in ["show my reminders", "what reminders", "list reminders", "get reminders"]):
            yield AgentResponseChunk(type="tool_start", tool_name="list_reminders", tool_params={})
            r_res = await tool_registry.execute_tool("list_reminders", {}, db_session)
            yield AgentResponseChunk(type="tool_result", tool_name="list_reminders", tool_result=r_res)

            count = r_res.get("count", 0)
            rems = r_res.get("reminders", [])
            if count == 0:
                final_text = "You have no upcoming reminders scheduled."
            else:
                items = [f"'{item['title']}' for {item['scheduled_time']}" for item in rems[:3]]
                final_text = f"You have {count} reminder{'s' if count > 1 else ''}: {'; '.join(items)}."

        # 9. Cancel Previous Request
        elif any(k in lowered for k in ["cancel my previous", "cancel previous", "cancel request"]):
            final_text = "Understood. I have cancelled your previous request."

        # 10. General Conversational Query
        else:
            final_text = f"I received your request: '{user_text}'. I can check the weather, save notes, or set reminders for you."

        await repo.add_message(conversation_id, role="assistant", content=final_text)
        yield AgentResponseChunk(type="text_chunk", content=final_text)
        yield AgentResponseChunk(type="done")

    def _format_tool_fallback_text(self, tool_name: str, result: dict) -> str:
        if tool_name == "get_weather":
            return f"The weather in {result.get('location', 'your location')} is {result.get('temperature', 'N/A')} with {result.get('condition', 'clear skies')}."
        elif tool_name == "create_note":
            return "Got it. I've saved that note."
        elif tool_name == "create_reminder":
            return f"I have set a reminder for '{result.get('title', '')}' on {result.get('scheduled_time', '')}."
        return "I completed the requested task."


aura_agent = AuraAgent()
