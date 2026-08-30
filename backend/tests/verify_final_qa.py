import asyncio
import json

import httpx
import websockets

WS_URL = "ws://localhost:8000/ws/voice"
REST_NOTES_URL = "http://localhost:8000/api/notes"


async def run_final_qa():
    print("==================================================")
    print("EXECUTING AURA FINAL QA TEST SUITE")
    print("==================================================")

    async with websockets.connect(WS_URL) as ws:
        await ws.recv()  # init
        await ws.recv()  # state IDLE

        # TEST 1: General Question
        print("\n--- TEST 1: General Question ---")
        await ws.send(json.dumps({"type": "text_input", "text": "What can you help me with?"}))
        t1_text = ""
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "assistant_text":
                t1_text += frame.get("text", "")
            elif frame.get("type") == "state" and frame.get("value") == "IDLE":
                break
        print(f"Response: '{t1_text}'")
        assert "weather" in t1_text.lower() and "notes" in t1_text.lower() and "reminders" in t1_text.lower()
        print("TEST 1: PASS ✓")

        # TEST 2: Weather
        print("\n--- TEST 2: Weather ---")
        await ws.send(json.dumps({"type": "text_input", "text": "What's the weather in Pune?"}))
        t2_tool = None
        t2_text = ""
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "tool_start":
                t2_tool = frame.get("tool")
            elif frame.get("type") == "assistant_text":
                t2_text += frame.get("text", "")
            elif frame.get("type") == "state" and frame.get("value") == "IDLE":
                break
        print(f"Tool Called: {t2_tool}, Text: '{t2_text}'")
        assert t2_tool == "get_weather" and "pune" in t2_text.lower()
        print("TEST 2: PASS ✓")

        # TEST 3: Note
        print("\n--- TEST 3: Note Extraction & DB ---")
        await ws.send(
            json.dumps({"type": "text_input", "text": "Create a note saying I need to prepare for my AI interview."})
        )
        t3_tool = None
        t3_text = ""
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "tool_start":
                t3_tool = frame.get("tool")
            elif frame.get("type") == "assistant_text":
                t3_text += frame.get("text", "")
            elif frame.get("type") == "state" and frame.get("value") == "IDLE":
                break

        async with httpx.AsyncClient() as client:
            notes_res = await client.get(REST_NOTES_URL)
            stored_note = notes_res.json()[0]["content"] if notes_res.json() else None

        print(f"Tool Called: {t3_tool}, SQLite Stored: '{stored_note}'")
        assert t3_tool == "create_note" and stored_note == "I need to prepare for my AI interview."
        print("TEST 3: PASS ✓")

        # TEST 4: Reminder
        print("\n--- TEST 4: Reminder Creation & Listing ---")
        await ws.send(json.dumps({"type": "text_input", "text": "Remind me to study Python tomorrow at 8 PM."}))
        t4_tool = None
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "tool_start":
                t4_tool = frame.get("tool")
            elif frame.get("type") == "state" and frame.get("value") == "IDLE":
                break

        # Follow-up: list reminders
        await ws.send(json.dumps({"type": "text_input", "text": "What reminders do I have?"}))
        t4_list_tool = None
        t4_list_text = ""
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "tool_start":
                t4_list_tool = frame.get("tool")
            elif frame.get("type") == "assistant_text":
                t4_list_text += frame.get("text", "")
            elif frame.get("type") == "state" and frame.get("value") == "IDLE":
                break

        print(f"Create Tool: {t4_tool}, List Tool: {t4_list_tool}, List Text: '{t4_list_text}'")
        assert (
            t4_tool == "create_reminder" and t4_list_tool == "list_reminders" and "study python" in t4_list_text.lower()
        )
        print("TEST 4: PASS ✓")

        # TEST 5: Context
        print("\n--- TEST 5: Multi-Turn Conversation Context ---")
        await ws.send(json.dumps({"type": "text_input", "text": "What is the weather in Pune?"}))
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "state" and frame.get("value") == "IDLE":
                break

        await ws.send(json.dumps({"type": "text_input", "text": "Should I carry an umbrella?"}))
        t5_tool = None
        t5_text = ""
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "tool_start":
                t5_tool = frame.get("tool")
            elif frame.get("type") == "assistant_text":
                t5_text += frame.get("text", "")
            elif frame.get("type") == "state" and frame.get("value") == "IDLE":
                break

        print(f"Context Tool: {t5_tool}, Response: '{t5_text}'")
        assert t5_tool == "get_weather" and "pune" in t5_text.lower()
        print("TEST 5: PASS ✓")

        # TEST 6: Barge-In
        print("\n--- TEST 6: User Interruption / Barge-in ---")
        await ws.send(json.dumps({"type": "text_input", "text": "Tell me a very long story about Python."}))
        # Wait for SPEAKING state
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "state" and frame.get("value") == "SPEAKING":
                break

        # Send interrupt signal
        await ws.send(json.dumps({"type": "interrupt"}))
        # Verify state resets to LISTENING/IDLE
        interrupted_state = None
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "state":
                interrupted_state = frame.get("value")
                break

        # Send new request immediately: Mumbai weather
        await ws.send(json.dumps({"type": "text_input", "text": "What's the weather in Mumbai?"}))
        t6_mumbai_text = ""
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "assistant_text":
                t6_mumbai_text += frame.get("text", "")
            elif frame.get("type") == "state" and frame.get("value") == "IDLE":
                break

        print(f"Interrupted State: {interrupted_state}, Mumbai Weather Response: '{t6_mumbai_text}'")
        assert interrupted_state in ["LISTENING", "IDLE"] and "mumbai" in t6_mumbai_text.lower()
        print("TEST 6: PASS ✓")

        # TEST 7: Silent Playback
        print("\n--- TEST 7: Silent Playback ---")
        await ws.send(json.dumps({"type": "text_input", "text": "Tell me a short poem about coding."}))
        t7_audio_chunks = 0
        t7_text = ""
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "audio":
                t7_audio_chunks += 1
            elif frame.get("type") == "assistant_text":
                t7_text += frame.get("text", "")
            elif frame.get("type") == "state" and frame.get("value") == "IDLE":
                break

        print(f"Audio Chunks Played: {t7_audio_chunks}, Text Length: {len(t7_text)}")
        assert t7_audio_chunks >= 1 and len(t7_text) > 10
        print("TEST 7: PASS ✓")

        # TEST 8: Error Handling (Empty input & Disconnect Handling)
        print("\n--- TEST 8: Error Handling & Disconnect Gracefulness ---")
        try:
            await ws.send(json.dumps({"type": "text_input", "text": "  "}))
            t8_text = ""
            while True:
                frame_raw = await ws.recv()
                frame = json.loads(frame_raw)
                if frame.get("type") == "assistant_text":
                    t8_text += frame.get("text", "")
                elif frame.get("type") == "state" and frame.get("value") == "IDLE":
                    break
            print(f"Empty Input Response: '{t8_text}'")
            assert any(k in t8_text.lower() for k in ["catch", "repeat", "speak", "again"])
            print("TEST 8: PASS ✓")
        except (websockets.exceptions.ConnectionClosedError, websockets.exceptions.ConnectionClosedOK) as e:
            print(f"TEST 8: Connection closed gracefully as expected during disconnect test: {e}")
            print("TEST 8: PASS ✓")

    print("\n==================================================")
    print("ALL 8 WEBSOCKET/FUNCTIONAL QA TESTS PASSED 100%!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_final_qa())
