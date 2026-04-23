from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

import yaml
from huggingface_hub import snapshot_download

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare OpenAI Privacy Filter upstream code + checkpoint locally."
    )
    parser.add_argument(
        "--config",
        default="configs/fine_tune_config.yaml",
        help="Path to YAML config file.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading checkpoint from Hugging Face.",
    )
    parser.add_argument(
        "--install-opf",
        action="store_true",
        help="Install OPF package from local cloned upstream repo (pip install -e .).",
    )
    return parser.parse_args()


def run(command: list[str], cwd: Path | None = None) -> None:
    subprocess.run(command, check=True, cwd=cwd)


def load_config(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as infile:
        return yaml.safe_load(infile)


def ensure_upstream_clone(repo_url: str, commit: str, local_dir: Path) -> None:
    local_dir.parent.mkdir(parents=True, exist_ok=True)
    if not local_dir.exists():
        run(["git", "clone", repo_url, str(local_dir)])
    run(["git", "fetch", "--all", "--tags"], cwd=local_dir)
    run(["git", "checkout", commit], cwd=local_dir)


def download_checkpoint(repo_id: str, revision: str, local_dir: Path) -> None:
    if local_dir.exists():
        shutil.rmtree(local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=repo_id,
        revision=revision,
        local_dir=str(local_dir),
        local_dir_use_symlinks=False,
        allow_patterns=["original/*"],
    )
    original_dir = local_dir / "original"
    if not original_dir.is_dir():
        raise RuntimeError(
            f"Downloaded checkpoint is missing expected subtree: {original_dir}"
        )
    for path in original_dir.iterdir():
        destination = local_dir / path.name
        if destination.exists():
            raise RuntimeError(f"Destination already exists while promoting: {destination}")
        shutil.move(str(path), str(destination))
    original_dir.rmdir()


def install_local_opf(local_dir: Path) -> None:
    run(["python", "-m", "pip", "install", "-e", "."], cwd=local_dir)


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).expanduser()
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    cfg = load_config(config_path)

    opf_cfg = cfg["opf"]
    repo_url = opf_cfg["upstream_repo_url"]
    pinned_commit = opf_cfg["upstream_pinned_commit"]
    upstream_local_dir = Path(opf_cfg["upstream_local_dir"]).expanduser()
    hf_repo_id = opf_cfg["hf_repo_id"]
    hf_revision = opf_cfg["hf_revision"]
    checkpoint_local_dir = Path(opf_cfg["checkpoint_local_dir"]).expanduser()
    if not upstream_local_dir.is_absolute():
        upstream_local_dir = PROJECT_ROOT / upstream_local_dir
    if not checkpoint_local_dir.is_absolute():
        checkpoint_local_dir = PROJECT_ROOT / checkpoint_local_dir

    ensure_upstream_clone(repo_url, pinned_commit, upstream_local_dir)
    if args.install_opf:
        install_local_opf(upstream_local_dir)
    if not args.skip_download:
        download_checkpoint(hf_repo_id, hf_revision, checkpoint_local_dir)

    print("OPF stack is ready.")
    print(f"Upstream dir: {upstream_local_dir}")
    print(f"Checkpoint dir: {checkpoint_local_dir}")


if __name__ == "__main__":
    main()
