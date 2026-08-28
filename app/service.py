import os
import textwrap
from pathlib import Path
from httpx import HTTPStatusError
from app.models import Song
from app.parser import HolyChordsParser


def get_default_output_dir() -> Path:
    one_drive_dir = os.environ.get("OneDrive")
    if one_drive_dir:
        one_drive_desktop = Path(one_drive_dir) / "Desktop"
        if one_drive_desktop.exists():
            return one_drive_desktop

    home_one_drive_desktop = Path.home() / "OneDrive" / "Desktop"
    if home_one_drive_desktop.exists():
        return home_one_drive_desktop

    return Path.home() / "Desktop"


def split_song_text(text: str, line_width: int = 30, lines_per_block: int = 2) -> str:
    result = []
    current_section = None
    block_lines = 0

    for line in text.splitlines():
        if line.startswith("##("):
            current_section = line
            block_lines = 0
            result.append(line)
            continue

        if not line:
            result.append("")
            block_lines = 0
            continue

        wrapped_lines = textwrap.wrap(
            line,
            width=line_width,
            break_long_words=False,
            break_on_hyphens=False,
        ) or [line]

        for wrapped_line in wrapped_lines:
            if current_section and block_lines >= lines_per_block:
                result.append("")
                result.append(current_section)
                block_lines = 0
            result.append(wrapped_line)
            block_lines += 1

    return "\n".join(result).strip()


def save_song(song: Song, output_dir: Path, split: bool = False) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"{song.name} ({song.artist}).txt"
    song_text = split_song_text(song.text) if split else song.text
    file_path.write_text(
        song_text,
        encoding="utf-8",
    )
    return file_path


async def fetch_song(song_id: str, output_dir: Path, split: bool = False) -> Path:
    song_parser = HolyChordsParser()
    try:
        song = await song_parser.get_song(song_id)
        return save_song(song, output_dir, split=split)
    except HTTPStatusError as error:
        raise RuntimeError(
            f"Ошибка при получении песни: {error.response.status_code} - "
            f"{error.response.reason_phrase}"
        ) from error
    except ValueError as error:
        raise RuntimeError(f"Ошибка: {error}") from error
    finally:
        await song_parser.close()
