import asyncio
import json

import httpx
import websockets

WS_URL = "ws://localhost:8000/ws/voice"
REST_URL = "http://localhost:8000/api/notes"

TEST_CASES = [
    {
        "input": "Create a note saying I need to prepare for my AI interview.",
        "expected": "I need to prepare for my AI interview.",
    },
    {"input": "Make a note that I need to call Rahul tomorrow.", "expected": "I need to call Rahul tomorrow."},
    {"input": "Note this: Submit the assignment by Monday.", "expected": "Submit the assignment by Monday."},
    {"input": "Remember this, I need to revise Python.", "expected": "I need to revise Python."},
    {"input": "Create a note saying buy milk and eggs.", "expected": "buy milk and eggs."},
]


async def run_note_tests():
    print("==================================================")
    print("VERIFYING NOTE CONTENT EXTRACTION & SQLITE DB")
    print("==================================================")

    async with websockets.connect(WS_URL) as ws:
        await ws.recv()  # init
        await ws.recv()  # state IDLE

        for idx, tc in enumerate(TEST_CASES, start=1):
            user_input = tc["input"]
            expected_content = tc["expected"]

            print(f"\n--- TEST {idx} ---")
            print(f"Input Speech/Text: '{user_input}'")

            await ws.send(json.dumps({"type": "text_input", "text": user_input}))

            assistant_text = ""
            tool_start_params = None

            while True:
                frame_raw = await ws.recv()
                frame = json.loads(frame_raw)
                ftype = frame.get("type")

                if ftype == "tool_start":
                    tool_start_params = frame.get("params")
                elif ftype == "assistant_text":
                    assistant_text += frame.get("text", "")
                elif ftype == "state" and frame.get("value") == "IDLE":
                    break

            # Fetch actual stored SQLite value via REST API
            async with httpx.AsyncClient() as client:
                res = await client.get(REST_URL)
                notes = res.json()
                latest_note = notes[0]["content"] if notes else None

            print(f"Extracted Tool Params: {tool_start_params}")
            print(f"Assistant Response: '{assistant_text}'")
            print(f"Actual SQLite Stored Note: '{latest_note}'")
            print(f"Expected Note Content: '{expected_content}'")

            passed = latest_note == expected_content
            print(f"Result: {'PASS ✓' if passed else 'FAIL ✗'}")
            assert passed, f"Test {idx} failed! Expected '{expected_content}', got '{latest_note}'"

    print("\n==================================================")
    print("ALL 5 NOTE EXTRACTION TESTS PASSED 100%!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(run_note_tests())
