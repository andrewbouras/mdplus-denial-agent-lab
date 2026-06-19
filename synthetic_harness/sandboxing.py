"""OS-level read barriers for retrieval-arm separation on macOS."""

from __future__ import annotations

from pathlib import Path

def _escape_profile_path(path: Path) -> str:
    return str(path.resolve()).replace("\\", "\\\\").replace('"', '\\"')


def write_web_read_barrier(
    *,
    workspace: Path,
    episode_root: Path,
    run_dir: Path,
    source_library_root: Path,
    platform_root: Path,
) -> Path:
    denied = [
        source_library_root,
        platform_root,
        episode_root / "system/library_only",
        episode_root / "sealed",
        workspace / "outputs/synthetic_patient_simulations/controller_keys",
    ]
    rules = "\n".join(
        f'  (subpath "{_escape_profile_path(path)}")' for path in denied
    )
    profile = f"""(version 1)
(allow default)
(deny file-read*
{rules}
)
"""
    path = run_dir / "web_read_barrier.sb"
    path.write_text(profile, encoding="utf-8")
    path.chmod(0o600)
    return path
