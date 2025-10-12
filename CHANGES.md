# md2 v0.9.0 Release Notes

## New Features

### md2rebuild Command

Added a new CLI command `md2rebuild` that forces a complete rebuild of the Docker/Podman container image, ignoring all cached layers.

**Usage:**
```bash
md2rebuild
```

**When to use:**
- After modifying the Dockerfile
- To pull updated base images
- When troubleshooting container-related issues
- To ensure a clean build from scratch

**Implementation:**
- New `rebuild_image()` function in `src/md2/runtime.py`
- New CLI entry point `main_md2rebuild()` in `src/md2/cli.py`
- Registered as console script in `pyproject.toml`
- Uses `--no-cache` flag to bypass Docker/Podman build cache

## Modified Files

- `src/md2/runtime.py`: Added `rebuild_image()` function
- `src/md2/cli.py`: Added `main_md2rebuild()` and `usage_md2rebuild()` functions
- `pyproject.toml`: 
  - Added `md2rebuild` to `[project.scripts]`
  - Version bumped from 0.8.4 to 0.9.0
- `README.md`: Added documentation for `md2rebuild` command

## Testing

Added test files:
- `src/tmp_tests/test_rebuild.py`: Tests for CLI argument handling
- `src/tmp_tests/test_rebuild_integration.py`: Tests for runtime module functions

All new tests pass successfully.
