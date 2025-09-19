import subprocess
import shutil
import os
from pathlib import Path

IMAGE_NAME = "md2:latest"


def get_container_runtime():
    # Allow override via environment variable
    env_choice = os.environ.get("RUNTIME")
    if env_choice in ("podman", "docker") and shutil.which(env_choice):
        return env_choice
    if shutil.which("podman"):
        return "podman"
    if shutil.which("docker"):
        return "docker"
    raise RuntimeError("Neither docker nor podman found")


def get_user_args(runtime: str):
    if runtime == "podman":
        args = ["--userns=keep-id"]
        # Prefer slirp4netns if available, otherwise avoid pasta by using host
        if shutil.which("slirp4netns"):
            args += ["--network=slirp4netns"]
        else:
            args += ["--network=host"]
        return args
    return ["--user", f"{_uid()}:{_gid()}"]


def _uid():
    import os

    return os.getuid()


def _gid():
    import os

    return os.getgid()


def image_exists(runtime: str, image: str = IMAGE_NAME):
    r = subprocess.run(
        [runtime, "image", "inspect", image],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return r.returncode == 0


def ensure_image(runtime: str, context_dir: Path):
    if image_exists(runtime):
        return
    subprocess.run(
        [runtime, "build", "-t", IMAGE_NAME, "-f", "Dockerfile", str(context_dir)],
        check=True,
        cwd=str(context_dir),
    )


def project_root():
    return Path(__file__).resolve().parent.parent.parent
