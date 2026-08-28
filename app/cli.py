import argparse
import asyncio
from pathlib import Path

from app.service import fetch_song, get_default_output_dir


def build_argument_parser() -> argparse.ArgumentParser:
    argument_parser = argparse.ArgumentParser(description="HolyChords Parser")
    argument_parser.add_argument("song_id", help="ID или ссылка на песню")
    argument_parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=get_default_output_dir(),
        help="папка для сохранения (по умолчанию: рабочий стол)",
    )
    argument_parser.add_argument(
        "--split",
        action="store_true",
        help="разбивать длинные строки песни на компактные блоки",
    )
    return argument_parser


def run_cli() -> None:
    args = build_argument_parser().parse_args()
    try:
        file_path = asyncio.run(
            fetch_song(args.song_id, args.output_dir, split=args.split)
        )
        print(f"Песня сохранена: {file_path}")
    except Exception as error:
        print(f"Ошибка: {error}")
