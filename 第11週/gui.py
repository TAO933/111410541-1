#!/usr/bin/env python3
"""Nand2Tetris VM 翻譯器的 Tkinter 圖形介面。

執行:
    py gui.py
"""
import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox, ttk

from vm_translator import default_output, find_vm_files, translate_source

FONT = ("Microsoft JhengHei UI", 10)
MONO_FONT = ("Consolas", 9)

BOOTSTRAP_CHOICES = (
    ("自動（單檔不加、資料夾加入）", "auto"),
    ("一律加入（呼叫 Sys.init）", "yes"),
    ("一律不加", "no"),
)


class VMTranslatorApp(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=16)
        self.master = master

        self._setup_window()
        self._setup_style()
        self._build_widgets()

    # ------------------------------------------------------------------
    # 視窗外觀
    # ------------------------------------------------------------------
    def _setup_window(self):
        self.master.title("Nand2Tetris VM 翻譯器")
        self.master.geometry("820x620")
        self.master.minsize(680, 520)
        self.master.columnconfigure(0, weight=1)
        self.master.rowconfigure(0, weight=1)
        self.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(5, weight=1)

        self.master.bind("<Control-o>", lambda _: self.choose_file())
        self.master.bind("<Control-O>", lambda _: self.choose_folder())
        self.master.bind("<Control-Return>", lambda _: self.on_translate())

    def _setup_style(self):
        style = ttk.Style(self)
        if os.name == "nt":
            try:
                style.theme_use("vista")
            except tk.TclError:
                pass

        style.configure("TLabel", font=FONT)
        style.configure("TButton", font=FONT)
        style.configure("TRadiobutton", font=FONT)
        style.configure("TLabelframe.Label", font=(FONT[0], FONT[1], "bold"))
        style.configure("Title.TLabel", font=(FONT[0], 18, "bold"))
        style.configure("Subtitle.TLabel", foreground="#666666")
        style.configure("Primary.TButton",
                        font=(FONT[0], 11, "bold"), padding=(20, 8))
        style.configure("Status.TLabel", foreground="#555555")

    # ------------------------------------------------------------------
    # 版面
    # ------------------------------------------------------------------
    def _build_widgets(self):
        self._build_header()
        self._build_source_box()
        self._build_output_box()
        self._build_options_box()
        self._build_action_bar()
        self._build_log_box()
        self._build_status_bar()

    def _build_header(self):
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Nand2Tetris VM 翻譯器",
                  style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="把 .vm 檔或整個資料夾翻譯成 Hack 組合語言（.asm）",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

    def _build_source_box(self):
        box = ttk.LabelFrame(self, text="輸入", padding=12)
        box.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="來源").grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.source_var = tk.StringVar()
        ttk.Entry(box, textvariable=self.source_var,
                  state="readonly").grid(row=0, column=1, sticky="ew")

        ttk.Button(box, text="選擇 .vm 檔",
                   command=self.choose_file).grid(row=0, column=2, padx=(10, 0))
        ttk.Button(box, text="選擇資料夾",
                   command=self.choose_folder).grid(row=0, column=3, padx=(8, 0))

    def _build_output_box(self):
        box = ttk.LabelFrame(self, text="輸出", padding=12)
        box.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text=".asm 檔").grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.output_var = tk.StringVar()
        ttk.Entry(box, textvariable=self.output_var).grid(
            row=0, column=1, sticky="ew")

        ttk.Button(box, text="另存新檔...",
                   command=self.choose_output).grid(row=0, column=2, padx=(10, 0))

    def _build_options_box(self):
        box = ttk.LabelFrame(self, text="選項", padding=12)
        box.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        box.columnconfigure(0, weight=1)

        ttk.Label(box, text="Bootstrap").grid(row=0, column=0, sticky="w")

        radios = ttk.Frame(box)
        radios.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.bootstrap_var = tk.StringVar(value="auto")
        for text, value in BOOTSTRAP_CHOICES:
            ttk.Radiobutton(radios, text=text, value=value,
                            variable=self.bootstrap_var).pack(
                side="left", padx=(0, 18))

        ttk.Label(
            box,
            text="自動模式會依輸入類型決定：單一檔案不加 bootstrap，"
                 "資料夾則加入並呼叫 Sys.init。",
            foreground="#777777",
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

    def _build_action_bar(self):
        bar = ttk.Frame(self)
        bar.grid(row=4, column=0, sticky="ew", pady=(0, 10))
        bar.columnconfigure(0, weight=1)

        self.open_folder_btn = ttk.Button(
            bar, text="開啟輸出資料夾",
            command=self.open_output_folder, state="disabled")
        self.open_folder_btn.grid(row=0, column=0, sticky="w")

        self.translate_btn = ttk.Button(
            bar, text="開始翻譯", style="Primary.TButton",
            command=self.on_translate)
        self.translate_btn.grid(row=0, column=1, sticky="e")

    def _build_log_box(self):
        box = ttk.LabelFrame(self, text="執行紀錄", padding=8)
        box.grid(row=5, column=0, sticky="nsew")
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)

        self.log_text = tk.Text(
            box, height=10, wrap="word", state="disabled",
            font=MONO_FONT, borderwidth=0, highlightthickness=0,
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            box, orient="vertical", command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _build_status_bar(self):
        self.status_var = tk.StringVar(
            value="請選擇要翻譯的 .vm 檔或資料夾。")
        ttk.Label(self, textvariable=self.status_var,
                  style="Status.TLabel", anchor="w").grid(
            row=6, column=0, sticky="ew", pady=(10, 0))

    # ------------------------------------------------------------------
    # 事件處理
    # ------------------------------------------------------------------
    def choose_file(self):
        path = filedialog.askopenfilename(
            parent=self.master,
            title="選擇 VM 檔",
            filetypes=[("VM 檔案", "*.vm"), ("所有檔案", "*.*")],
        )
        if path:
            self._set_source(path)

    def choose_folder(self):
        path = filedialog.askdirectory(
            parent=self.master,
            title="選擇包含 .vm 檔的資料夾",
        )
        if path:
            self._set_source(path)

    def choose_output(self):
        current = self.output_var.get().strip()
        options = {
            "parent": self.master,
            "title": "選擇輸出檔",
            "defaultextension": ".asm",
            "filetypes": [("Hack 組合語言", "*.asm"), ("所有檔案", "*.*")],
        }
        if current:
            options["initialdir"] = os.path.dirname(current) or os.getcwd()
            options["initialfile"] = os.path.basename(current)

        path = filedialog.asksaveasfilename(**options)
        if path:
            self.output_var.set(path)

    def _set_source(self, path):
        path = os.path.normpath(path)
        self.source_var.set(path)

        try:
            files, is_dir = find_vm_files(path)
        except ValueError as exc:
            self.output_var.set("")
            self.status_var.set("輸入無效")
            self._log(f"[{self._now()}] 錯誤：{exc}")
            messagebox.showerror("輸入無效", str(exc), parent=self.master)
            return

        self.output_var.set(default_output(path, is_dir))
        self._log(f"[{self._now()}] 已選擇輸入：{path}")
        if is_dir:
            self._log(f"    找到 {len(files)} 個 .vm 檔：")
            for vm_file in files:
                self._log(f"    - {os.path.basename(vm_file)}")
            self.status_var.set(
                f"已選擇資料夾：{os.path.basename(path)}"
                f"（{len(files)} 個 .vm 檔）")
        else:
            self.status_var.set(f"已選擇檔案：{os.path.basename(path)}")

    def on_translate(self):
        source = self.source_var.get().strip()
        if not source:
            messagebox.showwarning(
                "尚未選擇輸入", "請先選擇 .vm 檔或資料夾。",
                parent=self.master)
            return

        output = self.output_var.get().strip() or None
        bootstrap_mode = self.bootstrap_var.get()
        bootstrap = {"auto": None, "yes": True, "no": False}[bootstrap_mode]

        self.translate_btn.config(state="disabled")
        self.open_folder_btn.config(state="disabled")
        self.status_var.set("翻譯中，請稍候...")
        self._log(f"[{self._now()}] 開始翻譯：{source}")
        self.update_idletasks()

        try:
            stats = translate_source(source, output, bootstrap)
        except Exception as exc:
            self._log(f"[{self._now()}] 翻譯失敗：{exc}")
            self.status_var.set("翻譯失敗")
            messagebox.showerror("翻譯失敗", str(exc), parent=self.master)
            return
        finally:
            self.translate_btn.config(state="normal")

        self.output_var.set(stats["output"])
        self.open_folder_btn.config(state="normal")

        used_bootstrap = "是" if stats["bootstrap"] else "否"
        self._log(f"[{self._now()}] 翻譯完成：{stats['output']}")
        self._log(
            f"    檔案 {len(stats['files'])} 個；"
            f"指令 {stats['count']} 道；bootstrap：{used_bootstrap}")
        self.status_var.set(f"翻譯完成 → {stats['output']}")

        messagebox.showinfo(
            "翻譯完成",
            f"已產生：\n{stats['output']}\n\n"
            f"檔案 {len(stats['files'])} 個，"
            f"指令 {stats['count']} 道，bootstrap：{used_bootstrap}",
            parent=self.master,
        )

    def open_output_folder(self):
        output = self.output_var.get().strip()
        if not output:
            return
        folder = os.path.dirname(os.path.abspath(output))
        if not os.path.isdir(folder):
            messagebox.showerror(
                "找不到資料夾", f"資料夾不存在：\n{folder}",
                parent=self.master)
            return
        try:
            if hasattr(os, "startfile"):
                os.startfile(folder)
            else:
                import subprocess
                subprocess.Popen(["xdg-open", folder])
        except OSError as exc:
            messagebox.showerror(
                "無法開啟資料夾", str(exc), parent=self.master)

    # ------------------------------------------------------------------
    # 小工具
    # ------------------------------------------------------------------
    def _log(self, text):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    @staticmethod
    def _now():
        return datetime.now().strftime("%H:%M:%S")


def main():
    if os.name == "nt":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            pass

    root = tk.Tk()
    VMTranslatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
