"""
Student Management System
=========================
Libraries : tkinter (GUI), pandas (data handling / CSV storage),
            numpy (calculations), matplotlib (charts)

Features  : Add / Update / Delete / Search students
            Automatic Total, Percentage and Grade calculation
            Data saved permanently in students.csv
            Analytics dashboard with 4 charts + statistics
            Export report to CSV

Run       : python student_management_system.py
Install   : pip install pandas numpy matplotlib
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# --------------------------------------------------------------------------
# CONSTANTS
# --------------------------------------------------------------------------
DATA_FILE = "students.csv"
SUBJECTS = ["Math", "Science", "English", "Computer"]
BASE_COLUMNS = ["ID", "Name", "Age", "Gender", "Course"] + SUBJECTS
TABLE_COLUMNS = BASE_COLUMNS + ["Total", "Percentage", "Grade"]
COURSES = ["B.Tech", "BCA", "BBA", "B.Sc", "B.Com", "BA"]
PASS_PERCENTAGE = 40


# --------------------------------------------------------------------------
# DATA LAYER  (pandas + numpy)
# --------------------------------------------------------------------------
class StudentData:
    """Handles storage and calculations. No GUI code in here."""

    def __init__(self, filename=DATA_FILE):
        self.filename = filename
        self.df = self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                df = pd.read_csv(self.filename)
                for col in BASE_COLUMNS:
                    if col not in df.columns:
                        df[col] = ""
                return df[BASE_COLUMNS]
            except Exception:
                pass
        return pd.DataFrame(columns=BASE_COLUMNS)

    def save(self):
        self.df.to_csv(self.filename, index=False)

    def next_id(self):
        if self.df.empty:
            return 1
        return int(pd.to_numeric(self.df["ID"]).max()) + 1

    def computed(self, df=None):
        """Return a copy with Total, Percentage and Grade columns added."""
        df = (self.df if df is None else df).copy()
        marks = df[SUBJECTS].apply(pd.to_numeric, errors="coerce").fillna(0)
        df[SUBJECTS] = marks
        df["Total"] = marks.sum(axis=1)
        df["Percentage"] = np.round(df["Total"] / (100 * len(SUBJECTS)) * 100, 2)

        p = df["Percentage"]
        conditions = [p >= 90, p >= 80, p >= 70, p >= 60, p >= PASS_PERCENTAGE]
        grades = ["A+", "A", "B", "C", "D"]
        df["Grade"] = np.select(conditions, grades, default="F")
        return df

    def add(self, record):
        record["ID"] = self.next_id()
        self.df = pd.concat([self.df, pd.DataFrame([record])], ignore_index=True)
        self.save()
        return record["ID"]

    def update(self, student_id, record):
        mask = pd.to_numeric(self.df["ID"]) == int(student_id)
        if not mask.any():
            return False
        for key, value in record.items():
            self.df.loc[mask, key] = value
        self.save()
        return True

    def delete(self, student_id):
        mask = pd.to_numeric(self.df["ID"]) != int(student_id)
        self.df = self.df[mask].reset_index(drop=True)
        self.save()

    def search(self, text):
        data = self.computed()
        text = text.strip().lower()
        if not text:
            return data
        match = (
            data["Name"].astype(str).str.lower().str.contains(text)
            | data["Course"].astype(str).str.lower().str.contains(text)
            | data["ID"].astype(str).str.contains(text)
        )
        return data[match]

    def statistics(self):
        data = self.computed()
        if data.empty:
            return None
        pct = data["Percentage"].to_numpy()
        return {
            "Total Students": len(data),
            "Average %": round(float(np.mean(pct)), 2),
            "Median %": round(float(np.median(pct)), 2),
            "Std. Deviation": round(float(np.std(pct)), 2),
            "Highest %": round(float(np.max(pct)), 2),
            "Lowest %": round(float(np.min(pct)), 2),
            "Pass Rate %": round(float(np.mean(pct >= PASS_PERCENTAGE) * 100), 2),
            "Topper": data.loc[data["Percentage"].idxmax(), "Name"],
        }


# --------------------------------------------------------------------------
# GUI LAYER  (tkinter + matplotlib)
# --------------------------------------------------------------------------
class StudentApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Student Management System")
        self.geometry("1150x700")
        self.minsize(1000, 620)

        self.data = StudentData()
        self.selected_id = None
        self.vars = {}

        self._setup_style()
        self._build_header()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_students = ttk.Frame(self.notebook)
        self.tab_analytics = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_students, text="  Students  ")
        self.notebook.add(self.tab_analytics, text="  Analytics  ")

        self._build_students_tab()
        self._build_analytics_tab()
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        self.refresh_table()

    # ---------------------------- styling --------------------------------
    def _setup_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10), padding=5)

    def _build_header(self):
        header = tk.Frame(self, bg="#1f3a5f")
        header.pack(fill="x")
        tk.Label(
            header,
            text="🎓  Student Management System",
            font=("Segoe UI", 18, "bold"),
            fg="white",
            bg="#1f3a5f",
            pady=10,
        ).pack()

    # -------------------------- students tab -----------------------------
    def _build_students_tab(self):
        # ---- form ----
        form = ttk.LabelFrame(self.tab_students, text="Student Details", padding=10)
        form.pack(fill="x", padx=10, pady=10)

        for name in ["ID", "Name", "Age", "Gender", "Course"] + SUBJECTS:
            self.vars[name] = tk.StringVar()

        def add_field(label, widget_factory, row, col):
            ttk.Label(form, text=label).grid(row=row, column=col * 2, sticky="e", padx=5, pady=5)
            w = widget_factory()
            w.grid(row=row, column=col * 2 + 1, sticky="w", padx=5, pady=5)
            return w

        add_field("ID:", lambda: ttk.Entry(form, textvariable=self.vars["ID"], width=18, state="readonly"), 0, 0)
        add_field("Name:", lambda: ttk.Entry(form, textvariable=self.vars["Name"], width=22), 0, 1)
        add_field("Age:", lambda: ttk.Entry(form, textvariable=self.vars["Age"], width=18), 0, 2)
        add_field(
            "Gender:",
            lambda: ttk.Combobox(form, textvariable=self.vars["Gender"], width=16,
                                 values=["Male", "Female", "Other"], state="readonly"),
            1, 0,
        )
        add_field(
            "Course:",
            lambda: ttk.Combobox(form, textvariable=self.vars["Course"], width=20, values=COURSES),
            1, 1,
        )

        marks_frame = ttk.LabelFrame(form, text="Marks (out of 100)", padding=5)
        marks_frame.grid(row=2, column=0, columnspan=6, sticky="we", pady=8)
        for i, subject in enumerate(SUBJECTS):
            ttk.Label(marks_frame, text=f"{subject}:").grid(row=0, column=i * 2, padx=8, pady=4)
            ttk.Entry(marks_frame, textvariable=self.vars[subject], width=10).grid(
                row=0, column=i * 2 + 1, padx=4, pady=4
            )

        # ---- buttons ----
        btns = ttk.Frame(form)
        btns.grid(row=3, column=0, columnspan=6, pady=5)
        ttk.Button(btns, text="➕ Add", command=self.add_student).pack(side="left", padx=5)
        ttk.Button(btns, text="✏️ Update", command=self.update_student).pack(side="left", padx=5)
        ttk.Button(btns, text="🗑 Delete", command=self.delete_student).pack(side="left", padx=5)
        ttk.Button(btns, text="🧹 Clear", command=self.clear_form).pack(side="left", padx=5)
        ttk.Button(btns, text="📤 Export Report", command=self.export_report).pack(side="left", padx=5)

        # ---- search ----
        search_bar = ttk.Frame(self.tab_students)
        search_bar.pack(fill="x", padx=10)
        ttk.Label(search_bar, text="Search (ID / Name / Course):").pack(side="left")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_bar, textvariable=self.search_var, width=30)
        entry.pack(side="left", padx=6)
        entry.bind("<KeyRelease>", lambda e: self.refresh_table())
        ttk.Button(search_bar, text="Show All", command=self._show_all).pack(side="left")
        self.count_label = ttk.Label(search_bar, text="")
        self.count_label.pack(side="right")

        # ---- table ----
        table_frame = ttk.Frame(self.tab_students)
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.tree = ttk.Treeview(table_frame, columns=TABLE_COLUMNS, show="headings", selectmode="browse")
        widths = {"ID": 45, "Name": 150, "Age": 50, "Gender": 70, "Course": 80,
                  "Total": 60, "Percentage": 85, "Grade": 55}
        for col in TABLE_COLUMNS:
            self.tree.heading(col, text=col, command=lambda c=col: self._sort_by(c))
            self.tree.column(col, width=widths.get(col, 75), anchor="center")
        self.tree.column("Name", anchor="w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self._sort_state = {}

    # -------------------------- analytics tab ----------------------------
    def _build_analytics_tab(self):
        top = ttk.Frame(self.tab_analytics)
        top.pack(fill="x", padx=10, pady=8)
        ttk.Button(top, text="🔄 Refresh Charts", command=self.refresh_analytics).pack(side="left")

        self.stats_label = ttk.Label(top, text="", justify="left", font=("Segoe UI", 10))
        self.stats_label.pack(side="left", padx=20)

        self.figure = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.tab_analytics)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

    # ----------------------------- helpers -------------------------------
    def _on_tab_change(self, _event):
        if self.notebook.index(self.notebook.select()) == 1:
            self.refresh_analytics()

    def _show_all(self):
        self.search_var.set("")
        self.refresh_table()

    def _sort_by(self, column):
        rows = [(self.tree.set(k, column), k) for k in self.tree.get_children("")]
        reverse = self._sort_state.get(column, False)
        try:
            rows.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            rows.sort(key=lambda t: t[0].lower(), reverse=reverse)
        for index, (_, k) in enumerate(rows):
            self.tree.move(k, "", index)
        self._sort_state[column] = not reverse

    def _read_form(self):
        """Validate form input; return a dict or None."""
        name = self.vars["Name"].get().strip()
        if not name:
            messagebox.showwarning("Validation", "Name is required.")
            return None

        try:
            age = int(self.vars["Age"].get())
            if not 3 <= age <= 100:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Validation", "Age must be a whole number between 3 and 100.")
            return None

        if not self.vars["Gender"].get():
            messagebox.showwarning("Validation", "Please select a gender.")
            return None
        if not self.vars["Course"].get().strip():
            messagebox.showwarning("Validation", "Course is required.")
            return None

        record = {
            "Name": name,
            "Age": age,
            "Gender": self.vars["Gender"].get(),
            "Course": self.vars["Course"].get().strip(),
        }
        for subject in SUBJECTS:
            try:
                mark = float(self.vars[subject].get())
                if not 0 <= mark <= 100:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Validation", f"{subject} marks must be a number between 0 and 100.")
                return None
            record[subject] = mark
        return record

    # ------------------------------ actions ------------------------------
    def add_student(self):
        record = self._read_form()
        if record is None:
            return
        new_id = self.data.add(record)
        self.refresh_table()
        self.clear_form()
        messagebox.showinfo("Success", f"Student added with ID {new_id}.")

    def update_student(self):
        if self.selected_id is None:
            messagebox.showwarning("Update", "Select a student from the table first.")
            return
        record = self._read_form()
        if record is None:
            return
        if self.data.update(self.selected_id, record):
            self.refresh_table()
            self.clear_form()
            messagebox.showinfo("Success", "Student record updated.")

    def delete_student(self):
        if self.selected_id is None:
            messagebox.showwarning("Delete", "Select a student from the table first.")
            return
        if messagebox.askyesno("Confirm", f"Delete student ID {self.selected_id}?"):
            self.data.delete(self.selected_id)
            self.refresh_table()
            self.clear_form()

    def clear_form(self):
        for var in self.vars.values():
            var.set("")
        self.selected_id = None
        self.tree.selection_remove(self.tree.selection())

    def export_report(self):
        data = self.data.computed()
        if data.empty:
            messagebox.showinfo("Export", "No data to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="student_report.csv",
        )
        if path:
            data.sort_values("Percentage", ascending=False).to_csv(path, index=False)
            messagebox.showinfo("Export", f"Report saved to:\n{path}")

    def _on_select(self, _event):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        row = dict(zip(TABLE_COLUMNS, values))
        self.selected_id = int(row["ID"])
        for key in BASE_COLUMNS:
            self.vars[key].set(row[key])

    # ----------------------------- refreshing ----------------------------
    def refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        data = self.data.search(self.search_var.get() if hasattr(self, "search_var") else "")
        for _, row in data.iterrows():
            values = [row[c] for c in TABLE_COLUMNS]
            values[0] = int(values[0])
            self.tree.insert("", "end", values=values)
        if hasattr(self, "count_label"):
            self.count_label.config(text=f"Showing {len(data)} of {len(self.data.df)} students")

    def refresh_analytics(self):
        data = self.data.computed()
        stats = self.data.statistics()
        self.figure.clear()

        if stats is None:
            self.stats_label.config(text="No data yet. Add some students first.")
            self.canvas.draw()
            return

        self.stats_label.config(
            text=(
                f"Students: {stats['Total Students']}   |   Avg: {stats['Average %']}%   |   "
                f"Median: {stats['Median %']}%   |   Std Dev: {stats['Std. Deviation']}\n"
                f"Highest: {stats['Highest %']}%   |   Lowest: {stats['Lowest %']}%   |   "
                f"Pass Rate: {stats['Pass Rate %']}%   |   Topper: {stats['Topper']}"
            )
        )

        # 1) Grade distribution
        ax1 = self.figure.add_subplot(2, 2, 1)
        order = ["A+", "A", "B", "C", "D", "F"]
        counts = data["Grade"].value_counts().reindex(order, fill_value=0)
        ax1.bar(counts.index, counts.values, color="#3b82f6")
        ax1.set_title("Grade Distribution")
        ax1.set_ylabel("Students")

        # 2) Average marks per subject
        ax2 = self.figure.add_subplot(2, 2, 2)
        averages = [np.mean(data[s]) for s in SUBJECTS]
        bars = ax2.bar(SUBJECTS, averages, color="#10b981")
        ax2.set_ylim(0, 100)
        ax2.set_title("Average Marks per Subject")
        for bar, value in zip(bars, averages):
            ax2.text(bar.get_x() + bar.get_width() / 2, value + 1, f"{value:.1f}", ha="center", fontsize=8)

        # 3) Top 5 students
        ax3 = self.figure.add_subplot(2, 2, 3)
        top5 = data.nlargest(5, "Percentage").iloc[::-1]
        ax3.barh(top5["Name"], top5["Percentage"], color="#f59e0b")
        ax3.set_xlim(0, 100)
        ax3.set_title("Top 5 Students (%)")

        # 4) Percentage histogram (or course split when there is enough data)
        ax4 = self.figure.add_subplot(2, 2, 4)
        ax4.hist(data["Percentage"], bins=np.arange(0, 110, 10), color="#8b5cf6", edgecolor="white")
        ax4.axvline(PASS_PERCENTAGE, color="red", linestyle="--", label=f"Pass mark ({PASS_PERCENTAGE}%)")
        ax4.set_title("Percentage Distribution")
        ax4.set_xlabel("Percentage")
        ax4.set_ylabel("Students")
        ax4.legend(fontsize=8)

        self.figure.tight_layout()
        self.canvas.draw()


# --------------------------------------------------------------------------
if __name__ == "__main__":
    app = StudentApp()
    app.mainloop()