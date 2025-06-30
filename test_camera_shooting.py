#!/usr/bin/env python3
"""Test script for camera shooting endpoint."""

import asyncio
import json

from app.api.infrastructure.fastapi_app import create_app


async def test_camera_shooting():
    """Test the camera shooting functionality."""
    print("Testing camera shooting endpoint...")

    # Create the FastAPI app
    app = create_app()

    # Test data matching the bash script parameters
    test_request = {
        "subject_distance": 5.0,  # SD parameter
        "speed": 1.0,  # Speed parameter (shutter speed)
        "iso_value": 100,  # ISO value
        "shots": 10,  # Number of shots
        "interval": 2.0,  # Interval time between shots
    }

    print(f"Test request: {json.dumps(test_request, indent=2)}")

    # Test the endpoint
    from fastapi.testclient import TestClient

    client = TestClient(app)
    response = client.post("/camera/shoot", json=test_request)

    print(f"Response status: {response.status_code}")
    print(f"Response body: {json.dumps(response.json(), indent=2)}")

    return response.status_code == 200


if __name__ == "__main__":
    asyncio.run(test_camera_shooting())
