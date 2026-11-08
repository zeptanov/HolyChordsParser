from unittest.mock import AsyncMock
import unittest

import httpx

from app.parser import HolyChordsParser


class ParserTests(unittest.IsolatedAsyncioTestCase):
    async def test_removes_chord_progression_with_repeat_marker(self):
        parser = HolyChordsParser()
        html = """
        <div id="music_viewer">
            <div class="media-body">
                <a>В Твоём доме</a>
                <div class="text-muted">VL worship</div>
            </div>
        </div>
        <pre id="music_text">Intro:
        F# G# A#m C#/F x2
        Так свят и велик</pre>
        """
        response = httpx.Response(
            200,
            text=html,
            request=httpx.Request("GET", "https://holychords.pro/123"),
        )
        parser.client.get = AsyncMock(return_value=response)

        try:
            song = await parser.get_song("123")
        finally:
            await parser.close()

        self.assertNotIn("F# G# A#m C#/F x2", song.text)
        self.assertIn("Так свят и велик", song.text)


if __name__ == "__main__":
    unittest.main()
