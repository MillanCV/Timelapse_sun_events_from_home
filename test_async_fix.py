#!/usr/bin/env python3
"""Simple test to verify async/await fixes are working."""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from camera.application.use_cases import (
    ShootCameraRequest,
    ShootCameraUseCase,
)
from camera.infrastructure.chdkptp_camera_service import (
    CHDKPTPCameraService,
    CHDKPTPScriptGenerator,
)


async def test_async_camera_use_case():
    """Test that the camera use case can be called asynchronously."""
    try:
        # Create the camera service and script generator
        script_generator = CHDKPTPScriptGenerator()
        camera_service = CHDKPTPCameraService(script_generator)

        # Create the use case
        use_case = ShootCameraUseCase(camera_service)

        # Create a test request
        request = ShootCameraRequest(
            subject_distance=1.0,
            speed=1.0 / 60.0,
            iso_value=100,
            shots=1,
            interval=1.0,
        )

        # This should not raise a RuntimeWarning about coroutine not being awaited
        print("Testing async camera use case...")
        response = await use_case.execute(request)

        print(f"✅ Async test passed! Response: {response.success}")
        return True

    except Exception as e:
        print(f"❌ Async test failed: {e}")
        return False


async def test_camera_status():
    """Test that camera status can be retrieved asynchronously."""
    try:
        # Create the camera service and script generator
        script_generator = CHDKPTPScriptGenerator()
        camera_service = CHDKPTPCameraService(script_generator)

        # This should not raise a RuntimeWarning about coroutine not being awaited
        print("Testing async camera status...")
        status = await camera_service.get_camera_status()

        print(f"✅ Camera status test passed! Connected: {status.is_connected}")
        return True

    except Exception as e:
        print(f"❌ Camera status test failed: {e}")
        return False


async def main():
    """Run all async tests."""
    print("🧪 Testing async/await fixes...")

    # Test 1: Camera use case
    test1_passed = await test_async_camera_use_case()

    # Test 2: Camera status
    test2_passed = await test_camera_status()

    if test1_passed and test2_passed:
        print(
            "🎉 All async tests passed! The RuntimeWarning issues should be resolved."
        )
    else:
        print("💥 Some async tests failed.")

    return test1_passed and test2_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
