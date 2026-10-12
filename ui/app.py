
import queue
import re
import threading
import tkinter as tk
from tkinter import ttk

from core.engine import PolyCodeEngine


APP_NAME = "PolyCode IDE"
VERSION = "0.0.4"

C = {
    "bg": "#0B1120",
    "toolbar": "#111C30",
    "editor": "#0D1526",
    "gutter": "#101B2E",
    "output": "#0A1220",
    "border": "#233653",
    "blue": "#4DA3FF",
    "blue_hover": "#3289ED",
    "text": "#DCE8F8",
    "muted": "#7F95B5",
    "selection": "#203C60",
    "purple": "#C4A1FF",
    "string": "#A5E0A0",
    "number": "#FFBD7A",
    "comment": "#7189A6",
    "function": "#82C7FF",
    "error": "#FF8585",
}

STARTER_CODE = '''@python
print("Hello from Python!")

@cpp
cout << "Hello from C++" << endl;

@javascript
console.log("Hello from JavaScript");
'''


class PolyCodeApp:
    def __init__(self, root):
        self.root = root
        self.engine = PolyCodeEngine()
        self.result_queue = queue.Queue()
        self.running = False
        self.highlight_job = None
        self._gutter_syncing = False

        self.root.title(f"{APP_NAME} • v{VERSION}")
        self.root.geometry("1200x760")
        self.root.minsize(760, 480)
        self.root.configure(bg=C["bg"])

        self._build_layout()
        self._configure_tags()
        self._bind_shortcuts()

        self.editor.insert("1.0", STARTER_CODE)
        self.editor.edit_modified(False)
        self._update_line_numbers()
        self._schedule_highlighting()

        self.editor.focus_set()
        self.root.after(100, self._poll_results)
        self.root.after(180, self._set_initial_split)

    def _build_layout(self):
        style = ttk.Style()
        style.theme_use("clam")

        # Dark scrollbars: no white trough, border, or relief.
        style.configure(
            "Dark.Vertical.TScrollbar",
            background="#17243A",
            troughcolor=C["editor"],
            bordercolor=C["editor"],
            darkcolor="#17243A",
            lightcolor="#17243A",
            arrowcolor="#7F95B5",
            relief="flat",
            borderwidth=0,
            arrowsize=10,
        )
        style.map(
            "Dark.Vertical.TScrollbar",
            background=[
                ("active", "#31527A"),
                ("pressed", "#3B6596"),
            ],
            arrowcolor=[("active", C["blue"])],
        )

        style.configure(
            "Dark.Horizontal.TScrollbar",
            background="#17243A",
            troughcolor=C["editor"],
            bordercolor=C["editor"],
            darkcolor="#17243A",
            lightcolor="#17243A",
            arrowcolor="#7F95B5",
            relief="flat",
            borderwidth=0,
            arrowsize=10,
        )
        style.map(
            "Dark.Horizontal.TScrollbar",
            background=[
                ("active", "#31527A"),
                ("pressed", "#3B6596"),
            ],
            arrowcolor=[("active", C["blue"])],
        )

        # The sash uses the same color as the application background.
        style.configure(
            "Blue.Vertical.TPanedwindow",
            background=C["bg"],
            sashwidth=7,
            sashrelief="flat",
            sashpad=0,
            borderwidth=0,
        )

        toolbar = tk.Frame(self.root, bg=C["toolbar"], height=48)
        toolbar.pack(fill="x", padx=8, pady=(8, 4))
        toolbar.pack_propagate(False)

        tk.Label(
            toolbar,
            text="  ◈  PolyCode",
            bg=C["toolbar"],
            fg=C["blue"],
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left", padx=8)

        self.status_label = tk.Label(
            toolbar,
            text="Ready",
            bg=C["toolbar"],
            fg=C["muted"],
            font=("Segoe UI", 9),
        )
        self.status_label.pack(side="left", padx=16)

        tk.Button(
            toolbar,
            text="Clear",
            command=self.clear_editor,
            bg=C["toolbar"],
            fg=C["blue"],
            activebackground=C["selection"],
            activeforeground=C["text"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            padx=15,
            pady=5,
        ).pack(side="right", padx=(4, 8), pady=6)

        self.run_button = tk.Button(
            toolbar,
            text="▶  Run",
            command=self.run_code,
            bg=C["blue"],
            fg="#07101E",
            activebackground=C["blue_hover"],
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI", 10, "bold"),
            cursor="hand2",
            padx=18,
            pady=5,
        )
        self.run_button.pack(side="right", padx=4, pady=6)

        self.paned = ttk.Panedwindow(
            self.root,
            orient="vertical",
            style="Blue.Vertical.TPanedwindow",
        )
        self.paned.pack(fill="both", expand=True, padx=8, pady=(2, 8))

        editor_frame = tk.Frame(
            self.paned,
            bg=C["editor"],
            highlightthickness=1,
            highlightbackground=C["border"],
            bd=0,
        )

        editor_area = tk.Frame(editor_frame, bg=C["editor"])
        editor_area.pack(fill="both", expand=True)

        editor_font = ("Consolas", 11)

        self.line_numbers = tk.Text(
            editor_area,
            width=5,
            bg=C["gutter"],
            fg=C["muted"],
            font=editor_font,
            padx=8,
            pady=10,
            spacing1=0,
            spacing2=0,
            spacing3=0,
            relief="flat",
            bd=0,
            state="disabled",
            takefocus=0,
            wrap="none",
            cursor="arrow",
            highlightthickness=0,
            selectbackground=C["gutter"],
        )
        self.line_numbers.pack(side="left", fill="y")

        self.editor = tk.Text(
            editor_area,
            bg=C["editor"],
            fg=C["text"],
            insertbackground=C["blue"],
            selectbackground=C["selection"],
            selectforeground="#FFFFFF",
            font=editor_font,
            wrap="none",
            undo=True,
            maxundo=-1,
            padx=12,
            pady=10,
            spacing1=0,
            spacing2=0,
            spacing3=0,
            relief="flat",
            bd=0,
            tabs=("4c",),
            autoseparators=True,
            highlightthickness=0,
        )
        self.editor.pack(side="left", fill="both", expand=True)

        self.editor_vscroll = ttk.Scrollbar(
            editor_area,
            orient="vertical",
            style="Dark.Vertical.TScrollbar",
            command=self._scroll_editor,
        )
        self.editor_vscroll.pack(side="right", fill="y")

        self.editor.configure(yscrollcommand=self._editor_scroll_changed)

        editor_hscroll = ttk.Scrollbar(
            editor_frame,
            orient="horizontal",
            style="Dark.Horizontal.TScrollbar",
            command=self.editor.xview,
        )
        editor_hscroll.pack(side="bottom", fill="x")
        self.editor.configure(xscrollcommand=editor_hscroll.set)

        output_frame = tk.Frame(
            self.paned,
            bg=C["output"],
            highlightthickness=1,
            highlightbackground=C["border"],
            bd=0,
        )

        output_header = tk.Frame(
            output_frame,
            bg=C["toolbar"],
            height=36,
        )
        output_header.pack(fill="x")
        output_header.pack_propagate(False)

        tk.Label(
            output_header,
            text="  OUTPUT",
            bg=C["toolbar"],
            fg=C["blue"],
            font=("Segoe UI", 9, "bold"),
        ).pack(side="left", padx=4)

        tk.Button(
            output_header,
            text="Clear output",
            command=self.clear_output,
            bg=C["toolbar"],
            fg=C["muted"],
            activebackground=C["selection"],
            activeforeground=C["text"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=("Segoe UI", 9),
            cursor="hand2",
        ).pack(side="right", padx=10)

        output_body = tk.Frame(output_frame, bg=C["output"])
        output_body.pack(fill="both", expand=True)

        output_scroll = ttk.Scrollbar(
            output_body,
            orient="vertical",
            style="Dark.Vertical.TScrollbar",
        )
        output_scroll.pack(side="right", fill="y")

        self.output = tk.Text(
            output_body,
            bg=C["output"],
            fg=C["text"],
            insertbackground=C["text"],
            selectbackground=C["selection"],
            font=("Consolas", 10),
            wrap="word",
            state="disabled",
            padx=12,
            pady=10,
            relief="flat",
            bd=0,
            highlightthickness=0,
            yscrollcommand=output_scroll.set,
        )
        self.output.pack(fill="both", expand=True)
        output_scroll.configure(command=self.output.yview)

        self.output.tag_configure("error", foreground=C["error"])
        self.output.tag_configure("success", foreground=C["blue"])

        self.paned.add(editor_frame, weight=4)
        self.paned.add(output_frame, weight=1)

        self.status_bar = tk.Label(
            self.root,
            text="Ready",
            anchor="w",
            bg=C["blue"],
            fg="#07101E",
            font=("Segoe UI", 9),
            padx=10,
            pady=4,
        )
        self.status_bar.pack(fill="x", side="bottom")

        self.editor.bind("<KeyRelease>", self._on_editor_change)
        self.editor.bind("<<Modified>>", self._on_editor_modified)
        self.editor.bind("<Button-1>", self._on_editor_click, add="+")
        self.editor.bind("<Configure>", self._on_editor_change)
        self.editor.bind("<Tab>", self._insert_indentation)

    def _configure_tags(self):
        for tag, color in {
            "marker_python": "#65E6AD",
            "marker_cpp": "#67C7FF",
            "marker_javascript": "#F4D36B",
            "keyword": C["purple"],
            "string": C["string"],
            "number": C["number"],
            "comment": C["comment"],
            "function": C["function"],
        }.items():
            self.editor.tag_configure(tag, foreground=color)

        self.editor.tag_raise("sel")

    def _bind_shortcuts(self):
        self.root.bind("<Control-Return>", self._run_shortcut)
        self.root.bind("<F5>", self._run_shortcut)
        self.root.bind("<Control-l>", self._clear_output_shortcut)

    def _set_initial_split(self):
        height = self.paned.winfo_height()
        if height > 100:
            self.paned.sashpos(0, int(height * 0.72))

    def _set_status(self, message):
        self.status_label.configure(text=message)
        self.status_bar.configure(text=message)

    def _on_editor_change(self, event=None):
        self._update_line_numbers()
        self._schedule_highlighting()

    def _on_editor_click(self, event=None):
        self._update_line_numbers()

    def _on_editor_modified(self, event=None):
        if self.editor.edit_modified():
            self.editor.edit_modified(False)
            self._update_line_numbers()
            self._schedule_highlighting()

    def _update_line_numbers(self):
        if self._gutter_syncing:
            return

        self._gutter_syncing = True
        try:
            last_line = int(self.editor.index("end-1c").split(".")[0])
            numbers = "\n".join(str(n) for n in range(1, last_line + 1))

            self.line_numbers.configure(state="normal")
            self.line_numbers.delete("1.0", "end")
            self.line_numbers.insert("1.0", numbers)
            self.line_numbers.configure(state="disabled")

            self.line_numbers.yview_moveto(self.editor.yview()[0])
        finally:
            self._gutter_syncing = False

    def _editor_scroll_changed(self, first, last):
        self.editor_vscroll.set(first, last)
        if not self._gutter_syncing:
            self._gutter_syncing = True
            try:
                self.line_numbers.yview_moveto(float(first))
            finally:
                self._gutter_syncing = False

    def _scroll_editor(self, *args):
        self.editor.yview(*args)
        self.line_numbers.yview_moveto(self.editor.yview()[0])

    def _insert_indentation(self, event=None):
        self.editor.insert("insert", "    ")
        self._update_line_numbers()
        self._schedule_highlighting()
        return "break"

    def _schedule_highlighting(self):
        if self.highlight_job is not None:
            try:
                self.root.after_cancel(self.highlight_job)
            except tk.TclError:
                pass

        self.highlight_job = self.root.after(100, self._highlight_syntax)

    def _highlight_syntax(self):
        self.highlight_job = None
        source = self.editor.get("1.0", "end-1c")

        tags = (
            "marker_python",
            "marker_cpp",
            "marker_javascript",
            "keyword",
            "string",
            "number",
            "comment",
            "function",
        )
        for tag in tags:
            self.editor.tag_remove(tag, "1.0", "end")

        markers = {
            "@python": "marker_python",
            "@cpp": "marker_cpp",
            "@javascript": "marker_javascript",
        }

        keyword_pattern = re.compile(
            r"\b(?:if|else|elif|for|while|in|return|break|continue|"
            r"def|class|import|from|as|pass|try|except|finally|with|"
            r"lambda|and|or|not|is|None|True|False|"
            r"int|float|double|long|short|char|bool|void|string|auto|"
            r"const|static|public|private|protected|new|delete|"
            r"using|namespace|let|var|function|async|await|throw|this|"
            r"extends|null|undefined|true|false|std|cout|cin|endl|main)\b"
        )
        string_pattern = re.compile(
            r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|`(?:\\.|[^`\\])*`'
        )
        comment_pattern = re.compile(r"//.*|#.*|/\*.*?\*/")
        number_pattern = re.compile(r"\b\d+(?:\.\d+)?\b")
        function_pattern = re.compile(r"\b[A-Za-z_]\w*(?=\s*\()")

        for line_no, line in enumerate(source.splitlines(), 1):
            marker = line.strip()
            if marker in markers:
                start_col = len(line) - len(line.lstrip())
                self.editor.tag_add(
                    markers[marker],
                    f"{line_no}.{start_col}",
                    f"{line_no}.{len(line)}",
                )
                continue

            string_spans = []
            for match in string_pattern.finditer(line):
                string_spans.append(match.span())
                self.editor.tag_add(
                    "string",
                    f"{line_no}.{match.start()}",
                    f"{line_no}.{match.end()}",
                )

            comment_match = comment_pattern.search(line)
            comment_start = comment_match.start() if comment_match else len(line)

            def overlaps_string(start, end):
                return any(start < b and end > a for a, b in string_spans)

            for match in keyword_pattern.finditer(line):
                if (
                    match.start() < comment_start
                    and not overlaps_string(*match.span())
                ):
                    self.editor.tag_add(
                        "keyword",
                        f"{line_no}.{match.start()}",
                        f"{line_no}.{match.end()}",
                    )

            for match in number_pattern.finditer(line):
                if (
                    match.start() < comment_start
                    and not overlaps_string(*match.span())
                ):
                    self.editor.tag_add(
                        "number",
                        f"{line_no}.{match.start()}",
                        f"{line_no}.{match.end()}",
                    )

            for match in function_pattern.finditer(line):
                if (
                    match.start() < comment_start
                    and not overlaps_string(*match.span())
                ):
                    self.editor.tag_add(
                        "function",
                        f"{line_no}.{match.start()}",
                        f"{line_no}.{match.end()}",
                    )

            if comment_match:
                self.editor.tag_add(
                    "comment",
                    f"{line_no}.{comment_match.start()}",
                    f"{line_no}.{len(line)}",
                )

        self.editor.tag_raise("sel")
        self._update_line_numbers()

    def _write_output(self, text, tag=None):
        self.output.configure(state="normal")
        if text:
            self.output.insert("end", text)
            if not text.endswith("\n"):
                self.output.insert("end", "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def run_code(self):
        if self.running:
            return

        code = self.editor.get("1.0", "end-1c")
        if not code.strip():
            self.clear_output()
            self._write_output("Write some code before running the program.")
            self._set_status("Editor is empty")
            return

        self.running = True
        self.run_button.configure(state="disabled", text="Running...")
        self._set_status("Executing program...")
        self.clear_output()
        self._write_output("Running PolyCode program...\n")

        threading.Thread(
            target=self._execute_in_background,
            args=(code,),
            daemon=True,
        ).start()

    def _execute_in_background(self, code):
        try:
            result = self.engine.run(code)
            self.result_queue.put(
                ("success", result or "Execution finished with no output.")
            )
        except Exception as error:
            self.result_queue.put(
                ("error", f"{type(error).__name__}: {error}")
            )

    def _poll_results(self):
        try:
            while True:
                result_type, result = self.result_queue.get_nowait()
                self.clear_output()

                if result_type == "error":
                    self._write_output(result, "error")
                    self._set_status("Execution failed")
                else:
                    self._write_output(result)
                    self._set_status("Execution finished")

                self.running = False
                self.run_button.configure(state="normal", text="▶  Run")
        except queue.Empty:
            pass

        if self.root.winfo_exists():
            self.root.after(100, self._poll_results)

    def clear_editor(self):
        if self.running:
            return
        self.editor.delete("1.0", "end")
        self.editor.edit_modified(False)
        self._update_line_numbers()
        self._schedule_highlighting()
        self.editor.focus_set()
        self._set_status("Editor cleared")

    def clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _run_shortcut(self, event=None):
        self.run_code()
        return "break"

    def _clear_output_shortcut(self, event=None):
        self.clear_output()
        return "break"

    def on_close(self):
        if self.highlight_job is not None:
            try:
                self.root.after_cancel(self.highlight_job)
            except tk.TclError:
                pass
        self.root.destroy()


def main():
    root = tk.Tk()
    app = PolyCodeApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
