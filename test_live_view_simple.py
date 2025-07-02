#!/usr/bin/env python3
"""Simple test script for live view functionality."""

import asyncio
import aiohttp
import os


async def test_live_view_snapshot_simple():
    """Test the live view snapshot endpoint."""
    base_url = "http://localhost:8000"

    async with aiohttp.ClientSession() as session:
        print("Testing GET /camera/live-view/snapshot...")

        try:
            # Test snapshot (no parameters needed)
            async with session.get(f"{base_url}/camera/live-view/snapshot") as response:
                if response.status == 200:
                    print("✅ Live view snapshot successful!")

                    # Get image data
                    image_data = await response.read()
                    print(f"📸 Image size: {len(image_data)} bytes")

                    # Save test image
                    with open("live_view_test.jpg", "wb") as f:
                        f.write(image_data)
                    print("💾 Saved as: live_view_test.jpg")

                else:
                    print(f"❌ Snapshot failed with status {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")

        except Exception as e:
            print(f"❌ Exception occurred: {e}")


async def test_live_view_stream_simple():
    """Test the live view stream endpoint."""
    base_url = "http://localhost:8000"

    async with aiohttp.ClientSession() as session:
        print("Testing GET /camera/live-view/stream...")

        try:
            # Test stream (no parameters needed)
            async with session.get(f"{base_url}/camera/live-view/stream") as response:
                if response.status == 200:
                    print("✅ Live view stream started!")

                    # Read a few frames
                    frame_count = 0
                    async for line in response.content:
                        if b"--frame" in line:
                            frame_count += 1
                            print(f"📸 Frame {frame_count} received")

                        # Stop after 3 frames
                        if frame_count >= 3:
                            break

                    print(f"📊 Received {frame_count} frames")

                else:
                    print(f"❌ Stream failed with status {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")

        except Exception as e:
            print(f"❌ Exception occurred: {e}")


async def main():
    """Run the simple live view tests."""
    print("🚀 Starting simple live view tests...\n")

    # Test snapshot
    await test_live_view_snapshot_simple()
    print()

    # Test stream
    await test_live_view_stream_simple()
    print()

    # Cleanup
    if os.path.exists("live_view_test.jpg"):
        os.remove("live_view_test.jpg")
        print("🧹 Cleaned up: live_view_test.jpg")

    print("\n✅ Simple live view tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
