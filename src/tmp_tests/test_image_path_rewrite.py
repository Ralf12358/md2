"""Test image path extraction and copying for container conversion."""

import pytest
from pathlib import Path
from md2.conversion import collect_local_images, copy_images_and_rewrite


@pytest.fixture
def test_md_with_abs_paths(tmp_path):
    """Create a markdown file with absolute image paths."""
    # Create image directories
    img_dir1 = tmp_path / "images1"
    img_dir1.mkdir()
    (img_dir1 / "cover.png").write_bytes(b"PNG")

    img_dir2 = tmp_path / "subdir" / "images2"
    img_dir2.mkdir(parents=True)
    (img_dir2 / "diagram.svg").write_bytes(b"SVG")

    # Create markdown in a different directory
    md_dir = tmp_path / "docs"
    md_dir.mkdir()

    content = f"""# Test Document

![Cover]({img_dir1}/cover.png)

Some text here.

![Another]({img_dir2}/diagram.svg)

And relative image: ![Rel](./local.png)
"""
    md_file = md_dir / "test.md"
    md_file.write_text(content)
    return md_file, img_dir1, img_dir2, md_dir


def test_collect_local_images(test_md_with_abs_paths):
    """Test that absolute image paths are collected."""
    md_file, img_dir1, img_dir2, _ = test_md_with_abs_paths

    images = collect_local_images(md_file)

    assert img_dir1 / "cover.png" in images
    assert img_dir2 / "diagram.svg" in images


def test_collect_local_images_skips_urls(tmp_path):
    """Test that HTTP URLs are not collected."""
    md_file = tmp_path / "test.md"
    md_file.write_text(
        """
![Remote](https://example.com/image.png)
![Local](/tmp/local.png)
"""
    )

    images = collect_local_images(md_file)

    assert not any("example.com" in str(img) for img in images)


def test_copy_images_and_rewrite(test_md_with_abs_paths):
    """Test that external images are copied and paths rewritten."""
    md_file, img_dir1, img_dir2, md_dir = test_md_with_abs_paths

    content = md_file.read_text()
    rewritten, copied = copy_images_and_rewrite(content, md_file.parent, md_dir)

    # Check paths were rewritten to relative
    assert str(img_dir1) not in rewritten
    assert str(img_dir2) not in rewritten
    assert "cover.png" in rewritten
    assert "diagram.svg" in rewritten

    # Check files were copied
    assert len(copied) == 2
    assert (md_dir / "cover.png").exists()
    assert (md_dir / "diagram.svg").exists()


def test_copy_preserves_urls(tmp_path):
    """Test that HTTP URLs are not modified."""
    content = """![Remote](https://example.com/image.png)"""
    target = tmp_path / "work"
    target.mkdir()

    rewritten, copied = copy_images_and_rewrite(content, tmp_path, target)

    assert "https://example.com/image.png" in rewritten
    assert len(copied) == 0
