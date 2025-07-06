#!/usr/bin/env python3
"""Test file to verify FastAPI schema generation works without CallableSchema errors."""

import sys
import os
import json

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

from app.api.infrastructure.fastapi_app import create_app


def test_fastapi_app_creation():
    """Test that FastAPI app can be created without errors."""
    print("🧪 Testing FastAPI app creation...")

    try:
        # Create the FastAPI app
        app = create_app()

        # Verify it's a FastAPI app
        assert hasattr(app, "openapi")
        assert hasattr(app, "routes")

        print("✅ FastAPI app creation test passed!")
        return app

    except Exception as e:
        print(f"❌ FastAPI app creation failed: {e}")
        raise


def test_openapi_schema_generation():
    """Test that OpenAPI schema can be generated without CallableSchema errors."""
    print("🧪 Testing OpenAPI schema generation...")

    try:
        # Create the FastAPI app
        app = create_app()

        # Generate OpenAPI schema
        openapi_schema = app.openapi()

        # Verify the schema has the expected structure
        assert "openapi" in openapi_schema
        assert "info" in openapi_schema
        assert "paths" in openapi_schema

        # Verify it's a valid JSON
        schema_json = json.dumps(openapi_schema)
        assert len(schema_json) > 0

        print("✅ OpenAPI schema generation test passed!")
        print(f"📄 Schema size: {len(schema_json)} characters")

        return openapi_schema

    except Exception as e:
        print(f"❌ OpenAPI schema generation failed: {e}")
        print(f"Error type: {type(e).__name__}")
        raise


def test_schema_paths():
    """Test that the OpenAPI schema contains expected paths."""
    print("🧪 Testing OpenAPI schema paths...")

    try:
        # Get the OpenAPI schema
        openapi_schema = test_openapi_schema_generation()

        # Check for expected paths
        paths = openapi_schema.get("paths", {})

        # Should have at least some paths
        assert len(paths) > 0, "No paths found in OpenAPI schema"

        # Check for specific expected paths
        expected_paths = [
            "/",
            "/health",
            "/current",
            "/upcoming",
            "/timelapse",
            "/camera/shoot",
            "/camera/live-view/snapshot",
            "/camera/live-view/stream",
        ]

        found_paths = []
        for path in expected_paths:
            if path in paths:
                found_paths.append(path)
                print(f"  ✅ Found path: {path}")
            else:
                print(f"  ⚠️  Missing path: {path}")

        print(
            f"📊 Found {len(found_paths)} out of {len(expected_paths)} expected paths"
        )

        # At least some paths should be present
        assert len(found_paths) > 0, "No expected paths found in schema"

        print("✅ OpenAPI schema paths test passed!")

    except Exception as e:
        print(f"❌ OpenAPI schema paths test failed: {e}")
        raise


def test_schema_components():
    """Test that the OpenAPI schema has valid components."""
    print("🧪 Testing OpenAPI schema components...")

    try:
        # Get the OpenAPI schema
        openapi_schema = test_openapi_schema_generation()

        # Check for components (schemas, etc.)
        components = openapi_schema.get("components", {})

        # Should have schemas
        schemas = components.get("schemas", {})
        assert len(schemas) > 0, "No schemas found in OpenAPI components"

        # Check for specific expected schemas
        expected_schemas = [
            "TimelapseRequestModel",
            "TimelapseResponseModel",
            "ShootCameraResponseModel",
        ]

        found_schemas = []
        for schema_name in expected_schemas:
            if schema_name in schemas:
                found_schemas.append(schema_name)
                print(f"  ✅ Found schema: {schema_name}")
            else:
                print(f"  ⚠️  Missing schema: {schema_name}")

        print(
            f"📊 Found {len(found_schemas)} out of {len(expected_schemas)} expected schemas"
        )

        print("✅ OpenAPI schema components test passed!")

    except Exception as e:
        print(f"❌ OpenAPI schema components test failed: {e}")
        raise


def run_all_tests():
    """Run all FastAPI schema tests and report results."""
    print("🚀 Starting FastAPI schema generation tests...\n")

    tests = [
        test_fastapi_app_creation,
        test_openapi_schema_generation,
        test_schema_paths,
        test_schema_components,
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
        print(
            "\n🎉 All FastAPI schema tests passed! The CallableSchema issue is resolved."
        )
        return True
    else:
        print(
            f"\n⚠️  {failed} test(s) failed. The CallableSchema issue may still exist."
        )
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
