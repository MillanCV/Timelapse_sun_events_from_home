#!/usr/bin/env python3
"""Test script to check CHDKPTP commands."""

import subprocess
import os


def test_chdkptp_help():
    """Test CHDKPTP help to see available commands."""
    chdkptp_script = "/home/arrumada/Dev/CanonCameraControl/ChdkPTP/chdkptp.sh"

    if not os.path.exists(chdkptp_script):
        print(f"❌ CHDKPTP script not found: {chdkptp_script}")
        return

    print("🔍 Testing CHDKPTP help...")

    try:
        # Test basic help
        result = subprocess.run(
            ["sudo", chdkptp_script, "-h"],
            cwd="/home/arrumada/Dev/CanonCameraControl/ChdkPTP",
            capture_output=True,
            text=True,
            check=True,
        )
        print("✅ Help command successful")
        print(f"Output: {result.stdout}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Help command failed: {e}")
        print(f"Error: {e.stderr}")


def test_connect_only():
    """Test just connecting to the camera."""
    chdkptp_script = "/home/arrumada/Dev/CanonCameraControl/ChdkPTP/chdkptp.sh"

    print("🔍 Testing camera connection...")

    try:
        # Test just connecting
        result = subprocess.run(
            ["sudo", chdkptp_script, "-c"],
            cwd="/home/arrumada/Dev/CanonCameraControl/ChdkPTP",
            capture_output=True,
            text=True,
            check=True,
        )
        print("✅ Connect command successful")
        print(f"Output: {result.stdout}")

    except subprocess.CalledProcessError as e:
        print(f"❌ Connect command failed: {e}")
        print(f"Error: {e.stderr}")


def test_live_view_commands():
    """Test different live view command variations."""
    chdkptp_script = "/home/arrumada/Dev/CanonCameraControl/ChdkPTP/chdkptp.sh"

    commands_to_test = [
        ["-c", "-e", "lvdumpimg"],
        ["-c", "-e", "lv"],
        ["-c", "-e", "liveview"],
        ["-c", "-e", "dumpimg"],
        ["-c", "-e", "help"],
    ]

    for cmd in commands_to_test:
        print(f"🔍 Testing command: {cmd}")

        try:
            result = subprocess.run(
                ["sudo", chdkptp_script] + cmd,
                cwd="/home/arrumada/Dev/CanonCameraControl/ChdkPTP",
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                print(f"✅ Command successful: {cmd}")
                print(f"Output: {result.stdout}")
            else:
                print(f"❌ Command failed: {cmd}")
                print(f"Error: {result.stderr}")

        except subprocess.TimeoutExpired:
            print(f"⏰ Command timed out: {cmd}")
        except Exception as e:
            print(f"❌ Exception: {cmd} - {e}")


def main():
    """Run all tests."""
    print("🚀 Starting CHDKPTP command tests...\n")

    test_chdkptp_help()
    print()

    test_connect_only()
    print()

    test_live_view_commands()
    print()

    print("✅ CHDKPTP command tests completed!")


if __name__ == "__main__":
    main()
