from pathlib import Path


def show_song_saved(file_path: Path) -> None:
    try:
        from winotify import Notification, audio

        toast = Notification(
            app_id="HolyChords Parser",
            title="Песня сохранена",
            msg=str(file_path),
        )
        toast.set_audio(audio.Default, loop=False)
        toast.show()
    except ImportError:
        pass
