#!/usr/bin/env python3
"""Test file to verify error handling fixes are working correctly."""

import sys
import os
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.camera.domain.entities import (
    ErrorResponse,
    ErrorType,
    CameraControlError,
)
from app.camera.infrastructure.error_handling_service import (
    ErrorHandlingService,
    get_error_handling_service,
)


def test_error_response_to_dict():
    """Test that ErrorResponse.to_dict() method works correctly."""
    print("🧪 Testing ErrorResponse.to_dict() method...")

    # Create an error response
    error_response = ErrorResponse(
        success=False,
        error_type="validation_error",
        message="Test error message",
        code="TEST_ERROR",
        details={"test": "data"},
        request_id="test-request-id",
        status_code=400,
    )

    # Convert to dictionary
    result = error_response.to_dict()

    # Verify the structure
    expected_keys = {
        "success",
        "error_type",
        "message",
        "code",
        "details",
        "timestamp",
        "request_id",
        "status_code",
    }

    assert set(result.keys()) == expected_keys, (
        f"Expected keys {expected_keys}, got {set(result.keys())}"
    )
    assert result["success"] == False
    assert result["error_type"] == "validation_error"
    assert result["message"] == "Test error message"
    assert result["code"] == "TEST_ERROR"
    assert result["details"] == {"test": "data"}
    assert result["request_id"] == "test-request-id"
    assert result["status_code"] == 400
    assert result["timestamp"] is not None

    print("✅ ErrorResponse.to_dict() test passed!")


def test_error_handling_service_initialization():
    """Test that ErrorHandlingService can be initialized without schema errors."""
    print("🧪 Testing ErrorHandlingService initialization...")

    try:
        # Create error handling service
        error_service = ErrorHandlingService()

        # Verify it has the expected attributes
        assert hasattr(error_service, "_error_handlers")
        assert hasattr(error_service, "logger")

        # Verify error handlers are set up
        assert len(error_service._error_handlers) > 0

        print("✅ ErrorHandlingService initialization test passed!")
        return error_service

    except Exception as e:
        print(f"❌ ErrorHandlingService initialization failed: {e}")
        raise


def test_error_handling_service_methods():
    """Test that ErrorHandlingService methods work correctly."""
    print("🧪 Testing ErrorHandlingService methods...")

    error_service = ErrorHandlingService()

    # Test handle_error method
    try:
        test_error = ValueError("Test validation error")
        error_response = error_service.handle_error(
            test_error, context={"test": "context"}, request_id="test-request-id"
        )

        assert isinstance(error_response, ErrorResponse)
        assert error_response.success == False
        assert error_response.error_type == "validation_error"
        assert "Test validation error" in error_response.message
        assert error_response.request_id == "test-request-id"

        print("✅ ErrorHandlingService.handle_error() test passed!")

    except Exception as e:
        print(f"❌ ErrorHandlingService.handle_error() test failed: {e}")
        raise

    # Test handle_exception method
    try:
        test_exception = RuntimeError("Test runtime error")
        error_response = error_service.handle_exception(
            test_exception,
            request_id="test-exception-id",
            context={"test": "exception"},
        )

        assert isinstance(error_response, ErrorResponse)
        assert error_response.success == False
        assert error_response.request_id == "test-exception-id"

        print("✅ ErrorHandlingService.handle_exception() test passed!")

    except Exception as e:
        print(f"❌ ErrorHandlingService.handle_exception() test failed: {e}")
        raise


def test_global_error_handling_service():
    """Test the global error handling service singleton."""
    print("🧪 Testing global error handling service...")

    try:
        # Get the global service
        error_service = get_error_handling_service()

        # Verify it's the same instance
        error_service2 = get_error_handling_service()
        assert error_service is error_service2

        # Test that it works
        test_error = FileNotFoundError("Test file not found")
        error_response = error_service.handle_error(
            test_error, context={"operation": "test"}, request_id="global-test-id"
        )

        assert isinstance(error_response, ErrorResponse)
        assert error_response.error_type == "file_error"

        print("✅ Global error handling service test passed!")

    except Exception as e:
        print(f"❌ Global error handling service test failed: {e}")
        raise


def test_custom_exceptions():
    """Test custom exception handling."""
    print("🧪 Testing custom exception handling...")

    error_service = ErrorHandlingService()

    try:
        # Test CameraControlError
        camera_error = CameraControlError(
            message="Test camera error",
            error_type=ErrorType.CAMERA_ERROR,
            code="TEST_CAMERA_ERROR",
            details={"camera_id": "test-camera"},
        )

        error_response = error_service.handle_error(
            camera_error,
            context={"operation": "camera_test"},
            request_id="custom-exception-id",
        )

        assert isinstance(error_response, ErrorResponse)
        assert error_response.error_type == "camera_error"
        assert error_response.code == "TEST_CAMERA_ERROR"
        assert error_response.details == {"camera_id": "test-camera"}

        print("✅ Custom exception handling test passed!")

    except Exception as e:
        print(f"❌ Custom exception handling test failed: {e}")
        raise


def test_json_serialization():
    """Test that error responses can be serialized to JSON."""
    print("🧪 Testing JSON serialization...")

    error_service = ErrorHandlingService()

    try:
        # Create an error response
        test_error = ValueError("JSON serialization test")
        error_response = error_service.handle_error(
            test_error, context={"test": "json"}, request_id="json-test-id"
        )

        # Convert to dictionary
        error_dict = error_response.to_dict()

        # Serialize to JSON
        json_string = json.dumps(error_dict)

        # Deserialize back
        deserialized = json.loads(json_string)

        # Verify the data is preserved
        assert deserialized["success"] == error_dict["success"]
        assert deserialized["error_type"] == error_dict["error_type"]
        assert deserialized["message"] == error_dict["message"]
        assert deserialized["request_id"] == error_dict["request_id"]

        print("✅ JSON serialization test passed!")

    except Exception as e:
        print(f"❌ JSON serialization test failed: {e}")
        raise


def test_error_type_enum():
    """Test that ErrorType enum works correctly."""
    print("🧪 Testing ErrorType enum...")

    try:
        # Test enum values
        assert ErrorType.VALIDATION_ERROR.value == "validation_error"
        assert ErrorType.CAMERA_ERROR.value == "camera_error"
        assert ErrorType.FILE_ERROR.value == "file_error"
        assert ErrorType.UNKNOWN_ERROR.value == "unknown_error"

        # Test enum comparison
        assert ErrorType.VALIDATION_ERROR == ErrorType.VALIDATION_ERROR
        assert ErrorType.VALIDATION_ERROR != ErrorType.CAMERA_ERROR

        print("✅ ErrorType enum test passed!")

    except Exception as e:
        print(f"❌ ErrorType enum test failed: {e}")
        raise


def run_all_tests():
    """Run all tests and report results."""
    print("🚀 Starting error handling fixes tests...\n")

    tests = [
        test_error_type_enum,
        test_error_response_to_dict,
        test_error_handling_service_initialization,
        test_error_handling_service_methods,
        test_global_error_handling_service,
        test_custom_exceptions,
        test_json_serialization,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            failed += 1
        print()

    print("📊 Test Results:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Total: {passed + failed}")

    if failed == 0:
        print("\n🎉 All tests passed! The error handling fixes are working correctly.")
        return True
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
