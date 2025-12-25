"""
finance_gui.py
GUI на Tkinter для приложения "Учет личных финансов"
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from finance_classes import Transaction, FinanceManager, TransactionType


class FinanceApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.manager = FinanceManager(filename="transactions.csv")

        self.root.title("Учет личных финансов")
        self.root.geometry("900x650")
        self.root.minsize(850, 600)

        self._setup_styles()
        self._build_ui()
        self.update_table()
        self.update_balance()

    def _setup_styles(self) -> None:
        style = ttk.Style()
        # Выбираем тему, если доступна
        if "clam" in style.theme_names():
            style.theme_use("clam")

    def _build_ui(self) -> None:
        # === ВВОД ===
        input_frame = ttk.LabelFrame(self.root, text="Добавить операцию", padding=12)
        input_frame.pack(fill=tk.X, padx=12, pady=8)

        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, sticky=tk.W)
        self.amount_entry = ttk.Entry(input_frame, width=25)
        self.amount_entry.grid(row=0, column=1, padx=6, pady=3, sticky=tk.W)

        ttk.Label(input_frame, text="Категория:").grid(row=1, column=0, sticky=tk.W)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(
            input_frame, textvariable=self.category_var, width=23, state="readonly"
        )
        self.category_combo["values"] = [c.name for c in self.manager.categories]
        self.category_combo.grid(row=1, column=1, padx=6, pady=3, sticky=tk.W)
        if self.category_combo["values"]:
            self.category_combo.current(0)

        ttk.Label(input_frame, text="Дата (ГГГГ-ММ-ДД):").grid(row=2, column=0, sticky=tk.W)
        self.date_entry = ttk.Entry(input_frame, width=25)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.date_entry.grid(row=2, column=1, padx=6, pady=3, sticky=tk.W)

        ttk.Label(input_frame, text="Описание:").grid(row=3, column=0, sticky=tk.W)
        self.desc_entry = ttk.Entry(input_frame, width=45)
        self.desc_entry.grid(row=3, column=1, padx=6, pady=3, sticky=tk.W)

        button_frame = ttk.Frame(input_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky=tk.W)

        ttk.Button(button_frame, text="Добавить операцию", command=self.add_transaction).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Удалить выбранную", command=self.delete_transaction).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(button_frame, text="Аналитика", command=self.show_analytics).pack(
            side=tk.LEFT, padx=5
        )

        # === ИНФО ===
        info_frame = ttk.LabelFrame(self.root, text="Финансовая информация", padding=12)
        info_frame.pack(fill=tk.X, padx=12, pady=8)

        self.balance_label = ttk.Label(info_frame, text="", font=("Arial", 12, "bold"))
        self.balance_label.pack(anchor=tk.W)

        # === ТАБЛИЦА ===
        table_frame = ttk.LabelFrame(self.root, text="История операций", padding=12)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        columns = ("date", "category", "type", "amount", "desc")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        self.tree.heading("date", text="Дата")
        self.tree.heading("category", text="Категория")
        self.tree.heading("type", text="Тип")
        self.tree.heading("amount", text="Сумма")
        self.tree.heading("desc", text="Описание")

        self.tree.column("date", width=110, anchor=tk.W)
        self.tree.column("category", width=150, anchor=tk.W)
        self.tree.column("type", width=90, anchor=tk.W)
        self.tree.column("amount", width=110, anchor=tk.E)
        self.tree.column("desc", width=350, anchor=tk.W)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # двойной клик — быстро удалить (опционально)
        self.tree.bind("<Double-1>", lambda _e: self.delete_transaction())

    def _validate_date(self, date_str: str) -> bool:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def add_transaction(self) -> None:
        amount_raw = self.amount_entry.get().strip().replace(",", ".")
        category_name = self.category_var.get().strip()
        date_str = self.date_entry.get().strip()
        description = self.desc_entry.get().strip()

        if not amount_raw or not category_name or not date_str:
            messagebox.showwarning("Ошибка", "Заполните обязательные поля: сумма, категория, дата.")
            return

        try:
            amount = float(amount_raw)
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную сумму (например 1200.50).")
            return

        if amount <= 0:
            messagebox.showwarning("Ошибка", "Сумма должна быть больше 0.")
            return

        if not self._validate_date(date_str):
            messagebox.showerror("Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД (например 2025-12-26).")
            return

        category = self.manager.get_category_by_name(category_name)
        if not category:
            messagebox.showwarning("Ошибка", "Выберите корректную категорию.")
            return

        tx = Transaction(amount=amount, category=category, date=date_str, description=description)
        self.manager.add_transaction(tx)

        self.update_table()
        self.update_balance()
        self.clear_inputs()

    def delete_transaction(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Удаление", "Выберите строку в таблице.")
            return

        idx = self.tree.index(selected[0])
        self.manager.delete_transaction(idx)
        self.update_table()
        self.update_balance()

    def show_analytics(self) -> None:
        summary = self.manager.get_category_summary()

        win = tk.Toplevel(self.root)
        win.title("Аналитика по категориям")
        win.geometry("360x420")
        win.resizable(False, False)

        ttk.Label(win, text="Суммы по категориям", font=("Arial", 12, "bold")).pack(
            padx=12, pady=(12, 8), anchor=tk.W
        )

        container = ttk.Frame(win)
        container.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # Сортируем: сначала по абсолютной величине (чтобы топ видно), потом по имени
        items = sorted(summary.items(), key=lambda x: (abs(x[1]), x[0]), reverse=True)

        if not items:
            ttk.Label(container, text="Пока нет операций.").pack(anchor=tk.W)
            return

        for cat, amt in items:
            sign = "+" if amt >= 0 else "-"
            ttk.Label(container, text=f"{cat}: {sign}{abs(amt):.2f}").pack(
                pady=3, anchor=tk.W
            )

    def update_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        for tx in self.manager.transactions:
            self.tree.insert(
                "",
                tk.END,
                values=(
                    tx.date,
                    tx.category.name,
                    tx.category.type.value,
                    f"{tx.amount:.2f}",
                    tx.description,
                ),
            )

    def update_balance(self) -> None:
        balance = self.manager.get_balance()
        # Цвет текста через ttk не всегда просто, поэтому просто выводим знак
        prefix = "+" if balance >= 0 else "-"
        self.balance_label.config(text=f"Текущий баланс: {prefix}{abs(balance):.2f} руб.")

    def clear_inputs(self) -> None:
        self.amount_entry.delete(0, tk.END)
        self.desc_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))


def main() -> None:
    root = tk.Tk()
    app = FinanceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
