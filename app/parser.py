import re
import httpx
from bs4 import BeautifulSoup
from app.models import Song
from urllib.parse import urlparse

BASE_URL = "https://holychords.pro"

CHORD_LINE_PATTERN = re.compile(
    r"^\s*"
    r"(?:"
    r"[A-GH](?:#|b)?"
    r"(?:maj|min|m|dim|aug|sus|add)?"
    r"(?:\d+)?"
    r"(?:/[A-GH](?:#|b)?)?"
    r"(?:\s+|$)"
    r")+"
    r"(?:[xх]\s*\d+)?"
    r"\s*$",
    re.IGNORECASE,
)


def normalize_song_id(song_id_or_url: str) -> str:
    value = song_id_or_url.strip()
    if not value:
        raise ValueError("Введите ID или ссылку на песню")

    if value.startswith(("http://", "https://")):
        parsed_url = urlparse(value)
        if parsed_url.netloc.lower() not in {"holychords.pro", "www.holychords.pro"}:
            raise ValueError("Ссылка должна вести на holychords.pro")
        value = parsed_url.path.rstrip("/").split("/")[-1]

    if not value.isdigit():
        raise ValueError("ID песни должен быть числом или ссылкой на песню")

    return value


class HolyChordsParser:
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/139.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            },
        )

    async def close(self):
        await self.client.aclose()

    async def get_song(self, song_id: str) -> Song:
        normalized_song_id = normalize_song_id(song_id)
        url = f"{BASE_URL}/{normalized_song_id}"
        response = await self.client.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        # =========================================================
        # НАЗВАНИЕ
        # =========================================================

        title_element = soup.select_one("#music_viewer .media-body > a")
        title = (
            title_element.get_text(
                " ",
                strip=True,
            )
            if title_element
            else ""
        )

        # =========================================================
        # ИСПОЛНИТЕЛЬ
        # =========================================================

        artist_element = soup.select_one("#music_viewer .media-body .text-muted")
        artist = (
            artist_element.get_text(
                " ",
                strip=True,
            )
            if artist_element
            else ""
        )

        # =========================================================
        # ТЕКСТ ПЕСНИ
        # =========================================================

        music_text = soup.select_one("#music_text")
        if music_text is None:
            raise ValueError("Не найден #music_text")
        for chord_element in music_text.select(".chopds"):
            chord_element.decompose()
        raw_text = music_text.get_text(
            "\n",
            strip=False,
        )

        # =========================================================
        # REGEX ДЛЯ АККОРДОВ
        # =========================================================

        # =========================================================
        # REGEX ДЛЯ ЗАГОЛОВКОВ
        # =========================================================
        #
        # Поддерживает:
        #
        # Куплет:
        # Куплет x2:
        # Куплет x3:
        # Припев:
        # Припев x2:
        # Вставка x2:
        # Интро: х2
        #
        # И пробелы вокруг.
        #

        section_pattern = re.compile(
            r"^\s*(.+?)\s*:\s*(.*?)\s*$",
            re.IGNORECASE,
        )
        lines = []

        # =========================================================
        # ОБРАБОТКА СТРОК
        # =========================================================
        for raw_line in raw_text.splitlines():
            line = raw_line.strip()

            # Пустая строка
            if not line:
                lines.append("")
                continue

            # Аккорды
            if CHORD_LINE_PATTERN.match(line):
                continue

            # Заголовок секции
            section_match = section_pattern.match(line)
            if section_match:
                name = section_match.group(1).strip()
                suffix = section_match.group(2).strip()
                if suffix:
                    section = f"{name} {suffix}"
                else:
                    section = name
                lines.append(f"##({section})")
                continue

            # Обычный текст
            lines.append(line)

        # =========================================================
        # УБИРАЕМ ЛИШНИЕ ПУСТЫЕ СТРОКИ
        # =========================================================
        result = []
        previous_empty = False
        for line in lines:
            if not line:
                if not previous_empty:
                    result.append("")
                previous_empty = True
            else:
                result.append(line)
                previous_empty = False
        filtered_result = []
        for index, line in enumerate(result):
            if line.startswith("##("):
                next_section_index = index + 1
                while (
                    next_section_index < len(result)
                    and not result[next_section_index].startswith("##(")
                ):
                    next_section_index += 1
                has_section_text = any(
                    result[index + 1 : next_section_index]
                )
                if not has_section_text:
                    continue
            filtered_result.append(line)
        result = filtered_result
        text = "\n".join(result).strip()

        # =========================================================
        # ФИНАЛЬНАЯ ЧИСТКА ПУСТЫХ СТРОК
        # =========================================================
        text = re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        ).strip()

        return Song(
            id=normalized_song_id,
            name=title,
            artist=artist,
            text=text,
        )

