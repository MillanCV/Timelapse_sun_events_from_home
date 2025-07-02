#!/usr/bin/env python3
"""Test script for the list images endpoint."""

import asyncio
import aiohttp
import json


async def test_list_images():
    """Test the list images endpoint."""
    base_url = "http://localhost:8000"

    async with aiohttp.ClientSession() as session:
        # Test listing all images
        print("Testing GET /camera/images...")

        try:
            async with session.get(f"{base_url}/camera/images") as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ Success!")
                    print(f"Response: {json.dumps(data, indent=2)}")

                    if data.get("success"):
                        print(f"📸 Found {data['total_count']} images")

                        # Show details for each image
                        for i, image in enumerate(data.get("images", []), 1):
                            print(f"\n{i}. {image['filename']}")
                            print(f"   📏 Size: {image['size_bytes']} bytes")
                            print(f"   📅 Modified: {image['modified_time']}")
                            print(f"   🔗 URL: {image['image_url']}")

                            # Test if the image URL works
                            img_url = f"{base_url}{image['image_url']}"
                            async with session.head(img_url) as img_response:
                                if img_response.status == 200:
                                    print("   ✅ Image accessible")
                                else:
                                    print(
                                        f"   ❌ Image not accessible: {img_response.status}"
                                    )
                    else:
                        print(f"ℹ️  {data.get('message', 'Unknown error')}")
                else:
                    print(f"❌ Request failed with status {response.status}")
                    error_text = await response.text()
                    print(f"Error: {error_text}")

        except Exception as e:
            print(f"❌ Exception occurred: {e}")


if __name__ == "__main__":
    asyncio.run(test_list_images())
