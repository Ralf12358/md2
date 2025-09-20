from aimport import *
import subprocess
import shutil
import os
import importlib.resources
from pathlib import Path
from typing import List

IMAGE_NAME = "md2:latest"


def get_container_runtime() -> str:
    # Allow override via environment variable
    env_choice = os.environ.get("RUNTIME")
    if env_choice in ("podman", "docker") and shutil.which(env_choice):
        return env_choice
    if shutil.which("podman"):
        return "podman"
    if shutil.which("docker"):
        return "docker"
    raise RuntimeError("Neither docker nor podman found")


def get_user_args(runtime: str) -> List[str]:
    if runtime == "podman":
        args = ["--userns=keep-id"]
        # Prefer slirp4netns if available, otherwise avoid pasta by using host
        if shutil.which("slirp4netns"):
            args += ["--network=slirp4netns"]
        else:
            args += ["--network=host"]
        return args
    return ["--user", f"{_uid()}:{_gid()}"]


def _uid() -> int:
    return os.getuid()


def _gid() -> int:
    return os.getgid()


def image_exists(runtime: str, image: str = IMAGE_NAME) -> bool:
    r = subprocess.run(
        [runtime, "image", "inspect", image],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return r.returncode == 0


def ensure_image(runtime: str, context_dir: Path) -> None:
    if image_exists(runtime):
        return
    subprocess.run(
        [runtime, "build", "-t", IMAGE_NAME, "-f", "Dockerfile", str(context_dir)],
        check=True,
        cwd=str(context_dir),
    )


def project_root() -> Path:
    # For development: use relative path from source
    # For installed package: use package data directory
    current_file = Path(__file__).resolve()
    
    # Try development structure first: src/md2/runtime.py -> project_root
    dev_root = current_file.parent.parent.parent
    if (dev_root / "docker" / "md2html.sh").exists():
        return dev_root
    
    # For installed package: assets are packaged alongside the module
    package_root = current_file.parent
    return package_root


def get_docker_script_path() -> Path:
    # For development environment
    dev_path = project_root() / "docker" / "md2html.sh"
    if dev_path.exists():
        return dev_path
    
    # For installed package, use importlib.resources
    try:
        with importlib.resources.path("md2", "md2html.sh") as path:
            return path
    except (ImportError, FileNotFoundError):
        # Fallback to package directory
        return Path(__file__).parent / "md2html.sh"


def get_docker_filters_path() -> Path:
    # For development environment
    dev_path = project_root() / "docker" / "filters"
    if dev_path.exists():
        return dev_path
    
    # For installed package
    try:
        with importlib.resources.path("md2", "filters") as path:
            return path
    except (ImportError, FileNotFoundError):
        # Fallback to package directory
        return Path(__file__).parent / "filters"
