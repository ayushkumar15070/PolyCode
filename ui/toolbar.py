import tkinter as tk


class Toolbar(tk.Frame):

    def __init__(self, parent, run_command, clear_command):
        super().__init__(
            parent,
            bg="#181818",
            height=50
        )

        self.pack_propagate(False)

        self.title = tk.Label(
            self,
            text="POLYCODE",
            font=("Segoe UI", 14, "bold"),
            bg="#181818",
            fg="#ffffff"
        )

        self.title.pack(
            side="left",
            padx=15
        )

        self.clear_button = tk.Button(
            self,
            text="CLEAR",
            command=clear_command,
            font=("Segoe UI", 10, "bold"),
            bg="#2d2d2d",
            fg="#ffffff",
            activebackground="#3d3d3d",
            activeforeground="#ffffff",
            relief="flat",
            padx=15,
            pady=6,
            cursor="hand2"
        )

        self.clear_button.pack(
            side="right",
            padx=(5, 10)
        )

        self.run_button = tk.Button(
            self,
            text="▶ RUN",
            command=run_command,
            font=("Segoe UI", 10, "bold"),
            bg="#2d2d2d",
            fg="#ffffff",
            activebackground="#3d3d3d",
            activeforeground="#ffffff",
            relief="flat",
            padx=15,
            pady=6,
            cursor="hand2"
        )

        self.run_button.pack(
            side="right",
            padx=5
        )