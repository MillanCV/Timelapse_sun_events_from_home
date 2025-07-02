#!/usr/bin/env python3
"""Test script for the get last picture endpoint."""

import asyncio
import aiohttp
import os


async def test_get_last_picture():
    """Test the get last picture endpoint."""
    base_url = "http://localhost:8000"

    async with aiohttp.ClientSession() as session:
        # Test getting the last picture
        print("Testing GET /camera/last-picture...")

        try:
            async with session.get(f"{base_url}/camera/last-picture") as response:
                if response.status == 200:
                    print("✅ Success! Image file returned.")

                    # Get content type and content length
                    content_type = response.headers.get("content-type", "unknown")
                    content_length = response.headers.get("content-length", "unknown")
                    filename = response.headers.get("content-disposition", "unknown")

                    print(f"📸 Content-Type: {content_type}")
                    print(f"📏 Content-Length: {content_length} bytes")
                    print(f"📁 Filename: {filename}")

                    # Save the image to a local file for testing
                    image_data = await response.read()
                    test_filename = "last_picture_test.jpg"

                    with open(test_filename, "wb") as f:
                        f.write(image_data)

                    print(f"💾 Image saved as: {test_filename}")
                    print(f"📊 File size: {len(image_data)} bytes")

                    # Clean up test file
                    os.remove(test_filename)
                    print(f"🧹 Test file cleaned up: {test_filename}")

                elif response.status == 404:
                    print("ℹ️  No pictures found (404)")
                    error_text = await response.text()
                    print(f"Response: {error_text}")
                else:
                    print(f"❌ Request failed with status {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")

        except Exception as e:
            print(f"❌ Exception occurred: {e}")


if __name__ == "__main__":
    asyncio.run(test_get_last_picture())
