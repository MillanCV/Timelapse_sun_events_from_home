#!/usr/bin/env python3
"""Test script for the new camera router endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_camera_endpoints():
    """Test all camera endpoints."""
    print("Testing Camera Router Endpoints...")
    print("=" * 50)

    # Test camera status
    print("\n1. Testing GET /camera/status")
    try:
        response = requests.get(f"{BASE_URL}/camera/status")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

    # Test get all camera settings
    print("\n2. Testing GET /camera/settings")
    try:
        response = requests.get(f"{BASE_URL}/camera/settings")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")

    # Test individual settings GET endpoints
    settings = ["focal_length", "iso", "shutter_speed", "aperture", "mode"]
    for setting in settings:
        print(f"\n3. Testing GET /camera/settings/{setting}")
        try:
            response = requests.get(f"{BASE_URL}/camera/settings/{setting}")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

    # Test individual settings POST endpoints
    test_values = {
        "focal_length": 35.0,
        "iso": 200,
        "shutter_speed": 1.0 / 125.0,
        "aperture": 8.0,
        "mode": "rec",
    }

    for setting, value in test_values.items():
        print(f"\n4. Testing POST /camera/settings/{setting}")
        try:
            payload = {"value": value}
            response = requests.post(
                f"{BASE_URL}/camera/settings/{setting}", json=payload
            )
            print(f"Status: {response.status_code}")
            print(f"Payload: {payload}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")
        except Exception as e:
            print(f"Error: {e}")

    # Test camera shoot endpoint
    print("\n5. Testing POST /camera/shoot")
    try:
        payload = {
            "subject_distance": 1.0,
            "speed": 1.0 / 60.0,
            "iso_value": 100,
            "shots": 5,
            "interval": 2.0,
        }
        response = requests.post(f"{BASE_URL}/camera/shoot", json=payload)
        print(f"Status: {response.status_code}")
        print(f"Payload: {payload}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_camera_endpoints()
