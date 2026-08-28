from pydantic import BaseModel


class Song(BaseModel):
    id: int
    name: str
    artist: str
    text: str

    def __init__(self, id: int, name: str, artist: str, text: str, **data):
        super().__init__(id=id, name=name, artist=artist, text=text, **data)

    def get_from_dict(self, **data):
        super().__init__(**data)
        self.id = int(data.get("id", 0))
        self.name = data.get("name", "")
        self.artist = data.get("artist", "")
        self.text = data.get("text", "")

    @property
    def url(self) -> str:
        return f"https://holychords.pro/{self.id}"

    def __str__(self):
        return f"{self.name} by {self.artist}"