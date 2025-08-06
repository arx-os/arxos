#!/usr/bin/env python3
"""
Simple test script for SVGX Engine application
"""

import asyncio
import aiohttp
import time
import subprocess
import sys
import os


async def test_app():
    """Test the SVGX Engine application"""

    # Start the application
    print("Starting SVGX Engine application...")
    process = subprocess.Popen(
        ["python", "app.py"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )

    # Wait for application to start
    print("Waiting for application to start...")
    await asyncio.sleep(5)

    try:
        # Test health endpoint
        print("Testing health endpoint...")
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:8000/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Health check passed: {data}")
                else:
                    print(f"❌ Health check failed: {response.status}")
                    return False

        # Test parse endpoint
        print("Testing parse endpoint...")
        parse_payload = {
            "content": """
            <svgx>
                <circle cx="50" cy="50" r="25" fill="red"/>
                <rect x="100" y="100" width="50" height="50" fill="blue"/>
            </svgx>
            """
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/parse", json=parse_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(
                        f"✅ Parse test passed: {len(data.get('elements', []))} elements parsed"
                    )
                else:
                    print(f"❌ Parse test failed: {response.status}")
                    return False

        # Test evaluate endpoint
        print("Testing evaluate endpoint...")
        evaluate_payload = {
            "content": """
            <svgx>
                <circle cx="50" cy="50" r="25" fill="red" behavior="clickable"/>
            </svgx>
            """
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/evaluate", json=evaluate_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Evaluate test passed: {data}")
                else:
                    print(f"❌ Evaluate test failed: {response.status}")
                    return False

        # Test simulate endpoint
        print("Testing simulate endpoint...")
        simulate_payload = {
            "content": """
            <svgx>
                <circle cx="50" cy="50" r="25" fill="red" physics="gravity"/>
            </svgx>
            """
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/simulate", json=simulate_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Simulate test passed: {data}")
                else:
                    print(f"❌ Simulate test failed: {response.status}")
                    return False

        print("🎉 All tests passed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        # Stop the application
        print("Stopping application...")
        process.terminate()
        process.wait()
        print("Application stopped")


if __name__ == "__main__":
    success = asyncio.run(test_app())
    sys.exit(0 if success else 1)
