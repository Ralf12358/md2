#!/usr/bin/env python3

import sys
import os
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from aimport import *
import md2.runtime as rt


def test_get_user_args_without_uid_gid():
    """Test get_user_args when os.getuid/getgid are not available (Windows simulation)"""

    # Temporarily remove getuid and getgid to simulate Windows
    original_getuid = getattr(os, "getuid", None)
    original_getgid = getattr(os, "getgid", None)

    try:
        # Remove the functions if they exist
        if hasattr(os, "getuid"):
            delattr(os, "getuid")
        if hasattr(os, "getgid"):
            delattr(os, "getgid")

        # Test docker on "Windows"
        args = rt.get_user_args("docker")
        assert args == [], f"Expected empty list for docker on Windows, got {args}"

        # Test podman (should still work)
        args = rt.get_user_args("podman")
        assert isinstance(args, list), "Expected list from podman args"
        assert "--userns=keep-id" in args, "Expected --userns=keep-id in podman args"

        print("✓ Windows compatibility test passed")

    finally:
        # Restore the functions if they existed
        if original_getuid is not None:
            os.getuid = original_getuid
        if original_getgid is not None:
            os.getgid = original_getgid


def test_get_user_args_with_uid_gid():
    """Test get_user_args when os.getuid/getgid are available (Unix)"""

    # This should work normally on Linux
    if hasattr(os, "getuid") and hasattr(os, "getgid"):
        args = rt.get_user_args("docker")
        assert len(args) == 2, f"Expected 2 args for docker on Unix, got {len(args)}"
        assert args[0] == "--user", f"Expected --user as first arg, got {args[0]}"
        assert ":" in args[1], f"Expected uid:gid format, got {args[1]}"
        print("✓ Unix compatibility test passed")
    else:
        print("! Skipping Unix test - no getuid/getgid available")


if __name__ == "__main__":
    test_get_user_args_without_uid_gid()
    test_get_user_args_with_uid_gid()
    print("All tests passed!")
