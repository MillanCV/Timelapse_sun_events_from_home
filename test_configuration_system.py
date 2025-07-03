#!/usr/bin/env python3
"""
Test script for the configuration management system.
"""

import os
import sys
import json
import tempfile
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from camera.infrastructure.configuration_service import get_configuration_service
from camera.infrastructure.container import get_camera_container


def test_configuration_loading():
    """Test basic configuration loading."""
    print("🧪 Testing configuration loading...")

    # Test with default configuration
    config_service = get_configuration_service()
    result = config_service.load_configuration()

    if result.is_success:
        config = result.value
        print("✅ Configuration loaded successfully")
        print(f"   Camera CHDKPTP location: {config.camera.chdkptp_location}")
        print(f"   Output directory: {config.camera.output_directory}")
        print(f"   JPEG quality: {config.image_processing.default_jpeg_quality}")
        print(f"   Environment: {config.environment.environment}")
        return True
    else:
        print(f"❌ Configuration loading failed: {result.error}")
        return False


def test_environment_variables():
    """Test environment variable override."""
    print("\n🧪 Testing environment variable override...")

    # Set test environment variables
    test_vars = {
        "CAMERA_DEFAULT_JPEG_QUALITY": "95",
        "IMAGE_TIMESTAMP_FONT_SCALE": "1.2",
        "ENVIRONMENT": "staging",
        "LOG_LEVEL": "DEBUG",
    }

    # Store original values
    original_vars = {}
    for key in test_vars:
        original_vars[key] = os.getenv(key)
        os.environ[key] = test_vars[key]

    try:
        # Reset configuration service to force reload
        from camera.infrastructure.configuration_service import (
            reset_configuration_service,
        )

        reset_configuration_service()

        config_service = get_configuration_service()
        result = config_service.load_configuration()

        if result.is_success:
            config = result.value
            print("✅ Environment variables applied successfully")
            print(
                f"   JPEG quality: {config.camera.default_jpeg_quality} (expected: 95)"
            )
            print(
                f"   Font scale: {config.image_processing.timestamp_font_scale} (expected: 1.2)"
            )
            print(
                f"   Environment: {config.environment.environment} (expected: staging)"
            )
            print(f"   Log level: {config.environment.log_level} (expected: DEBUG)")

            # Verify values
            success = (
                config.camera.default_jpeg_quality == 95
                and config.image_processing.timestamp_font_scale == 1.2
                and config.environment.environment == "staging"
                and config.environment.log_level == "DEBUG"
            )

            if success:
                print("✅ All environment variables correctly applied")
                return True
            else:
                print("❌ Some environment variables not applied correctly")
                return False
        else:
            print(f"❌ Configuration loading failed: {result.error}")
            return False

    finally:
        # Restore original environment variables
        for key, value in original_vars.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_configuration_file():
    """Test configuration file loading."""
    print("\n🧪 Testing configuration file loading...")

    # Create a temporary configuration file
    config_data = {
        "camera": {
            "chdkptp_location": "/test/chdkptp",
            "output_directory": "/test/images",
            "default_jpeg_quality": 85,
            "max_framerate": 6.0,
        },
        "image_processing": {
            "timestamp_font_scale": 0.8,
            "timestamp_color": [255, 0, 0],
        },
        "environment": {
            "environment": "testing",
            "debug": True,
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(config_data, f, indent=2)
        config_file_path = f.name

    try:
        # Reset configuration service
        from camera.infrastructure.configuration_service import (
            reset_configuration_service,
        )

        reset_configuration_service()

        # Load configuration from file
        config_service = get_configuration_service(config_file_path)
        result = config_service.load_configuration()

        if result.is_success:
            config = result.value
            print("✅ Configuration file loaded successfully")
            print(f"   CHDKPTP location: {config.camera.chdkptp_location}")
            print(f"   Output directory: {config.camera.output_directory}")
            print(f"   JPEG quality: {config.camera.default_jpeg_quality}")
            print(f"   Max framerate: {config.camera.max_framerate}")
            print(f"   Font scale: {config.image_processing.timestamp_font_scale}")
            print(f"   Environment: {config.environment.environment}")
            print(f"   Debug mode: {config.environment.debug}")

            # Verify values
            success = (
                config.camera.chdkptp_location == "/test/chdkptp"
                and config.camera.output_directory == "/test/images"
                and config.camera.default_jpeg_quality == 85
                and config.camera.max_framerate == 6.0
                and config.image_processing.timestamp_font_scale == 0.8
                and config.environment.environment == "testing"
                and config.environment.debug is True
            )

            if success:
                print("✅ All configuration file values correctly loaded")
                return True
            else:
                print("❌ Some configuration file values not loaded correctly")
                return False
        else:
            print(f"❌ Configuration file loading failed: {result.error}")
            return False

    finally:
        # Clean up temporary file
        os.unlink(config_file_path)


def test_configuration_validation():
    """Test configuration validation."""
    print("\n🧪 Testing configuration validation...")

    # Test invalid values
    test_cases = [
        ("Invalid JPEG quality", {"CAMERA_DEFAULT_JPEG_QUALITY": "150"}),
        ("Invalid framerate", {"CAMERA_MAX_FRAMERATE": "15.0"}),
        ("Invalid timeout", {"CAMERA_COMMAND_TIMEOUT": "1"}),
        ("Invalid font scale", {"IMAGE_TIMESTAMP_FONT_SCALE": "10.0"}),
        ("Invalid environment", {"ENVIRONMENT": "invalid"}),
    ]

    for test_name, test_vars in test_cases:
        print(f"   Testing: {test_name}")

        # Set test environment variables
        original_vars = {}
        for key, value in test_vars.items():
            original_vars[key] = os.getenv(key)
            os.environ[key] = value

        try:
            # Reset configuration service
            from camera.infrastructure.configuration_service import (
                reset_configuration_service,
            )

            reset_configuration_service()

            config_service = get_configuration_service()
            result = config_service.load_configuration()

            if result.is_success:
                print(f"   ❌ Validation should have failed for: {test_name}")
                return False
            else:
                print(f"   ✅ Validation correctly failed: {result.error}")

        finally:
            # Restore original environment variables
            for key, value in original_vars.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    print("✅ All validation tests passed")
    return True


def test_container_integration():
    """Test container integration with configuration."""
    print("\n🧪 Testing container integration...")

    try:
        # Reset container
        from camera.infrastructure.container import reset_camera_container

        reset_camera_container()

        # Get container with configuration
        container = get_camera_container()

        # Check if configuration is available
        camera_config = container.camera_config
        image_config = container.image_config
        env_config = container.environment_config

        if camera_config and image_config and env_config:
            print("✅ Container configuration integration successful")
            print(f"   Camera config available: {camera_config.chdkptp_location}")
            print(f"   Image config available: {image_config.default_jpeg_quality}")
            print(f"   Environment config available: {env_config.environment}")
            return True
        else:
            print("❌ Container configuration not available")
            return False

    except Exception as e:
        print(f"❌ Container integration test failed: {e}")
        return False


def main():
    """Run all configuration tests."""
    print("🚀 Starting Configuration Management System Tests")
    print("=" * 50)

    tests = [
        ("Basic Configuration Loading", test_configuration_loading),
        ("Environment Variable Override", test_environment_variables),
        ("Configuration File Loading", test_configuration_file),
        ("Configuration Validation", test_configuration_validation),
        ("Container Integration", test_container_integration),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Configuration system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the configuration system.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
