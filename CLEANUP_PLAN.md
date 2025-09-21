# MD2 Architecture Cleanup Plan

## Goal

Restructure the md2 project to:
- **Keep all dependencies in Docker container** (Pandoc, MathJax, Mermaid, Python libs, etc.)
- **Mount scripts/filters/styles from host** (avoid expensive Docker rebuilds during development)
- **Single source of truth**: eliminate all duplication between docker/, src/md2/, and root styles/
- **Minimal host Python dependencies**: host only needs container runtime + basic Python to invoke Docker
- **All temp/intermediate files created inside container** (clean host filesystem, especially for PDF generation where temporary HTML and intermediate PDF files are created before TOC processing)
- **Support parallel execution** (multiple processes can run simultaneously)
- **Keep both Podman and Docker support** (prefer Podman as default)

## Current State Issues

- **Triple duplication**: scripts/styles/filters exist in docker/, src/md2/, and root directories
- **Mixed execution model**: HTML uses host-mounted script, PDF uses in-container script
- **Host filesystem pollution**: temp files created on host
- **Heavy host dependencies**: Python needs all conversion libraries
- **Inconsistent runtime paths**: dev vs installed package fallbacks
- **Legacy code**: unused src/md_html_pdf/ module
- **Broken examples**: reference non-existent files and wrong CLI interface

## Planned Architecture

```
project-root/
├── src/md2/           # Minimal Python runtime (container orchestration only)
├── docker/            # All container dependencies (tools, libs, base scripts)
├── styles/            # CSS/DOCX templates (mounted into container)
├── filters/           # Pandoc Lua filters (mounted into container)
├── scripts/           # Bash conversion scripts (mounted into container)
└── examples/          # Working examples
```

## Detailed Implementation Steps

### Phase 1: Consolidate Assets (Single Source of Truth)

1. **Merge duplicate directories**:
   - Keep root `styles/` (delete `src/md2/styles/`)
   - Keep root `filters/` (delete `docker/filters/` and `src/md2/filters/`)
   - Move `docker/md2html.sh` → `scripts/md2html.sh` (delete `src/md2/md2html.sh`)
   - Move other docker scripts to `scripts/` directory

2. **Remove legacy code**:
   - Delete entire `src/md_html_pdf/` module (appears unused)
   - Clean up any imports/references to removed code

3. **Update Dockerfile**:
   - Remove `COPY styles /styles` (will be mounted)
   - Remove `COPY docker/filters /filters` (will be mounted)
   - Remove `COPY docker/md2html.sh` (will be mounted)
   - Keep only tool installations and dependencies

### Phase 2: Simplify Python Runtime

4. **Streamline `src/md2/runtime.py`**:
   - Remove all fallback path detection (`project_root()`, `get_docker_*_path()`)
   - Hardcode mount paths: `/work` (input/output), `/styles`, `/filters`, `/scripts`
   - Force Podman as default, keep Docker as fallback
   - Remove `importlib.resources` complexity

5. **Simplify `src/md2/conversion.py`**:
   - Remove `_styles_dir()` function and fallbacks
   - All temp files created in container `/tmp` (not host)
   - Standardize all commands to use mounted `/scripts/md2html.sh`
   - Remove host-side temp file creation

6. **Update packaging**:
   - Remove `md2html.sh`, `filters/*`, `styles/*` from `pyproject.toml` package-data
   - Keep only Python source files in package

### Phase 3: Container Execution Model

7. **Standardize container mounts**:
   ```bash
   -v "$(pwd)":/work
   -v "${project_root}/styles":/styles:ro
   -v "${project_root}/filters":/filters:ro
   -v "${project_root}/scripts":/scripts:ro
   ```

8. **Container temp file handling**:
   - All intermediate files in container `/tmp`
   - Use unique prefixes for parallel execution safety
   - No cleanup needed on host

9. **Update script interfaces**:
   - Scripts expect standard mount points (`/work`, `/styles`, `/filters`)
   - Remove host-path assumptions
   - Ensure scripts support parallel execution (unique temp files)

### Phase 4: Fix Examples and Tests

10. **Fix examples**:
    - Update `examples/external-css.sh` to use correct CLI commands
    - Fix script paths and argument formats
    - Ensure examples work with new architecture

11. **Update tests**:
    - Remove assertions about specific host paths
    - Test container mount points and execution
    - Add parallel execution tests

### Phase 5: Documentation and Cleanup

12. **Update documentation**:
    - README.md with new architecture
    - Installation requirements (minimal host dependencies)
    - Development workflow (mount-based, no rebuilds)

13. **Final validation**:
    - All tests pass
    - Examples work correctly
    - Parallel execution supported
    - Both Podman and Docker work

## Testing Strategy

**Pre-cleanup baseline**:
1. Generate reference outputs using `examples/doc.md`:
   ```bash
   mkdir -p baseline_outputs
   md2html examples/doc.md && mv examples/doc.html baseline_outputs/
   md2pdf examples/doc.md && mv examples/doc.pdf baseline_outputs/
   md2docx examples/doc.md && mv examples/doc.docx baseline_outputs/
   ```

**Post-cleanup validation**:
1. Generate outputs with cleaned architecture:
   ```bash
   mkdir -p cleaned_outputs
   md2html examples/doc.md && mv examples/doc.html cleaned_outputs/
   md2pdf examples/doc.md && mv examples/doc.pdf cleaned_outputs/
   md2docx examples/doc.md && mv examples/doc.docx cleaned_outputs/
   ```

2. **Binary comparison**: Ensure outputs are byte-identical
3. **Functional testing**: All CLI commands work identically
4. **Parallel execution**: Multiple processes can run simultaneously without conflicts

## Implementation

Now proceeding with the cleanup implementation following this plan.

## Benefits After Cleanup

- **Fast development**: script changes don't require Docker rebuild
- **Clean separation**: container has tools, host has minimal orchestration
- **Parallel safe**: each process gets isolated container environment
- **Simple packaging**: Python package contains only orchestration code
- **Single source**: no more duplicate files or fallback paths
- **Clean host**: all temp files contained in Docker

## Migration Safety

- Keep existing CLI interface unchanged
- **NO backward compatibility needed - no existing users**
- **Clean architecture without redundancy, fallbacks, or legacy support**
- Focus on optimal design, not migration concerns
- Only internal architecture changes
- Comprehensive testing before cleanup

## Questions for Clarification

1. Should `scripts/` be a new directory, or would you prefer `docker/` to remain for scripts?
2. For the Python package installation: should it fail fast if not in a development environment (since styles/filters won't be available)?
3. Any specific parallel execution requirements (max processes, resource limits)?
