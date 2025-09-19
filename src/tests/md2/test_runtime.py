from aimport import *
import md2.runtime as rt
import md2.conversion as conv


def test_get_container_runtime_docker_only(monkeypatch):
    monkeypatch.setattr(
        "shutil.which", lambda name: "bin" if name == "docker" else None
    )
    assert rt.get_container_runtime() == "docker"


def test_get_container_runtime_podman_only(monkeypatch):
    monkeypatch.setattr(
        "shutil.which", lambda name: "bin" if name == "podman" else None
    )
    assert rt.get_container_runtime() == "podman"


def test_get_container_runtime_prefers_podman(monkeypatch):
    def which(name):
        return "bin" if name in ("docker", "podman") else None

    monkeypatch.setattr("shutil.which", which)
    assert rt.get_container_runtime() == "podman"