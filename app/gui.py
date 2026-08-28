import asyncio
import threading
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.notifications import show_song_saved
from app.service import fetch_song, get_default_output_dir
from app.shortcuts import bind_entry_shortcuts


def run_gui() -> None:
    app = ctk.CTk()
    app.title("HolyChords Parser")
    app.geometry("520x430")
    app.resizable(False, False)
    app.configure(fg_color="#101820")
    app.iconbitmap(Path(__file__).parent / "assets" / "icon.ico")

    header = ctk.CTkFrame(app, fg_color="transparent")
    header.pack(fill="x", padx=32, pady=(28, 6))
    ctk.CTkLabel(
        header, text="✝", text_color="#F4B860", font=("Segoe UI Symbol", 42, "bold")
    ).pack(side="left", padx=(0, 10))

    title_frame = ctk.CTkFrame(header, fg_color="transparent")
    title_frame.pack(side="left", anchor="w")
    ctk.CTkLabel(
        title_frame, text="HolyChords", text_color="#F6F1E9", font=("Segoe UI", 24, "bold")
    ).pack(anchor="w")
    ctk.CTkLabel(
        title_frame,
        text="Парсер песен с сайта holychords.pro для Holyrics",
        text_color="#9AA8B5",
        font=("Segoe UI", 12),
    ).pack(anchor="w")

    form = ctk.CTkFrame(app, fg_color="#192735", corner_radius=14)
    form.pack(fill="x", padx=28, pady=(8, 4))
    ctk.CTkLabel(
        form, text="Ссылка или ID песни", text_color="#F6F1E9", font=("Segoe UI", 14, "bold")
    ).pack(anchor="w", padx=22, pady=(18, 7))

    song_entry = ctk.CTkEntry(
        form,
        width=420,
        height=38,
        border_width=0,
        fg_color="#253747",
        text_color="#F6F1E9",
        placeholder_text_color="#8495A5",
        placeholder_text="64615 или https://holychords.pro/64615",
    )
    song_entry.pack(padx=22, pady=(0, 16))
    bind_entry_shortcuts(song_entry)

    output_dir = ctk.StringVar(value=str(get_default_output_dir()))
    ctk.CTkLabel(
        form, text="Папка сохранения", text_color="#F6F1E9", font=("Segoe UI", 14, "bold")
    ).pack(anchor="w", padx=22, pady=(0, 7))
    output_frame = ctk.CTkFrame(form, fg_color="transparent")
    output_frame.pack(fill="x", padx=22, pady=(0, 10))
    output_entry = ctk.CTkEntry(
        output_frame,
        textvariable=output_dir,
        width=320,
        height=38,
        border_width=0,
        fg_color="#253747",
        text_color="#F6F1E9",
    )
    output_entry.pack(side="left", padx=(0, 8))
    bind_entry_shortcuts(output_entry)

    split_enabled = ctk.BooleanVar(value=False)
    split_switch = ctk.CTkSwitch(
        form,
        text="Разбивка",
        variable=split_enabled,
        text_color="#F6F1E9",
        progress_color="#D98466",
        button_color="#F4B860",
        button_hover_color="#E3A34A",
    )
    split_switch.pack(anchor="w", padx=22, pady=(0, 14))

    def choose_output_dir():
        selected_dir = filedialog.askdirectory(
            parent=app,
            title="Выберите папку для сохранения",
            initialdir=output_dir.get() or str(get_default_output_dir()),
        )
        if selected_dir:
            output_dir.set(selected_dir)

    choose_button = ctk.CTkButton(
        output_frame,
        text="Выбрать",
        width=92,
        height=38,
        fg_color="#D98466",
        hover_color="#C46E52",
        command=choose_output_dir,
    )
    choose_button.pack(side="left")

    status_label = ctk.CTkLabel(
        app, text="Готово к загрузке", text_color="#9AA8B5", font=("Segoe UI", 12)
    )
    status_label.pack(pady=(0, 0))
    progress_bar = ctk.CTkProgressBar(app, width=300, mode="indeterminate")

    def finish_loading(status: str):
        progress_bar.stop()
        progress_bar.pack_forget()
        submit_button.configure(state="normal")
        choose_button.configure(state="normal")
        status_label.configure(text=status)

    def show_error(error: Exception):
        finish_loading("Ошибка загрузки")
        messagebox.showerror("Не удалось загрузить песню", str(error), parent=app)

    def show_success(file_path: Path):
        finish_loading("Песня сохранена")
        show_song_saved(file_path)

    def on_submit():
        song_id = song_entry.get().strip()
        output_value = output_dir.get().strip()
        if not song_id:
            messagebox.showwarning("Нужен ID песни", "Введите ID или ссылку на песню.", parent=app)
            return
        if not output_value:
            messagebox.showwarning("Нужна папка", "Выберите папку для сохранения.", parent=app)
            return

        submit_button.configure(state="disabled")
        choose_button.configure(state="disabled")
        progress_bar.pack(pady=(0, 8))
        progress_bar.start()
        status_label.configure(text="Загружается...")

        def load_song():
            try:
                file_path = asyncio.run(
                    fetch_song(
                        song_id,
                        Path(output_value).expanduser(),
                        split=split_enabled.get(),
                    )
                )
            except Exception as error:
                app.after(0, lambda error=error: show_error(error))
            else:
                app.after(0, lambda: show_success(file_path))

        threading.Thread(target=load_song, daemon=True).start()

    submit_button = ctk.CTkButton(
        app,
        text="Получить песню",
        width=250,
        height=42,
        corner_radius=10,
        fg_color="#F4B860",
        hover_color="#E3A34A",
        text_color="#101820",
        font=("Segoe UI", 14, "bold"),
        command=on_submit,
    )
    submit_button.pack(pady=10)
    app.mainloop()
