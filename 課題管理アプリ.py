import customtkinter as ctk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
import sqlite3
from datetime import datetime

# =====================================
# アプリ設定
# =====================================

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

DB_NAME = "tasks.db"

# =====================================
# データベース管理
# =====================================

class DatabaseManager:

    def __init__(self):

        self.conn = sqlite3.connect(DB_NAME)
        self.cursor = self.conn.cursor()

        self.create_table()

    def create_table(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT,
            subject TEXT,
            deadline TEXT,
            priority TEXT,
            completed INTEGER

        )
        """)

        self.conn.commit()

    def add_task(self, task, subject, deadline, priority):

        self.cursor.execute("""
        INSERT INTO tasks (
            task,
            subject,
            deadline,
            priority,
            completed
        )
        VALUES (?, ?, ?, ?, 0)
        """, (task, subject, deadline, priority))

        self.conn.commit()

    def update_task(self, task_id, task, subject, deadline, priority):

        self.cursor.execute("""
        UPDATE tasks
        SET
            task=?,
            subject=?,
            deadline=?,
            priority=?
        WHERE id=?
        """, (task, subject, deadline, priority, task_id))

        self.conn.commit()

    def delete_task(self, task_id):

        self.cursor.execute("""
        DELETE FROM tasks
        WHERE id=?
        """, (task_id,))

        self.conn.commit()

    def toggle_complete(self, task_id):

        self.cursor.execute("""
        UPDATE tasks
        SET completed = CASE completed
            WHEN 0 THEN 1
            ELSE 0
        END
        WHERE id=?
        """, (task_id,))

        self.conn.commit()

    def fetch_tasks(self):

        self.cursor.execute("""
        SELECT *
        FROM tasks
        ORDER BY deadline ASC
        """)

        return self.cursor.fetchall()

# =====================================
# メインアプリ
# =====================================

class TaskManagerApp:

    def __init__(self, root):

        self.root = root
        self.root.title("📚 TaskBase")
        self.root.geometry("1450x850")

        self.db = DatabaseManager()

        self.selected_task_id = None
        self.sort_reverse = False

        # =====================================
        # タイトル
        # =====================================

        title = ctk.CTkLabel(
            root,
            text="📚 TaskBase",
            font=("Arial", 34, "bold")
        )

        title.pack(pady=15)

        self.progress_label = ctk.CTkLabel(
            root,
            text="完了率: 0%",
            font=("Arial", 18)
        )

        self.progress_label.pack()

        self.notification_label = ctk.CTkLabel(
            root,
            text="",
            font=("Arial", 18, "bold"),
            text_color="orange"
        )

        self.notification_label.pack(pady=10)

        # =====================================
        # 検索エリア
        # =====================================

        search_frame = ctk.CTkFrame(root)
        search_frame.pack(fill="x", padx=15, pady=10)

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="課題名・科目名で検索",
            height=40,
            font=("Arial", 18)
        )

        self.search_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=10,
            pady=10
        )

        self.priority_filter = ctk.CTkOptionMenu(
            search_frame,
            values=["すべて", "🔴 高", "🟡 中", "🟢 低"],
            width=140,
            height=40,
            font=("Arial", 16)
        )

        self.priority_filter.pack(side="left", padx=5)

        self.status_filter = ctk.CTkOptionMenu(
            search_frame,
            values=["すべて", "未完了", "完了"],
            width=140,
            height=40,
            font=("Arial", 16)
        )

        self.status_filter.pack(side="left", padx=5)

        ctk.CTkButton(
            search_frame,
            text="検索",
            command=self.search_tasks,
            width=120,
            height=40,
            font=("Arial", 16)
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            search_frame,
            text="全表示",
            command=self.load_tasks,
            width=120,
            height=40,
            font=("Arial", 16)
        ).pack(side="left", padx=5)

        # =====================================
        # 入力フォーム
        # =====================================

        form = ctk.CTkFrame(root)
        form.pack(fill="x", padx=15, pady=15)

        self.task_entry = ctk.CTkEntry(
            form,
            placeholder_text="課題名",
            width=250,
            height=50,
            font=("Arial", 18)
        )

        self.task_entry.grid(row=0, column=0, padx=10, pady=10)

        self.subject_entry = ctk.CTkEntry(
            form,
            placeholder_text="科目名",
            width=220,
            height=50,
            font=("Arial", 18)
        )

        self.subject_entry.grid(row=0, column=1, padx=10)

        # =====================================
        # 超巨大カレンダー
        # =====================================

        self.deadline_entry = DateEntry(
            form,
            date_pattern="yyyy-mm-dd",
            width=20,
            font=("Arial", 40),
            headersbackground="#1f538d",
            normalbackground="#2b2b2b",
            weekendbackground="#333333",
            foreground="white",
            weekendforeground="white",
            headersforeground="white",
            borderwidth=5
        )

        self.deadline_entry.grid(
            row=0,
            column=2,
            padx=15,
            pady=10
        )

        # カレンダー本体巨大化
        
        self.priority_menu = ctk.CTkOptionMenu(
            form,
            values=["🔴 高", "🟡 中", "🟢 低"],
            width=140,
            height=50,
            font=("Arial", 18)
        )

        self.priority_menu.grid(row=0, column=3, padx=10)

        ctk.CTkButton(
            form,
            text="追加",
            command=self.add_task,
            width=120,
            height=50,
            font=("Arial", 18)
        ).grid(row=0, column=4, padx=10)

        ctk.CTkButton(
            form,
            text="編集保存",
            command=self.edit_task,
            width=140,
            height=50,
            font=("Arial", 18)
        ).grid(row=0, column=5, padx=10)

        # =====================================
        # Treeviewスタイル
        # =====================================

        style = ttk.Style()

        style.theme_use("default")

        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            rowheight=70,
            borderwidth=0,
            font=("Arial", 22)
        )

        style.configure(
            "Treeview.Heading",
            font=("Arial", 16, "bold"),
            padding=10
        )

        style.map(
            "Treeview",
            background=[("selected", "#22559b")]
        )

        columns = (
            "状態",
            "課題",
            "科目",
            "締切",
            "優先度",
            "残り"
        )

        self.tree = ttk.Treeview(
            root,
            columns=columns,
            show="headings",
            height=18
        )

        for col in columns:

            self.tree.heading(
                col,
                text=col,
                command=lambda c=col: self.sort_tree(c)
            )

        self.tree.column("状態", width=90, anchor="center")
        self.tree.column("課題", width=320)
        self.tree.column("科目", width=220)
        self.tree.column("締切", width=150, anchor="center")
        self.tree.column("優先度", width=120, anchor="center")
        self.tree.column("残り", width=140, anchor="center")

        self.tree.pack(
            fill="both",
            expand=True,
            padx=15,
            pady=15
        )

        # 色タグ
        self.tree.tag_configure(
            "overdue",
            foreground="#ff5555"
        )

        self.tree.tag_configure(
            "urgent",
            foreground="#ffaa33"
        )

        self.tree.tag_configure(
            "completed",
            foreground="gray"
        )

        # イベント
        self.tree.bind(
            "<<TreeviewSelect>>",
            self.select_task
        )

        # ダブルクリックで完了切替
        self.tree.bind(
            "<Double-1>",
            lambda e: self.toggle_complete()
        )

        # =====================================
        # 下部ボタン
        # =====================================

        btn_frame = ctk.CTkFrame(root)
        btn_frame.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(
            btn_frame,
            text="✅ 完了切替",
            command=self.toggle_complete,
            width=160,
            height=50,
            font=("Arial", 18)
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="🗑 削除",
            command=self.delete_task,
            fg_color="#aa3333",
            hover_color="#cc4444",
            width=140,
            height=50,
            font=("Arial", 18)
        ).pack(side="left", padx=10)

        # 初期表示
        self.load_tasks()

    # =====================================
    # 残日数計算
    # =====================================

    def calculate_remaining(self, deadline):

        deadline_date = datetime.strptime(
            deadline,
            "%Y-%m-%d"
        )

        days = (
            deadline_date - datetime.now()
        ).days

        if days < 0:

            return f"{abs(days)}日超過", "overdue"

        elif days <= 3:

            return f"残り{days}日", "urgent"

        return f"残り{days}日", ""

    # =====================================
    # 課題追加
    # =====================================

    def add_task(self):

        task = self.task_entry.get()
        subject = self.subject_entry.get()
        deadline = self.deadline_entry.get()
        priority = self.priority_menu.get()

        if not task or not subject:

            messagebox.showerror(
                "入力エラー",
                "すべて入力してください"
            )

            return

        self.db.add_task(
            task,
            subject,
            deadline,
            priority
        )

        messagebox.showinfo(
            "追加完了",
            "課題を追加しました"
        )

        self.clear_inputs()
        self.load_tasks()

    # =====================================
    # 編集
    # =====================================

    def edit_task(self):

        if self.selected_task_id is None:

            messagebox.showwarning(
                "警告",
                "課題を選択してください"
            )

            return

        task = self.task_entry.get()
        subject = self.subject_entry.get()
        deadline = self.deadline_entry.get()
        priority = self.priority_menu.get()

        self.db.update_task(
            self.selected_task_id,
            task,
            subject,
            deadline,
            priority
        )

        messagebox.showinfo(
            "更新完了",
            "課題を更新しました"
        )

        self.clear_inputs()
        self.load_tasks()

    # =====================================
    # 表示
    # =====================================

    def load_tasks(self):

        for item in self.tree.get_children():

            self.tree.delete(item)

        tasks = self.db.fetch_tasks()

        completed_count = 0

        today_tasks = []

        for task in tasks:

            task_id, name, subject, deadline, priority, completed = task

            remain, tag = self.calculate_remaining(deadline)

            status = "✅" if completed else "⬜"

            if completed:

                tag = "completed"

                completed_count += 1

            if "残り0日" in remain:

                today_tasks.append(name)

            self.tree.insert(
                "",
                "end",
                iid=task_id,
                values=(
                    status,
                    name,
                    subject,
                    deadline,
                    priority,
                    remain
                ),
                tags=(tag,)
            )

        total = len(tasks)

        rate = int(
            completed_count / total * 100
        ) if total else 0

        self.progress_label.configure(
            text=f"完了率: {rate}%"
        )

        if today_tasks:

            self.notification_label.configure(
                text=f"⚠ 今日締切: {', '.join(today_tasks)}"
            )

        else:

            self.notification_label.configure(
                text=""
            )

    # =====================================
    # 選択
    # =====================================

    def select_task(self, event):

        selected = self.tree.selection()

        if not selected:
            return

        item_id = selected[0]

        self.selected_task_id = int(item_id)

        values = self.tree.item(
            item_id,
            "values"
        )

        self.task_entry.delete(0, "end")
        self.task_entry.insert(0, values[1])

        self.subject_entry.delete(0, "end")
        self.subject_entry.insert(0, values[2])

        self.deadline_entry.set_date(values[3])

        self.priority_menu.set(values[4])

    # =====================================
    # 削除
    # =====================================

    def delete_task(self):

        if self.selected_task_id is None:

            messagebox.showwarning(
                "警告",
                "課題を選択してください"
            )

            return

        result = messagebox.askyesno(
            "削除確認",
            "この課題を削除しますか？"
        )

        if result:

            self.db.delete_task(
                self.selected_task_id
            )

            messagebox.showinfo(
                "削除完了",
                "課題を削除しました"
            )

            self.selected_task_id = None

            self.load_tasks()

    # =====================================
    # 完了切替
    # =====================================

    def toggle_complete(self):

        if self.selected_task_id is None:

            messagebox.showwarning(
                "警告",
                "課題を選択してください"
            )

            return

        item = self.tree.item(
            self.selected_task_id
        )

        current_status = item["values"][0]

        if current_status == "⬜":

            result = messagebox.askyesno(
                "課題完了",
                "この課題を完了にしますか？"
            )

        else:

            result = messagebox.askyesno(
                "未完了へ戻す",
                "この課題を未完了へ戻しますか？"
            )

        if result:

            self.db.toggle_complete(
                self.selected_task_id
            )

            self.load_tasks()

            messagebox.showinfo(
                "更新完了",
                "課題状態を更新しました"
            )

    # =====================================
    # 検索
    # =====================================

    def search_tasks(self):

        keyword = self.search_entry.get().lower()

        priority_filter = self.priority_filter.get()

        status_filter = self.status_filter.get()

        for item in self.tree.get_children():

            self.tree.delete(item)

        tasks = self.db.fetch_tasks()

        for task in tasks:

            task_id, name, subject, deadline, priority, completed = task

            if (
                keyword not in name.lower()
                and
                keyword not in subject.lower()
            ):

                continue

            if priority_filter != "すべて":

                if priority != priority_filter:

                    continue

            if (
                status_filter == "完了"
                and
                completed == 0
            ):

                continue

            if (
                status_filter == "未完了"
                and
                completed == 1
            ):

                continue

            remain, tag = self.calculate_remaining(
                deadline
            )

            status = "✅" if completed else "⬜"

            if completed:

                tag = "completed"

            self.tree.insert(
                "",
                "end",
                iid=task_id,
                values=(
                    status,
                    name,
                    subject,
                    deadline,
                    priority,
                    remain
                ),
                tags=(tag,)
            )

    # =====================================
    # ソート
    # =====================================

    def sort_tree(self, col):

        data = []

        for child in self.tree.get_children():

            values = self.tree.item(child)["values"]

            data.append((values, child))

        col_index = {

            "状態": 0,
            "課題": 1,
            "科目": 2,
            "締切": 3,
            "優先度": 4,
            "残り": 5

        }[col]

        data.sort(
            key=lambda x: x[0][col_index],
            reverse=self.sort_reverse
        )

        for index, (_, child) in enumerate(data):

            self.tree.move(
                child,
                "",
                index
            )

        self.sort_reverse = not self.sort_reverse

    # =====================================
    # 入力クリア
    # =====================================

    def clear_inputs(self):

        self.task_entry.delete(0, "end")

        self.subject_entry.delete(0, "end")

        self.priority_menu.set("🔴 高")

        self.selected_task_id = None

# =====================================
# 起動
# =====================================

root = ctk.CTk()

app = TaskManagerApp(root)

root.mainloop()
