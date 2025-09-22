"""Integration test for container-based image validation."""

import tempfile
from pathlib import Path
from md2.conversion import md2html
import subprocess
import sys


def test_container_image_validation():
    """Test that container-based image validation works correctly."""

    # Test with remote images - should show warnings
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(
            """# Test Remote Images

![Valid Image](https://github.githubassets.com/assets/GitHub-Mark-ea2971cee799.png)
![Invalid Image](https://example.com/nonexistent.jpg)
![Private Image](https://github.com/private/repo/image.png)
"""
        )
        f.flush()

        temp_path = Path(f.name)

    try:
        # Capture stderr to check for warnings
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"from md2.conversion import md2html; md2html(['{temp_path}'])",
            ],
            capture_output=True,
            text=True,
            cwd=temp_path.parent,
        )

        # Should have warnings about invalid images
        assert "WARNING" in result.stderr
        assert "inaccessible remote image" in result.stderr
        assert "nonexistent.jpg" in result.stderr

    finally:
        temp_path.unlink()
        html_file = temp_path.with_suffix(".html")
        if html_file.exists():
            html_file.unlink()

    # Test without remote images - should not show validation warnings
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write("# Test Local Only\n\n![Local](local.png)")
        f.flush()
        temp_path = Path(f.name)

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                f"from md2.conversion import md2html; md2html(['{temp_path}'])",
            ],
            capture_output=True,
            text=True,
            cwd=temp_path.parent,
        )

        # Should not have image validation warnings (may have pandoc warnings about missing local file)
        assert "inaccessible remote image" not in result.stderr

    finally:
        temp_path.unlink()
        html_file = temp_path.with_suffix(".html")
        if html_file.exists():
            html_file.unlink()


if __name__ == "__main__":
    test_container_image_validation()
    print("✓ Container-based image validation test passed")
