#!/usr/bin/env python3
"""
expenses-tracker.py
Lab 3 - Personal Expenses Tracker

Behavior:
- balance.txt stores the user's current starting balance (single number).
- Expense files are named: expenses_YYYY-MM-DD.txt
  Each expense line format: ID|timestamp|item|amount
- Available balance = balance_from_file - sum(all recorded expenses)
- Adding money updates balance.txt
- Recording an expense writes to the day's file (does NOT change balance.txt)
"""

import os
import sys
import datetime

BALANCE_FILE = "balance.txt"
EXPENSE_PREFIX = "expenses_"
EXPENSE_GLOB = "expenses_*.txt"
ARCHIVE_DIR = "archives"  # used by shell script (consistent name)

# ---------- Helpers ----------
def read_balance():
    """Read starting/current balance from balance.txt. If missing, create one with 0.0."""
    if not os.path.exists(BALANCE_FILE):
        with open(BALANCE_FILE, "w") as f:
            f.write("0.0\n")
        return 0.0
    with open(BALANCE_FILE, "r") as f:
        contents = f.read().strip()
    try:
        return float(contents)
    except ValueError:
        print("Error: balance.txt does not contain a valid number. Resetting to 0.0")
        with open(BALANCE_FILE, "w") as f:
            f.write("0.0\n")
        return 0.0

def write_balance(new_balance):
    with open(BALANCE_FILE, "w") as f:
        f.write(f"{new_balance:.2f}\n")

def list_expense_files():
    return sorted([f for f in os.listdir() if f.startswith(EXPENSE_PREFIX) and f.endswith(".txt")])

def parse_expense_line(line):
    # ID|timestamp|item|amount
    parts = line.strip().split("|")
    if len(parts) != 4:
        return None
    try:
        return {
            "id": int(parts[0]),
            "timestamp": parts[1],
            "item": parts[2],
            "amount": float(parts[3])
        }
    except Exception:
        return None

def total_expenses():
    total = 0.0
    for fname in list_expense_files():
        with open(fname, "r") as f:
            for line in f:
                rec = parse_expense_line(line)
                if rec:
                    total += rec["amount"]
    return total

def format_currency(x):
    return f"{x:.2f}"

# ---------- Feature Implementations ----------
def show_balance_report():
    bal = read_balance()
    total = total_expenses()
    available = bal - total
    print("\n--- BALANCE REPORT ---")
    print(f"Balance (from {BALANCE_FILE}): {format_currency(bal)}")
    print(f"Total expenses (all files): {format_currency(total)}")
    print(f"Available balance: {format_currency(available)}")
    # Ask to add money
    ans = input("\nDo you want to add money to your balance? (y/n): ").strip().lower()
    if ans == 'y':
        while True:
            amt_str = input("Enter amount to add (positive number): ").strip()
            try:
                amt = float(amt_str)
                if amt <= 0:
                    print("Amount must be positive.")
                    continue
            except ValueError:
                print("Please enter a valid number.")
                continue
            new_bal = bal + amt
            write_balance(new_bal)
            print(f"Balance updated. New balance: {format_currency(new_bal)}")
            break

