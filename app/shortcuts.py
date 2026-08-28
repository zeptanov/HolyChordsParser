from tkinter import TclError

import customtkinter as ctk


def bind_entry_shortcuts(entry: ctk.CTkEntry) -> None:
    history = [entry.get()]
    history_index = 0
    changing_history = False

    def remember_text():
        nonlocal history_index
        current_text = entry.get()
        if current_text == history[history_index]:
            return
        del history[history_index + 1 :]
        history.append(current_text)
        history_index += 1

    def replace_text(text):
        nonlocal changing_history
        changing_history = True
        entry.delete(0, "end")
        entry.insert(0, text)
        changing_history = False

    def undo():
        nonlocal history_index
        if history_index == 0:
            return
        history_index -= 1
        replace_text(history[history_index])

    def redo():
        nonlocal history_index
        if history_index >= len(history) - 1:
            return
        history_index += 1
        replace_text(history[history_index])

    def paste_from_clipboard(event=None):
        try:
            clipboard_text = entry.clipboard_get()
        except TclError:
            return "break"

        try:
            entry.delete("sel.first", "sel.last")
        except TclError:
            pass
        entry.insert("insert", clipboard_text)
        remember_text()
        return "break"

    def copy_selection():
        try:
            selected_text = entry.selection_get()
        except TclError:
            return
        entry.clipboard_clear()
        entry.clipboard_append(selected_text)

    def cut_selection():
        copy_selection()
        try:
            entry.delete("sel.first", "sel.last")
        except TclError:
            pass
        remember_text()

    def handle_shortcut(event):
        handlers = {
            65: lambda: (entry.select_range(0, "end"), entry.icursor("end")),
            67: copy_selection,
            86: paste_from_clipboard,
            88: cut_selection,
            89: redo,
            90: undo,
        }
        handler = handlers.get(event.keycode)
        if handler is not None:
            handler()
            return "break"
        return None

    entry.bind("<Control-KeyPress>", handle_shortcut, add="+")
    entry.bind(
        "<KeyRelease>",
        lambda event: remember_text() if not changing_history else None,
        add="+",
    )
    entry.bind("<Shift-KeyPress-Insert>", paste_from_clipboard, add="+")
