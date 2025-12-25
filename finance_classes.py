"""
finance_classes.py
Логика приложения "Учет личных финансов":
- OOP: Transaction, Category, FinanceManager
- CSV: сохранение/загрузка
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional


class TransactionType(Enum):
    INCOME = "Доход"
    EXPENSE = "Расход"


@dataclass(frozen=True)
class Category:
    name: str
    type: TransactionType


@dataclass
class Transaction:
    amount: float
    category: Category
    date: str  # YYYY-MM-DD
    description: str = ""


class FinanceManager:
    """
    Хранит транзакции и категории, отвечает за сохранение/загрузку из CSV.
    """

    CSV_HEADERS = ["Amount", "Category", "Type", "Date", "Description"]

    def __init__(self, filename: str = "transactions.csv") -> None:
        self.filename = Path(filename)
        self.transactions: List[Transaction] = []
        self.categories: List[Category] = [
            Category("Зарплата", TransactionType.INCOME),
            Category("Инвестиции", TransactionType.INCOME),
            Category("Продукты", TransactionType.EXPENSE),
            Category("Транспорт", TransactionType.EXPENSE),
            Category("Развлечения", TransactionType.EXPENSE),
        ]
        self.load_from_file()

    def get_category_by_name(self, name: str) -> Optional[Category]:
        return next((c for c in self.categories if c.name == name), None)

    def add_transaction(self, transaction: Transaction) -> None:
        self.transactions.append(transaction)
        self.save_to_file()

    def delete_transaction(self, index: int) -> None:
        if 0 <= index < len(self.transactions):
            del self.transactions[index]
            self.save_to_file()

    def get_balance(self) -> float:
        income = sum(
            t.amount for t in self.transactions if t.category.type == TransactionType.INCOME
        )
        expenses = sum(
            t.amount for t in self.transactions if t.category.type == TransactionType.EXPENSE
        )
        return income - expenses

    def get_category_summary(self) -> Dict[str, float]:
        """
        Возвращает суммы по категориям:
        - для доходов: +amount
        - для расходов: -amount (чтобы визуально было понятно, что это минус)
        """
        summary: Dict[str, float] = {}
        for t in self.transactions:
            key = t.category.name
            summary.setdefault(key, 0.0)
            if t.category.type == TransactionType.INCOME:
                summary[key] += t.amount
            else:
                summary[key] -= t.amount
        return summary

    def save_to_file(self) -> None:
        # создаём файл рядом с проектом (если передан относительный путь)
        with self.filename.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(self.CSV_HEADERS)
            for t in self.transactions:
                writer.writerow(
                    [
                        f"{t.amount:.2f}",
                        t.category.name,
                        t.category.type.value,
                        t.date,
                        t.description,
                    ]
                )

    def load_from_file(self) -> None:
        self.transactions = []
        if not self.filename.exists():
            # Создадим пустой CSV с заголовками, чтобы файл сразу был в проекте
            self.save_to_file()
            return

        try:
            with self.filename.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    cat = self.get_category_by_name(row.get("Category", "").strip())
                    if not cat:
                        # если в файле категория неизвестная — пропускаем, чтобы не падать
                        continue
                    amount_str = (row.get("Amount") or "").replace(",", ".").strip()
                    if not amount_str:
                        continue
                    try:
                        amount = float(amount_str)
                    except ValueError:
                        continue

                    self.transactions.append(
                        Transaction(
                            amount=amount,
                            category=cat,
                            date=(row.get("Date") or "").strip(),
                            description=(row.get("Description") or "").strip(),
                        )
                    )
        except Exception:
            # Если файл повреждён — стартуем с пустого списка, но приложение не падает
            self.transactions = []
