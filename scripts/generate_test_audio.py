#!/usr/bin/env python3
"""Generate local speech fixtures for tellm protocol tests."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


FIXTURES = [
    {
        "id": "tellm-pl-pogoda",
        "language": "pl",
        "voice": "pl",
        "text": "Jaka jest pogoda w Warszawie?",
    },
    {
        "id": "tellm-pl-zadanie",
        "language": "pl",
        "voice": "pl",
        "text": "Dodaj zadanie na jutro o dziewiątej.",
    },
]

FORMATS = {
    "webm": ["-c:a", "libopus", "-b:a", "32k"],
    "ogg": ["-c:a", "libopus", "-b:a", "32k"],
    "mp3": ["-c:a", "libmp3lame", "-b:a", "64k"],
    "m4a": ["-c:a", "aac", "-b:a", "64k"],
}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def require_tool(name: str) -> str:
    path = shutil.which(name)
    if not path:
        raise SystemExit(f"Missing required tool: {name}")
    return path


def generate_fixture(output_dir: Path, fixture: dict) -> dict:
    base = output_dir / fixture["id"]
    wav_path = base.with_suffix(".wav")

    run(
        [
            require_tool("espeak-ng"),
            "-v",
            fixture["voice"],
            "-s",
            "145",
            "-w",
            str(wav_path),
            fixture["text"],
        ]
    )

    files = [{"format": "wav", "path": str(wav_path)}]
    ffmpeg = require_tool("ffmpeg")
    for suffix, args in FORMATS.items():
        out_path = base.with_suffix("." + suffix)
        run(
            [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(wav_path),
                *args,
                str(out_path),
            ]
        )
        files.append({"format": suffix, "path": str(out_path)})

    return {
        "id": fixture["id"],
        "language": fixture["language"],
        "text": fixture["text"],
        "files": files,
    }


def main() -> None:
    output_dir = Path("output/test-audio")
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = [generate_fixture(output_dir, fixture) for fixture in FIXTURES]
    manifest = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "generator": "scripts/generate_test_audio.py",
        "fixtures": generated,
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    print(manifest_path)
    for fixture in generated:
        for file_info in fixture["files"]:
            print(file_info["path"])


if __name__ == "__main__":
    main()
