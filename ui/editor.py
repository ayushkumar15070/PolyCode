import tkinter as tk


class CodeEditor(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent)

        self.configure(bg="#1e1e1e")

        # ==========================================
        # LINE NUMBERS
        # ==========================================

        self.line_numbers = tk.Text(
            self,
            width=4,
            padx=8,
            pady=15,
            font=("Consolas", 12),
            bg="#181818",
            fg="#858585",
            insertbackground="#181818",
            state="disabled",
            takefocus=0,
            borderwidth=0,
            highlightthickness=0
        )

        self.line_numbers.pack(
            side="left",
            fill="y"
        )

        # ==========================================
        # CODE EDITOR
        # ==========================================

        self.text_area = tk.Text(
            self,
            wrap="none",
            undo=True,
            font=("Consolas", 12),
            bg="#1e1e1e",
            fg="#d4d4d4",
            insertbackground="#ffffff",
            selectbackground="#264f78",
            padx=10,
            pady=15,
            borderwidth=0,
            highlightthickness=0
        )

        self.text_area.pack(
            side="left",
            fill="both",
            expand=True
        )

        # ==========================================
        # SYNTAX HIGHLIGHTING COLORS
        # ==========================================

        self.text_area.tag_configure(
            "python_marker",
            foreground="#3572A5",
            font=("Consolas", 12, "bold")
        )

        self.text_area.tag_configure(
            "cpp_marker",
            foreground="#F34B7D",
            font=("Consolas", 12, "bold")
        )

        self.text_area.tag_configure(
            "javascript_marker",
            foreground="#F7DF1E",
            font=("Consolas", 12, "bold")
        )

        # ==========================================
        # SCROLLBAR
        # ==========================================

        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self._scroll
        )

        self.scrollbar.pack(
            side="right",
            fill="y"
        )

        self.text_area.configure(
            yscrollcommand=self._sync_scrollbar
        )

        self.line_numbers.configure(
            yscrollcommand=self._sync_line_numbers
        )

        # ==========================================
        # EVENTS
        # ==========================================

        self.text_area.bind(
            "<KeyRelease>",
            self.on_editor_change
        )

        self.text_area.bind(
            "<MouseWheel>",
            self.on_editor_change
        )

        self.text_area.bind(
            "<Button-1>",
            self.on_editor_change
        )

        # Initial line numbers
        self.update_line_numbers()

    # ==============================================
    # SCROLLING
    # ==============================================

    def _scroll(self, *args):

        self.text_area.yview(*args)

        self.line_numbers.yview(*args)

    def _sync_scrollbar(self, *args):

        self.scrollbar.set(*args)

    def _sync_line_numbers(self, *args):

        self.line_numbers.yview_moveto(args[0])

    # ==============================================
    # EDITOR CHANGE
    # ==============================================

    def on_editor_change(self, event=None):

        self.update_line_numbers()

        self.highlight_languages()

    # ==============================================
    # LINE NUMBERS
    # ==============================================

    def update_line_numbers(self, event=None):

        self.line_numbers.config(
            state="normal"
        )

        self.line_numbers.delete(
            "1.0",
            tk.END
        )

        line_count = int(
            self.text_area.index(
                "end-1c"
            ).split(".")[0]
        )

        numbers = "\n".join(
            str(i)
            for i in range(
                1,
                line_count + 1
            )
        )

        self.line_numbers.insert(
            "1.0",
            numbers
        )

        self.line_numbers.config(
            state="disabled"
        )

    # ==============================================
    # LANGUAGE HIGHLIGHTING
    # ==============================================

    def highlight_languages(self):

        # Remove previous highlighting

        self.text_area.tag_remove(
            "python_marker",
            "1.0",
            tk.END
        )

        self.text_area.tag_remove(
            "cpp_marker",
            "1.0",
            tk.END
        )

        self.text_area.tag_remove(
            "javascript_marker",
            "1.0",
            tk.END
        )

        # Number of lines

        total_lines = int(
            self.text_area.index(
                "end-1c"
            ).split(".")[0]
        )

        # Check every line

        for line_number in range(
            1,
            total_lines + 1
        ):

            line_start = f"{line_number}.0"

            line_end = f"{line_number}.end"

            line = self.text_area.get(
                line_start,
                line_end
            ).strip()

            # Python

            if line == "@python":

                self.text_area.tag_add(
                    "python_marker",
                    line_start,
                    line_end
                )

            # C++

            elif line == "@cpp":

                self.text_area.tag_add(
                    "cpp_marker",
                    line_start,
                    line_end
                )

            # JavaScript

            elif line == "@javascript":

                self.text_area.tag_add(
                    "javascript_marker",
                    line_start,
                    line_end
                )

    # ==============================================
    # GET CODE
    # ==============================================

    def get_code(self):

        return self.text_area.get(
            "1.0",
            tk.END
        )

    # ==============================================
    # SET CODE
    # ==============================================

    def set_code(self, code):

        self.text_area.delete(
            "1.0",
            tk.END
        )

        self.text_area.insert(
            "1.0",
            code
        )

        self.update_line_numbers()

        self.highlight_languages()

    # ==============================================
    # CLEAR EDITOR
    # ==============================================

    def clear(self):

        self.text_area.delete(
            "1.0",
            tk.END
        )

        self.update_line_numbers()

        self.highlight_languages()