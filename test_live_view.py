#!/usr/bin/env python3
"""Test script for live view functionality."""

import asyncio
import aiohttp
import os
import time


async def test_live_view_snapshot():
    """Test the live view snapshot endpoint."""
    base_url = "http://localhost:8000"

    async with aiohttp.ClientSession() as session:
        print("Testing GET /camera/live-view/snapshot...")

        try:
            # Test snapshot with overlay
            async with session.get(
                f"{base_url}/camera/live-view/snapshot?include_overlay=true"
            ) as response:
                if response.status == 200:
                    print("✅ Live view snapshot with overlay successful!")

                    # Get image data
                    image_data = await response.read()
                    print(f"📸 Image size: {len(image_data)} bytes")

                    # Save test image
                    with open("live_view_snapshot.jpg", "wb") as f:
                        f.write(image_data)
                    print("💾 Saved as: live_view_snapshot.jpg")

                else:
                    print(f"❌ Snapshot failed with status {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")

        except Exception as e:
            print(f"❌ Exception occurred: {e}")


async def test_live_view_stream():
    """Test the live view stream endpoint."""
    base_url = "http://localhost:8000"

    async with aiohttp.ClientSession() as session:
        print("Testing GET /camera/live-view/stream...")

        try:
            # Test stream with 2 FPS for 5 seconds
            start_time = time.time()
            frame_count = 0

            async with session.get(
                f"{base_url}/camera/live-view/stream?fps=2&include_overlay=true"
            ) as response:
                if response.status == 200:
                    print("✅ Live view stream started!")

                    # Read stream for 5 seconds
                    async for line in response.content:
                        if b"--frame" in line:
                            frame_count += 1
                            print(f"📸 Frame {frame_count} received")

                        # Stop after 5 seconds
                        if time.time() - start_time > 5:
                            break

                    print(f"📊 Received {frame_count} frames in 5 seconds")

                    # Stop the stream
                    async with session.post(
                        f"{base_url}/camera/live-view/stop"
                    ) as stop_response:
                        if stop_response.status == 200:
                            print("✅ Stream stopped successfully")
                        else:
                            print(f"❌ Failed to stop stream: {stop_response.status}")

                else:
                    print(f"❌ Stream failed with status {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")

        except Exception as e:
            print(f"❌ Exception occurred: {e}")


async def test_live_view_without_overlay():
    """Test live view without overlay."""
    base_url = "http://localhost:8000"

    async with aiohttp.ClientSession() as session:
        print("Testing live view snapshot without overlay...")

        try:
            async with session.get(
                f"{base_url}/camera/live-view/snapshot?include_overlay=false"
            ) as response:
                if response.status == 200:
                    print("✅ Live view snapshot without overlay successful!")

                    image_data = await response.read()
                    print(f"📸 Image size: {len(image_data)} bytes")

                    # Save test image
                    with open("live_view_no_overlay.jpg", "wb") as f:
                        f.write(image_data)
                    print("💾 Saved as: live_view_no_overlay.jpg")

                else:
                    print(f"❌ Snapshot failed with status {response.status}")

        except Exception as e:
            print(f"❌ Exception occurred: {e}")


async def main():
    """Run all live view tests."""
    print("🚀 Starting live view tests...\n")

    # Test snapshot
    await test_live_view_snapshot()
    print()

    # Test snapshot without overlay
    await test_live_view_without_overlay()
    print()

    # Test stream
    await test_live_view_stream()
    print()

    # Cleanup
    for filename in ["live_view_snapshot.jpg", "live_view_no_overlay.jpg"]:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"🧹 Cleaned up: {filename}")

    print("\n✅ Live view tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
