import asyncio
import json
import websockets

WS_URL = "ws://localhost:8000/ws/voice"

TEST_LOCATIONS = [
    {"input": "What's the weather in Pune?", "expected_city": "Pune"},
    {"input": "What's the weather in Mumbai?", "expected_city": "Mumbai"},
    {"input": "What's the weather in Solapur?", "expected_city": "Solapur"},
    {"input": "What's the weather in Delhi?", "expected_city": "Delhi"},
    {"input": "What's the weather in London?", "expected_city": "London"},
]

async def run_weather_tests():
    print("==================================================")
    print("VERIFYING DYNAMIC WEATHER LOCATION ROUTING")
    print("==================================================")

    results = []

    async with websockets.connect(WS_URL) as ws:
        await ws.recv() # init
        await ws.recv() # state IDLE

        for tc in TEST_LOCATIONS:
            user_input = tc["input"]
            exp_city = tc["expected_city"]

            print(f"\nTesting Input: '{user_input}'")
            await ws.send(json.dumps({"type": "text_input", "text": user_input}))

            extracted_loc = None
            tool_res = None
            assistant_text = ""

            while True:
                frame = json.loads(await ws.recv())
                ftype = frame.get("type")
                if ftype == "tool_start":
                    extracted_loc = frame.get("params", {}).get("location")
                elif ftype == "tool_result":
                    tool_res = frame.get("result")
                elif ftype == "assistant_text":
                    assistant_text += frame.get("text", "")
                elif ftype == "state" and frame.get("value") == "IDLE":
                    break

            location_name = tool_res.get("location", "") if tool_res else ""
            lat = tool_res.get("latitude") if tool_res else None
            lon = tool_res.get("longitude") if tool_res else None
            temp = tool_res.get("temperature") if tool_res else None

            print(f"  - Extracted Location Param: '{extracted_loc}'")
            print(f"  - Geocoded City: '{location_name}' (lat={lat}, lon={lon})")
            print(f"  - Open-Meteo Temperature: {temp}")
            print(f"  - Assistant Spoken Text: '{assistant_text}'")

            passed = (extracted_loc == exp_city) and (exp_city.lower() in location_name.lower())
            print(f"  - Result: {'PASS ✓' if passed else 'FAIL ✗'}")
            assert passed, f"Failed location test for {exp_city}! Got extracted '{extracted_loc}' and geocoded '{location_name}'"

            results.append({
                "city": exp_city,
                "lat": lat,
                "lon": lon,
                "extracted": extracted_loc
            })

        # TEST 6: Context test ("How is the weather there?")
        print("\nTesting Context Input: 'How is the weather there?'")
        await ws.send(json.dumps({"type": "text_input", "text": "How is the weather there?"}))
        ctx_loc = None
        ctx_res = None
        while True:
            frame = json.loads(await ws.recv())
            if frame.get("type") == "tool_start":
                ctx_loc = frame.get("params", {}).get("location")
            elif frame.get("type") == "tool_result":
                ctx_res = frame.get("result")
            elif frame.get("type") == "state" and frame.get("value") == "IDLE":
                break

        print(f"  - Context Extracted Location: '{ctx_loc}'")
        print(f"  - Context Geocoded City: '{ctx_res.get('location') if ctx_res else ''}'")
        assert ctx_loc == "London", f"Expected 'London' from context, got '{ctx_loc}'"
        print("  - Context Result: PASS ✓")

    # Regression assertion: Pune != Mumbai != Solapur != Delhi != London
    print("\nRegression Check: Verify distinct geocoded coordinates across cities:")
    lats = [r["lat"] for r in results]
    lons = [r["lon"] for r in results]
    assert len(set(lats)) == len(lats), "Error: Geocoded latitudes must be distinct across cities!"
    assert len(set(lons)) == len(lons), "Error: Geocoded longitudes must be distinct across cities!"
    print("  - Pune != Mumbai != Solapur != Delhi != London: CONFIRMED DISTINCT ✓")

    print("\n==================================================")
    print("ALL 6 DYNAMIC WEATHER TESTS PASSED 100%!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(run_weather_tests())
