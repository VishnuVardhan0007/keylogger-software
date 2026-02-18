"""Tkinter GUI: logger and viewer tabs for encrypted keystroke capture and playback."""

from __future__ import annotations

import datetime as dt
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional

from . import crypto, db
from .constants import APP_TITLE, DB_FILE_TYPES, DEFAULT_DB_FILENAME, WINDOW_GEOMETRY


def _ask_db_path(save: bool, initial: str) -> Optional[str]:
    if save:
        return filedialog.asksaveasfilename(
            title="Choose database file",
            defaultextension=".db",
            filetypes=DB_FILE_TYPES,
            initialfile=initial or DEFAULT_DB_FILENAME,
        )
    return filedialog.askopenfilename(
        title="Open database file",
        filetypes=DB_FILE_TYPES,
        initialfile=initial or DEFAULT_DB_FILENAME,
    )


def _get_db_and_passphrase(
    db_path_var: tk.StringVar, passphrase_var: tk.StringVar
) -> Optional[tuple[str, str]]:
    db_path = db_path_var.get().strip()
    if not db_path:
        messagebox.showerror("Missing database", "Please choose a database file path.")
        return None
    passphrase = passphrase_var.get()
    if not passphrase:
        messagebox.showerror("Missing passphrase", "Please enter a passphrase first.")
        return None
    return (db_path, passphrase)


