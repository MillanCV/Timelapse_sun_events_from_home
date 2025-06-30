#!/usr/bin/env python3
"""Simple test script for the camera shoot endpoint."""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_camera_shoot():
    """Test the camera shoot endpoint."""
    print("Testing Camera Shoot Endpoint...")
    print("=" * 40)

    # Test the simple test-shoot endpoint
    print("\n1. Testing POST /camera/test-shoot")
    try:
        response = requests.post(f"{BASE_URL}/camera/test-shoot")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

    # Test the full shoot endpoint with parameters
    print("\n2. Testing POST /camera/shoot")
    try:
        payload = {
            "subject_distance": 1.0,
            "speed": 1.0 / 60.0,
            "iso_value": 100,
            "shots": 2,
            "interval": 2.0,
        }
        response = requests.post(f"{BASE_URL}/camera/shoot", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Payload: {payload}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

    # Test camera status
    print("\n3. Testing GET /camera/status")
    try:
        response = requests.get(f"{BASE_URL}/camera/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_camera_shoot()
