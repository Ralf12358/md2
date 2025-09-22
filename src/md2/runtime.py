import subprocess
import shutil
import os
from pathlib import Path
from typing import List

IMAGE_NAME = "md2:latest"
PROJECT_ROOT = Path(__file__).parent


def get_container_runtime() -> str:
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
        if shutil.which("slirp4netns"):
            args += ["--network=slirp4netns"]
        else:
            args += ["--network=host"]
        return args
    return ["--user", f"{os.getuid()}:{os.getgid()}"]


def get_security_args(runtime: str) -> List[str]:
    return [
        "--cap-add=SYS_ADMIN",
        "--security-opt=seccomp=unconfined",
        "--shm-size=1g",
    ]


def image_exists(runtime: str, image: str = IMAGE_NAME) -> bool:
    r = subprocess.run(
        [runtime, "image", "inspect", image],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return r.returncode == 0


def ensure_image(runtime: str, root: Path | None = None) -> None:
    if image_exists(runtime):
        return
    context = PROJECT_ROOT if root is None else root
    subprocess.run(
        [runtime, "build", "-t", IMAGE_NAME, "-f", "Dockerfile", str(context)],
        check=True,
        cwd=str(context),
    )
