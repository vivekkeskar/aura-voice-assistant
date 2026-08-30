import asyncio
import json

import websockets

WS_URL = "ws://localhost:8000/ws/voice"


async def test_command(ws, user_input: str, expected_tool: str = None) -> dict:
    await ws.send(json.dumps({"type": "text_input", "text": user_input}))

    received_tool_call = None
    tool_result = None
    assistant_text = ""

    while True:
        frame_raw = await ws.recv()
        frame = json.loads(frame_raw)
        ftype = frame.get("type")

        if ftype == "tool_start":
            received_tool_call = frame.get("tool")
        elif ftype == "tool_result":
            tool_result = frame.get("result")
        elif ftype == "assistant_text":
            assistant_text += frame.get("text", "")
        elif ftype == "state" and frame.get("value") == "IDLE":
            break

    is_generic_intro = "I am AURA, your voice assistant. I can help you check real-time weather" in assistant_text
    passed = not is_generic_intro and (expected_tool is None or received_tool_call == expected_tool)

    return {
        "user_input": user_input,
        "tool_called": received_tool_call,
        "tool_result": tool_result,
        "assistant_text": assistant_text,
        "is_generic_intro": is_generic_intro,
        "passed": passed,
    }


async def run_all_tests():
    print("==================================================")
    print("RUNNING 7 COMMAND VERIFICATION SUITE")
    print("==================================================")

    async with websockets.connect(WS_URL) as ws:
        await ws.recv()  # init
        await ws.recv()  # state IDLE

        # TEST 1: Weather query
        res1 = await test_command(ws, "What's the weather in Pune?", expected_tool="get_weather")
        print(f"\nTEST 1: {res1['user_input']}")
        print(f"  Tool Called: {res1['tool_called']}")
        print(f"  Assistant Text: {res1['assistant_text']}")
        print(f"  Status: {'PASS' if res1['passed'] else 'FAIL'}")

        # TEST 8 (Multi-turn Context): Follow-up question
        res8 = await test_command(ws, "Should I carry an umbrella?", expected_tool="get_weather")
        print(f"\nTEST 8 (Context): {res8['user_input']}")
        print(f"  Tool Called: {res8['tool_called']}")
        print(f"  Assistant Text: {res8['assistant_text']}")
        print(f"  Status: {'PASS' if res8['passed'] else 'FAIL'}")

        # TEST 2: Create note
        res2 = await test_command(ws, "Create a note saying prepare for my AI interview.", expected_tool="create_note")
        print(f"\nTEST 2: {res2['user_input']}")
        print(f"  Tool Called: {res2['tool_called']}")
        print(f"  Assistant Text: {res2['assistant_text']}")
        print(f"  Status: {'PASS' if res2['passed'] else 'FAIL'}")

        # TEST 3: Show notes
        res3 = await test_command(ws, "Show my notes.", expected_tool="list_notes")
        print(f"\nTEST 3: {res3['user_input']}")
        print(f"  Tool Called: {res3['tool_called']}")
        print(f"  Assistant Text: {res3['assistant_text']}")
        print(f"  Status: {'PASS' if res3['passed'] else 'FAIL'}")

        # TEST 4: Create reminder
        res4 = await test_command(ws, "Remind me to study tomorrow at 8 PM.", expected_tool="create_reminder")
        print(f"\nTEST 4: {res4['user_input']}")
        print(f"  Tool Called: {res4['tool_called']}")
        print(f"  Assistant Text: {res4['assistant_text']}")
        print(f"  Status: {'PASS' if res4['passed'] else 'FAIL'}")

        # TEST 5: Show reminders
        res5 = await test_command(ws, "What reminders do I have?", expected_tool="list_reminders")
        print(f"\nTEST 5: {res5['user_input']}")
        print(f"  Tool Called: {res5['tool_called']}")
        print(f"  Assistant Text: {res5['assistant_text']}")
        print(f"  Status: {'PASS' if res5['passed'] else 'FAIL'}")

        # TEST 6: Greeting
        res6 = await test_command(ws, "Hey AURA, good morning.", expected_tool=None)
        print(f"\nTEST 6: {res6['user_input']}")
        print(f"  Tool Called: {res6['tool_called']}")
        print(f"  Assistant Text: {res6['assistant_text']}")
        print(f"  Status: {'PASS' if res6['passed'] else 'FAIL'}")

        # TEST 7: Identity / Introduction
        res7 = await test_command(ws, "Who are you?", expected_tool=None)
        print(f"\nTEST 7: {res7['user_input']}")
        print(f"  Tool Called: {res7['tool_called']}")
        print(f"  Assistant Text: {res7['assistant_text']}")
        print(f"  Status: {'PASS' if res7['passed'] else 'FAIL'}")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