def add_new_expense():
    # show available at top
    bal = read_balance()
    total = total_expenses()
    available = bal - total
    print(f"\nAvailable balance: {format_currency(available)}")

    # date prompt
    while True:
        date_str = input("Enter date (YYYY-MM-DD) [press Enter for today]: ").strip()
        if date_str == "":
            date_obj = datetime.date.today()
            date_str = date_obj.isoformat()
            break
        try:
            date_obj = datetime.date.fromisoformat(date_str)
            date_str = date_obj.isoformat()
            break
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD.")

    # item name
    item = input("Enter item name: ").strip()
    while not item:
        print("Item name cannot be empty.")
        item = input("Enter item name: ").strip()

    # amount
    while True:
        amt_str = input("Enter amount paid: ").strip()
        try:
            amt = float(amt_str)
            if amt <= 0:
                print("Amount must be positive.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")

    # confirmation
    print("\nPlease confirm the entry:")
    print(f"Date: {date_str}")
    print(f"Item: {item}")
    print(f"Amount: {format_currency(amt)}")
    conf = input("Save this expense? (y/n): ").strip().lower()
    if conf != 'y':
        print("Expense not saved.")
        return

    # check amount <= available
    if amt > available + 1e-9:
        print("Insufficient balance! Cannot save expense.")
        return

    fname = f"{EXPENSE_PREFIX}{date_str}.txt"
    # generate ID = next integer based on existing lines
    next_id = 1
    if os.path.exists(fname):
        with open(fname, "r") as f:
            lines = [l for l in f if l.strip()]
            if lines:
                last = parse_expense_line(lines[-1])
                if last:
                    next_id = last["id"] + 1

    timestamp = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
    line = f"{next_id}|{timestamp}|{item}|{amt:.2f}\n"
    with open(fname, "a") as f:
        f.write(line)

    print(f"Expense saved to {fname}. Remaining available balance: {format_currency(available - amt)}")
    # Note: design choice — we keep balance.txt as the starting/current balance and
    # compute available as balance - sum(expenses). We do NOT modify balance.txt here
    # to preserve an auditable ledger (initial balance + deposits - expenses = available).

def search_expenses_by_item():
    q = input("Enter item name or substring to search (case-insensitive): ").strip().lower()
    if not q:
        print("Empty search.")
        return
    matches = []
    for fname in list_expense_files():
        with open(fname, "r") as f:
            for line in f:
                rec = parse_expense_line(line)
                if rec and q in rec["item"].lower():
                    rec["file"] = fname
                    matches.append(rec)
    if not matches:
        print("No results found.")
        return
    print(f"\nFound {len(matches)} result(s):")
    for r in matches:
        print(f"{r['file']} | ID {r['id']} | {r['timestamp']} | {r['item']} | {format_currency(r['amount'])}")

def search_expenses_by_amount():
    while True:
        q = input("Enter amount to search (exact match) or range (min-max): ").strip()
        if not q:
            print("Empty input.")
            return
        # check range
        if '-' in q:
            parts = q.split('-', 1)
            try:
                lo = float(parts[0])
                hi = float(parts[1])
            except ValueError:
                print("Invalid range. Use min-max, e.g., 5-20")
                continue
            matches = []
            for fname in list_expense_files():
                with open(fname, "r") as f:
                    for line in f:
                        rec = parse_expense_line(line)
                        if rec and lo <= rec["amount"] <= hi:
                            rec["file"] = fname
                            matches.append(rec)
            break
        else:
            try:
                target = float(q)
            except ValueError:
                print("Enter a valid number or range.")
                continue
            matches = []
            for fname in list_expense_files():
                with open(fname, "r") as f:
                    for line in f:
                        rec = parse_expense_line(line)
                        if rec and abs(rec["amount"] - target) < 1e-9:
                            rec["file"] = fname
                            matches.append(rec)
            break

    if not matches:
        print("No results found.")
        return
    print(f"\nFound {len(matches)} result(s):")
    for r in matches:
        print(f"{r['file']} | ID {r['id']} | {r['timestamp']} | {r['item']} | {format_currency(r['amount'])}")

def view_expenses_menu():
    while True:
        print("\n--- VIEW EXPENSES ---")
        print("1. Search by item name")
        print("2. Search by amount")
        print("3. Back to main menu")
        choice = input("Choose an option: ").strip()
        if choice == "1":
            search_expenses_by_item()
        elif choice == "2":
            search_expenses_by_amount()
        elif choice == "3":
            return
        else:
            print("Invalid option. Choose 1, 2 or 3.")

# ---------- Main menu ----------
def main_menu():
    print("Welcome to Personal Expenses Tracker\n")
    while True:
        print("\n--- MAIN MENU ---")
        print("1. Check Remaining Balance")
        print("2. View Expenses")
        print("3. Add New Expense")
        print("4. Exit")
        choice = input("Choose an option (1-4): ").strip()
        if choice == "1":
            show_balance_report()
        elif choice == "2":
            view_expenses_menu()
        elif choice == "3":
            add_new_expense()
        elif choice == "4":
            print("Exiting. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid input. Choose 1-4.")

if _name_ == "_main_":
    main_menu()