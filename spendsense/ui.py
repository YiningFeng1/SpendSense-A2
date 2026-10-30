"""Beginner-friendly Tkinter interface for SpendSense."""

from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import webbrowser

from .loader import load_csv
from .pipeline import run_pipeline


BG = "#F4F2EA"
PANEL = "#FFFFFF"
GREEN = "#274C3A"
PALE_GREEN = "#DDE8D2"
ORANGE = "#D86A48"
TEXT = "#1E2A23"
MUTED = "#68736C"
BORDER = "#D8DED6"


class SpendSenseApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("SpendSense")
        self.geometry("1120x720")
        self.minsize(930, 620)
        self.configure(bg=BG)

        self.project_root = Path(__file__).resolve().parents[1]
        self.csv_path: Path | None = None
        self.output_path = self.project_root / "outputs"
        self.rules_path = self.project_root / "config" / "category_rules.json"
        self.last_result = None

        self.file_var = tk.StringVar(value="No CSV selected")
        self.output_var = tk.StringVar(value=str(self.output_path))
        self.status_var = tk.StringVar(value="Select a CSV file to begin.")
        self.rows_var = tk.StringVar(value="—")
        self.columns_var = tk.StringVar(value="—")
        self.result_var = tk.StringVar(value="Not analysed")

        self._configure_style()
        self._build()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Spend.Treeview",
            background=PANEL,
            fieldbackground=PANEL,
            foreground=TEXT,
            rowheight=30,
            borderwidth=0,
        )
        style.configure(
            "Spend.Treeview.Heading",
            background=PALE_GREEN,
            foreground=GREEN,
            padding=8,
            font=("Helvetica", 10, "bold"),
        )

    def _build(self) -> None:
        header = tk.Frame(self, bg=GREEN, height=100)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(
            header,
            text="SpendSense",
            bg=GREEN,
            fg="white",
            font=("Georgia", 28, "bold"),
        ).pack(anchor="w", padx=30, pady=(18, 0))
        tk.Label(
            header,
            text="A simple view of where your money goes",
            bg=GREEN,
            fg=PALE_GREEN,
            font=("Helvetica", 11),
        ).pack(anchor="w", padx=30, pady=(3, 0))

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=26, pady=22)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_controls(body)
        self._build_preview(body)

        status = tk.Label(
            self,
            textvariable=self.status_var,
            bg="#E6E9E3",
            fg=MUTED,
            anchor="w",
            padx=26,
            font=("Helvetica", 9),
        )
        status.pack(fill="x", side="bottom", ipady=8)

    def _build_controls(self, parent: tk.Widget) -> None:
        panel = tk.Frame(parent, bg=PANEL, width=285, highlightbackground=BORDER, highlightthickness=1)
        panel.grid(row=0, column=0, sticky="ns", padx=(0, 18))
        panel.grid_propagate(False)

        tk.Label(panel, text="SETUP", bg=PANEL, fg=MUTED, font=("Helvetica", 10, "bold")).pack(
            anchor="w", padx=20, pady=(22, 10)
        )
        self._control_label(panel, "1  Choose bank CSV")
        self._path_label(panel, self.file_var)
        self._button(panel, "Select CSV", self.choose_csv, GREEN).pack(fill="x", padx=20, pady=(10, 22))

        self._control_label(panel, "2  Choose output folder")
        self._path_label(panel, self.output_var)
        self._button(panel, "Change folder", self.choose_output, PALE_GREEN, GREEN).pack(
            fill="x", padx=20, pady=(10, 22)
        )

        self._control_label(panel, "3  Run analysis")
        self.run_button = self._button(panel, "Start analysis", self.analyse, ORANGE)
        self.run_button.pack(fill="x", padx=20, pady=(8, 14))
        self.run_button.configure(state="disabled")

        self.progress = ttk.Progressbar(panel, mode="indeterminate")
        self.progress.pack(fill="x", padx=20, pady=(0, 14))

        self.chart_button = self._button(panel, "View dashboard", self.view_dashboard, PALE_GREEN, GREEN)
        self.chart_button.pack(fill="x", padx=20, pady=(0, 8))
        self.chart_button.configure(state="disabled")

        self.folder_button = self._button(panel, "Open results folder", self.open_results, PALE_GREEN, GREEN)
        self.folder_button.pack(fill="x", padx=20, pady=(0, 14))
        self.folder_button.configure(state="disabled")

        tk.Label(
            panel,
            text="SpendSense cleans, categorises, summarises, charts, and exports your transactions.",
            bg=PANEL,
            fg=MUTED,
            wraplength=240,
            justify="left",
            font=("Helvetica", 9),
        ).pack(anchor="w", padx=20)

    def _build_preview(self, parent: tk.Widget) -> None:
        area = tk.Frame(parent, bg=BG)
        area.grid(row=0, column=1, sticky="nsew")
        area.grid_columnconfigure(0, weight=1)
        area.grid_rowconfigure(2, weight=1)

        tk.Label(area, text="Transaction preview", bg=BG, fg=TEXT, font=("Georgia", 21, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 14)
        )

        cards = tk.Frame(area, bg=BG)
        cards.grid(row=1, column=0, sticky="ew", pady=(0, 14))
        for index in range(3):
            cards.grid_columnconfigure(index, weight=1)
        self._card(cards, 0, "ROWS", self.rows_var)
        self._card(cards, 1, "COLUMNS", self.columns_var)
        self._card(cards, 2, "RESULT", self.result_var)

        table_panel = tk.Frame(area, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        table_panel.grid(row=2, column=0, sticky="nsew")
        table_panel.grid_columnconfigure(0, weight=1)
        table_panel.grid_rowconfigure(0, weight=1)

        self.tree = ttk.Treeview(table_panel, show="headings", style="Spend.Treeview")
        y_scroll = ttk.Scrollbar(table_panel, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_panel, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")

    def _control_label(self, parent: tk.Widget, text: str) -> None:
        tk.Label(parent, text=text, bg=PANEL, fg=TEXT, font=("Helvetica", 11, "bold")).pack(
            anchor="w", padx=20, pady=(8, 7)
        )

    def _path_label(self, parent: tk.Widget, variable: tk.StringVar) -> None:
        tk.Label(
            parent,
            textvariable=variable,
            bg="#F1F4EF",
            fg=MUTED,
            padx=9,
            pady=7,
            anchor="w",
            wraplength=225,
            justify="left",
            font=("Helvetica", 9),
        ).pack(fill="x", padx=20)

    @staticmethod
    def _button(parent: tk.Widget, text: str, command, bg: str, fg: str = "white") -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            activebackground=bg,
            activeforeground=fg,
            disabledforeground="#A7ADA8",
            relief="flat",
            borderwidth=0,
            cursor="hand2",
            pady=9,
            font=("Helvetica", 10, "bold"),
        )

    def _card(self, parent: tk.Widget, column: int, title: str, value: tk.StringVar) -> None:
        card = tk.Frame(parent, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        card.grid(row=0, column=column, sticky="ew", padx=(0 if column == 0 else 6, 0 if column == 2 else 6))
        tk.Label(card, text=title, bg=PANEL, fg=MUTED, font=("Helvetica", 9, "bold")).pack(
            anchor="w", padx=14, pady=(11, 2)
        )
        tk.Label(card, textvariable=value, bg=PANEL, fg=GREEN, font=("Georgia", 17, "bold")).pack(
            anchor="w", padx=14, pady=(0, 11)
        )

    def choose_csv(self) -> None:
        selected = filedialog.askopenfilename(
            title="Choose a bank CSV",
            initialdir=str(self.project_root / "data" / "sample"),
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not selected:
            return
        try:
            loaded = load_csv(selected)
        except Exception as error:
            messagebox.showerror("Cannot read CSV", str(error), parent=self)
            return

        self.csv_path = Path(selected)
        self.last_result = None
        self.file_var.set(self.csv_path.name)
        self.rows_var.set(f"{len(loaded.frame):,}")
        self.columns_var.set(str(len(loaded.frame.columns)))
        self.result_var.set("Ready")
        self._show_frame(loaded.frame.head(100))
        self.run_button.configure(state="normal")
        self.chart_button.configure(state="disabled")
        self.folder_button.configure(state="disabled")
        self.status_var.set(f"Loaded {self.csv_path.name} using {loaded.encoding}.")

    def choose_output(self) -> None:
        selected = filedialog.askdirectory(title="Choose output folder", initialdir=str(self.output_path))
        if selected:
            self.output_path = Path(selected)
            self.output_var.set(str(self.output_path))

    def analyse(self) -> None:
        if self.csv_path is None:
            return
        self.run_button.configure(state="disabled")
        self.progress.start(12)
        self.status_var.set("Analysing transactions...")
        self.update_idletasks()
        try:
            result = run_pipeline(self.csv_path, self.rules_path, self.output_path)
        except Exception as error:
            self.result_var.set("Error")
            messagebox.showerror("Analysis failed", str(error), parent=self)
            self.status_var.set("Analysis failed. Check the CSV columns and values.")
        else:
            self.last_result = result
            metrics = result.metrics
            self.result_var.set(f"${metrics['expenses']:,.2f} spent")
            self._show_frame(result.transactions.head(100))
            self.chart_button.configure(state="normal")
            self.folder_button.configure(state="normal")
            self.status_var.set(
                f"Finished: {metrics['transactions']} transactions, "
                f"{metrics['uncategorised']} uncategorised."
            )
            messagebox.showinfo(
                "Analysis complete",
                f"Income: ${metrics['income']:,.2f}\n"
                f"Expenses: ${metrics['expenses']:,.2f}\n"
                f"Uncategorised: {metrics['uncategorised']}\n"
                f"Rejected rows: {result.rejected_rows}\n\n"
                f"Files saved to:\n{self.output_path}",
                parent=self,
            )
        finally:
            self.progress.stop()
            self.run_button.configure(state="normal")

    def view_dashboard(self) -> None:
        """Show the generated PNG dashboard in a new window."""

        if self.last_result is None:
            return
        chart_path = self.last_result.output_files.get("dashboard")
        if chart_path is None or not chart_path.exists():
            messagebox.showerror("Chart missing", "The dashboard file could not be found.", parent=self)
            return

        window = tk.Toplevel(self)
        window.title("SpendSense dashboard")
        window.configure(bg=BG)

        image = tk.PhotoImage(file=str(chart_path))
        # Matplotlib creates a large, sharp PNG. Halving it keeps the preview
        # comfortable on a laptop while the saved file retains full quality.
        if image.width() > 1200:
            image = image.subsample(2, 2)
        label = tk.Label(window, image=image, bg=BG, padx=12, pady=12)
        label.image = image
        label.pack(fill="both", expand=True)

    def open_results(self) -> None:
        """Open the output directory with the computer's file browser."""

        self.output_path.mkdir(parents=True, exist_ok=True)
        webbrowser.open(self.output_path.resolve().as_uri())

    def _show_frame(self, frame) -> None:
        self.tree.delete(*self.tree.get_children())
        columns = [f"c{index}" for index in range(len(frame.columns))]
        self.tree.configure(columns=columns)
        for column_id, heading in zip(columns, frame.columns):
            self.tree.heading(column_id, text=str(heading))
            self.tree.column(column_id, width=max(115, min(250, len(str(heading)) * 12)), stretch=True)
        for row in frame.itertuples(index=False, name=None):
            self.tree.insert("", "end", values=["" if value is None else value for value in row])