class LoggerTab(ttk.Frame):
    """Tab that captures keystrokes in its text area and writes encrypted logs to the DB."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        db_path_var: tk.StringVar,
        passphrase_var: tk.StringVar,
    ) -> None:
        super().__init__(master)

        self.db_path_var = db_path_var
        self.passphrase_var = passphrase_var
        self.logging_enabled = True
        self._crypto_params: Optional[crypto.CryptoParams] = None

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self)
        top.pack(side="top", fill="x", padx=10, pady=10)

        ttk.Label(top, text="Database file:").grid(row=0, column=0, sticky="w")
        entry_db = ttk.Entry(top, textvariable=self.db_path_var, width=40)
        entry_db.grid(row=0, column=1, sticky="we", padx=(4, 4))
        ttk.Button(top, text="Browse…", command=self._choose_db_path).grid(
            row=0, column=2, sticky="w"
        )

        ttk.Label(top, text="Passphrase:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        entry_pw = ttk.Entry(top, textvariable=self.passphrase_var, width=30, show="•")
        entry_pw.grid(row=1, column=1, sticky="we", padx=(4, 4), pady=(6, 0))

        self.toggle_btn = ttk.Button(top, text="Start logging", command=self._toggle_logging)
        self.toggle_btn.grid(row=1, column=2, sticky="w", pady=(6, 0))

        self.status_var = tk.StringVar(value="Logging is OFF")
        ttk.Label(top, textvariable=self.status_var).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(6, 0)
        )

        top.columnconfigure(1, weight=1)

        text_frame = ttk.Frame(self)
        text_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

        self.text = tk.Text(text_frame, wrap="word", undo=True)
        self.text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame, command=self.text.yview)
        scrollbar.pack(side="right", fill="y")
        self.text.configure(yscrollcommand=scrollbar.set)
        self.text.bind("<KeyPress>", self._on_key_press, add="+")

        ttk.Button(self, text="Clear typed text", command=self._clear_text).pack(
            side="bottom", anchor="e", padx=10, pady=(0, 10)
        )

    def _choose_db_path(self) -> None:
        path = _ask_db_path(True, self.db_path_var.get())
        if path:
            self.db_path_var.set(path)

    def _toggle_logging(self) -> None:
        if not self.logging_enabled:
            self._start_logging()
        else:
            self._stop_logging()

    def _start_logging(self) -> None:
        result = _get_db_and_passphrase(self.db_path_var, self.passphrase_var)
        if result is None:
            return
        db_path, passphrase = result

        params = db.get_or_create_crypto_params(db_path)
        self._crypto_params = params

        try:
            crypto.build_fernet(passphrase, params.salt, params.kdf_iters)
        except crypto.CryptoError as exc:
            messagebox.showerror("Crypto error", str(exc))
            return

        self.logging_enabled = True
        self.toggle_btn.configure(text="Stop logging")
        self.status_var.set(f"Logging to {db_path}")

    def _stop_logging(self) -> None:
        self.logging_enabled = False
        self.toggle_btn.configure(text="Start logging")
        self.status_var.set("Logging is OFF")

    def _clear_text(self) -> None:
        self.text.delete("1.0", "end")

    def _on_key_press(self, event: tk.Event) -> None:  # type: ignore[override]
        if not self.logging_enabled:
            return
        if event.widget is not self.text:
            return
        if self._crypto_params is None:
            return

        db_path = self.db_path_var.get().strip()
        if not db_path:
            return

        passphrase = self.passphrase_var.get()
        if not passphrase:
            return

        params = self._crypto_params
        fernet = crypto.build_fernet(passphrase, params.salt, params.kdf_iters)

        payload = {
            "char": event.char,
            "keysym": event.keysym,
            "keycode": event.keycode,
            "widget": "logger_text",
        }
        ciphertext = crypto.encrypt_json(fernet, payload)

        ts = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
        db.insert_log(
            db_path,
            ts=ts,
            event_type="key",
            keysym=event.keysym,
            keycode=event.keycode or 0,
            ciphertext=ciphertext,
        )


class ViewerTab(ttk.Frame):
    """Tab that loads and decrypts log entries from the DB and shows details."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        db_path_var: tk.StringVar,
        passphrase_var: tk.StringVar,
    ) -> None:
        super().__init__(master)
        self.db_path_var = db_path_var
        self.passphrase_var = passphrase_var
        self._rows_by_iid: Dict[str, db.LogRow] = {}

        self._build_ui()

    def _build_ui(self) -> None:
        top = ttk.Frame(self)
        top.pack(side="top", fill="x", padx=10, pady=10)

        ttk.Label(top, text="Database file:").grid(row=0, column=0, sticky="w")
        entry_db = ttk.Entry(top, textvariable=self.db_path_var, width=40)
        entry_db.grid(row=0, column=1, sticky="we", padx=(4, 4))
        ttk.Button(top, text="Browse…", command=self._choose_db_path).grid(
            row=0, column=2, sticky="w"
        )

        ttk.Label(top, text="Passphrase:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        entry_pw = ttk.Entry(top, textvariable=self.passphrase_var, width=30, show="•")
        entry_pw.grid(row=1, column=1, sticky="we", padx=(4, 4), pady=(6, 0))

        ttk.Button(top, text="Load logs", command=self._load_logs).grid(
            row=1, column=2, sticky="w", pady=(6, 0)
        )

        self.status_var = tk.StringVar(value="No logs loaded.")
        ttk.Label(top, textvariable=self.status_var).grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(6, 0)
        )

        top.columnconfigure(1, weight=1)

        middle = ttk.Frame(self)
        middle.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("ts", "event_type", "keysym", "preview")
        self.tree = ttk.Treeview(
            middle, columns=columns, show="headings", height=12, selectmode="browse"
        )
        for col in columns:
            self.tree.heading(col, text=col)
        self.tree.column("ts", width=160, anchor="w")
        self.tree.column("event_type", width=80, anchor="w")
        self.tree.column("keysym", width=100, anchor="w")
        self.tree.column("preview", width=300, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(middle, command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        bottom = ttk.LabelFrame(self, text="Details")
        bottom.pack(side="bottom", fill="both", expand=False, padx=10, pady=(0, 10))

        self.detail_text = tk.Text(bottom, height=6, wrap="word", state="disabled")
        self.detail_text.pack(fill="both", expand=True)

    def _choose_db_path(self) -> None:
        path = _ask_db_path(False, self.db_path_var.get())
        if path:
            self.db_path_var.set(path)

    def _load_logs(self) -> None:
        result = _get_db_and_passphrase(self.db_path_var, self.passphrase_var)
        if result is None:
            return
        db_path, passphrase = result

        params = db.get_existing_crypto_params(db_path)
        if params is None:
            self.status_var.set("No metadata found; no logs yet?")
            self.tree.delete(*self.tree.get_children())
            return

        try:
            fernet = crypto.build_fernet(passphrase, params.salt, params.kdf_iters)
        except crypto.CryptoError as exc:
            messagebox.showerror("Crypto error", str(exc))
            return

        rows = list(db.fetch_logs(db_path))
        self.tree.delete(*self.tree.get_children())
        self._rows_by_iid.clear()

        if not rows:
            self.status_var.set("No log entries found.")
            return

        try:
            for row in rows:
                payload = crypto.decrypt_json(fernet, row.ciphertext)
                preview = payload.get("char") or payload.get("keysym") or ""
                iid = self.tree.insert(
                    "",
                    "end",
                    values=(row.ts, row.event_type, row.keysym, preview),
                )
                self._rows_by_iid[iid] = row
        except crypto.DecryptionError as exc:
            self.tree.delete(*self.tree.get_children())
            self._rows_by_iid.clear()
            self.status_var.set("Failed to decrypt logs.")
            messagebox.showerror("Decryption error", str(exc))
            return

        self.status_var.set(f"Loaded {len(rows)} log entries.")

    def _on_select(self, event: tk.Event) -> None:  # type: ignore[override]
        selection = self.tree.selection()
        if not selection:
            return
        iid = selection[0]
        row = self._rows_by_iid.get(iid)
        if row is None:
            return

        db_path = self.db_path_var.get().strip()
        passphrase = self.passphrase_var.get()
        params = db.get_existing_crypto_params(db_path)
        if not db_path or not passphrase or params is None:
            return

        try:
            fernet = crypto.build_fernet(passphrase, params.salt, params.kdf_iters)
            payload = crypto.decrypt_json(fernet, row.ciphertext)
        except (crypto.CryptoError, crypto.DecryptionError):
            return

        self.detail_text.configure(state="normal")
        self.detail_text.delete("1.0", "end")
        for key, value in payload.items():
            self.detail_text.insert("end", f"{key}: {value}\n")
        self.detail_text.configure(state="disabled")


class App(ttk.Frame):
    """Main application frame: shared DB/passphrase vars and notebook with Logger/Viewer tabs."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.pack(fill="both", expand=True)

        self.db_path_var = tk.StringVar(value=DEFAULT_DB_FILENAME)
        self.passphrase_var = tk.StringVar()

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True)

        logger_tab = LoggerTab(
            notebook,
            db_path_var=self.db_path_var,
            passphrase_var=self.passphrase_var,
        )
        viewer_tab = ViewerTab(
            notebook,
            db_path_var=self.db_path_var,
            passphrase_var=self.passphrase_var,
        )
        notebook.add(logger_tab, text="Logger")
        notebook.add(viewer_tab, text="Viewer")


def main() -> None:
    """Create the main window and run the event loop."""
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry(WINDOW_GEOMETRY)

    style = ttk.Style(root)
    try:
        if "vista" in style.theme_names():
            style.theme_use("vista")
    except tk.TclError:
        pass

    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
