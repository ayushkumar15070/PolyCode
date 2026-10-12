import tkinter as tk


class OutputPanel(tk.Frame):

    def __init__(self, parent):
        super().__init__(parent)

        self.label = tk.Label(
            self,
            text="OUTPUT",
            anchor="w",
            font=("Segoe UI", 10, "bold"),
            bg="#181818",
            fg="#ffffff",
            padx=10,
            pady=6
        )

        self.label.pack(
            fill="x"
        )

        self.text_area = tk.Text(
            self,
            height=8,
            wrap="none",
            font=("Consolas", 11),
            bg="#181818",
            fg="#d4d4d4",
            insertbackground="#ffffff",
            padx=10,
            pady=10,
            borderwidth=0,
            state="disabled"
        )

        self.text_area.pack(
            fill="both",
            expand=True
        )

    def write(self, text):
        self.text_area.config(state="normal")

        self.text_area.delete(
            "1.0",
            tk.END
        )

        self.text_area.insert(
            tk.END,
            text
        )

        self.text_area.config(state="disabled")

    def clear(self):
        self.text_area.config(state="normal")

        self.text_area.delete(
            "1.0",
            tk.END
        )

        self.text_area.config(state="disabled")