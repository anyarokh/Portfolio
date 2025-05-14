import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox  # підключення для використання комбобоксів та повідомлень
import matplotlib.pyplot as plt
import os  # для роботи з файловою системою


def process_database(selected_db):
    original_db = f"{selected_db}.db"  # ім'я оригінальної бази даних
    stat_db = f"stat_{selected_db}.db"  # ім'я бази даних для статистики

    # перевірка, чи існує база даних статистики, і видалення її при необхідності
    if os.path.exists(stat_db):
        os.remove(stat_db)

    # з'єднання з початковою та статистичною базами даних
    conn_sample = sqlite3.connect(original_db)
    cursor_sample = conn_sample.cursor()
    conn_stat = sqlite3.connect(stat_db)
    cursor_stat = conn_stat.cursor()

    # отримання списку частин мови з бази даних
    cursor_sample.execute("SELECT DISTINCT частина_мови FROM част_мови")
    parts_of_speech = [row[0] for row in cursor_sample.fetchall()]

    # створення таблиць для кожної частини мови у статистичній базі даних
    for pos in parts_of_speech:
        cursor_stat.execute(f'''CREATE TABLE IF NOT EXISTS "{pos}" (xi INTEGER)''')
        cursor_sample.execute(f"SELECT * FROM част_мови WHERE частина_мови = ?", (pos,))
        for row in cursor_sample.fetchall():
            for val in row[2:]:
                cursor_stat.execute(f'INSERT INTO "{pos}" (xi) VALUES (?)', (val,))
    conn_stat.commit()

    # створення нових таблиць для унікальних значень xi
    cursor_stat.execute("SELECT name FROM sqlite_master WHERE type='table'")
    table_names = [row[0] for row in cursor_stat.fetchall()]

    for table in table_names:
        new_table = f"unique_{table}_values"
        cursor_stat.execute(f'''CREATE TABLE IF NOT EXISTS "{new_table}" (xi INTEGER, ni INTEGER)''')
        cursor_stat.execute(f"SELECT DISTINCT xi FROM \"{table}\" ORDER BY xi ASC")
        for (xi,) in cursor_stat.fetchall():
            cursor_stat.execute(f"SELECT COUNT(*) FROM \"{table}\" WHERE xi = ?", (xi,))
            ni = cursor_stat.fetchone()[0]
            cursor_stat.execute(f'INSERT INTO "{new_table}" (xi, ni) VALUES (?, ?)', (xi, ni))
        conn_stat.commit()

        # обчислення середнього та дисперсії для кожного значення xi
        cursor_stat.execute(f"SELECT xi, ni FROM \"{new_table}\" WHERE xi IS NOT NULL")
        data = cursor_stat.fetchall()
        total_ni = sum([ni for xi, ni in data])
        total_xini = sum([xi * ni for xi, ni in data])
        average = total_xini / total_ni if total_ni else 0

        # додавання стовпців
        try:
            cursor_stat.execute(f"ALTER TABLE \"{new_table}\" ADD COLUMN xini INTEGER")
            cursor_stat.execute(f"ALTER TABLE \"{new_table}\" ADD COLUMN dispersion REAL")
        except sqlite3.OperationalError:
            pass

        # оновлення значень
        for xi, ni in data:
            xini = int(xi * ni)
            disp = ((xi - average) ** 2) * ni
            cursor_stat.execute(f'''UPDATE "{new_table}" SET xini = ?, dispersion = ? WHERE xi = ?''',
                                (xini, round(disp, 2), xi))

        # додавання загальної статистики для таблиці
        cursor_stat.execute(f'''INSERT INTO "{new_table}" VALUES (?, ?, ?, ?)''',
                            (None, total_ni, total_xini, None))
        cursor_stat.execute(f'''SELECT SUM(dispersion) FROM "{new_table}"''')
        total_d = cursor_stat.fetchone()[0]
        cursor_stat.execute(f'''UPDATE "{new_table}" SET dispersion = ? WHERE xi IS NULL''', (total_d,))

        # створення таблиці інтервалів для кожної таблиці
        def build_interval_table(table_name, intervals):
            interval_table_name = f"{table_name}_intervals"
            cursor_stat.execute(
                f"CREATE TABLE IF NOT EXISTS {interval_table_name} (interval TEXT, ni INTEGER, midpoint REAL, "
                f"xini REAL)"
            )

            sum_ni = 0
            sum_xini = 0

            for i in range(len(intervals) - 1):
                interval_start = round(intervals[i], 1)
                interval_end = round(intervals[i + 1], 1)

                cursor_stat.execute(
                    f"SELECT SUM(ni) FROM {table_name} WHERE xi >= ? AND xi <= ?",
                    (interval_start, interval_end)
                )
                row = cursor_stat.fetchone()
                ni = row[0] if row[0] is not None else 0
                sum_ni += ni

                midpoint = round(interval_start + (interval_end - interval_start) / 2, 1)
                xini = round(ni * midpoint, 1)
                sum_xini += xini

                interval_label = f"{interval_start}–{interval_end}"

                cursor_stat.execute(
                    f"INSERT INTO {interval_table_name} VALUES (?, ?, ?, ?)",
                    (interval_label, ni, midpoint, xini)
                )

            cursor_stat.execute(
                f"INSERT INTO {interval_table_name} VALUES (?, ?, ?, ?)",
                (None, sum_ni, None, round(sum_xini, 1))
            )

        # побудова таблиці інтервалів
        cursor_stat.execute(f"SELECT MIN(xi), MAX(xi) FROM \"{new_table}\" WHERE xi IS NOT NULL")
        min_xi, max_xi = cursor_stat.fetchone()
        if min_xi is not None and max_xi is not None and min_xi < max_xi:
            step = round((max_xi - min_xi) / 5, 1)
            intervals = [round(min_xi + i * step, 1) for i in range(6)]
            build_interval_table(new_table, intervals)

    conn_stat.commit()
    conn_sample.close()
    conn_stat.close()


def plot_variational_polygon(selected_db):  # функція для побудови варіаційного полігону
    stat_db = f"stat_{selected_db}.db"
    conn = sqlite3.connect(stat_db)
    cursor = conn.cursor()

    # вибір усіх таблиць, що містять унікальні значення xi
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'unique_%_values'")
    tables = [row[0] for row in cursor.fetchall()]

    # побудова полігону для кожної таблиці
    for table in tables:
        cursor.execute(f"SELECT xi, ni FROM \"{table}\" WHERE xi IS NOT NULL ORDER BY xi")
        data = cursor.fetchall()
        xi = [row[0] for row in data]
        ni = [row[1] for row in data]
        plt.plot(xi, ni, marker='o')
        plt.title(f"Полігон частот (варіаційний ряд): {table}")
        plt.xlabel("xi")
        plt.ylabel("ni")
        plt.grid(True)
        plt.show()

    conn.close()


def on_process(selected_db_var=None):  # функція для запуску обробки даних
    selected_db = selected_db_var.get()
    if selected_db:  # перевірка, чи вибрана база даних
        process_database(selected_db)  # виклик функції обробки бази
        messagebox.showinfo("Успіх", f"Обробку бази '{selected_db}' завершено.")
    else:
        messagebox.showwarning("Помилка", "Оберіть базу даних перед обробкою.")


def plot_interval_polygon(selected_db):
    stat_db_path = f"stat_{selected_db}.db"  # створення шляху до бази даних
    conn_stat = sqlite3.connect(stat_db_path)
    cursor = conn_stat.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    for table in tables:
        table_name = table[0]
        # перевірка на відповідність шаблону для таблиць інтервалів
        if table_name.endswith("_intervals"):
            cursor.execute(f"SELECT midpoint, ni FROM \"{table_name}\"")
            data = cursor.fetchall()

            if not data:
                continue

            midpoints, frequencies = zip(*data)

            # створення графіку
            plt.figure(figsize=(10, 6))
            plt.plot(midpoints, frequencies, marker='o', linestyle='-')
            plt.title(f'Полігон частот для {table_name}')
            plt.xlabel('Середина інтервалу')
            plt.ylabel('ni')
            plt.grid(True)
            plt.show()

    conn_stat.close()


def get_tables_for_part_of_speech(part_of_speech):
    # словник для визначення таблиць на основі частини мови
    tables_dict = {
        "прикметник": ["unique_ADJF_values", "unique_ADJF_values_intervals", "ADJF"],
        "дієслово": ["unique_VERB_values", "unique_VERB_values_intervals", "VERB"],
        "іменник": ["unique_NOUN_values", "unique_NOUN_values_intervals", "NOUN"],
        "прислівник": ["unique_ADVB_values", "unique_ADVB_values_intervals", "ADVB"],
        "сполучник": ["unique_CONJ_values", "unique_CONJ_values_intervals", "CONJ"],
        "дієслівно-іменниковий": ["unique_GRND_values", "unique_GRND_values_intervals", "GRND"],
        "займенник": ["unique_NPRO_values", "unique_NPRO_values_intervals", "NPRO"],
        "числівник": ["unique_NUMR_values", "unique_NUMR_values_intervals", "NUMR"],
        "частка": ["unique_PRCL_values", "unique_PRCL_values_intervals", "PRCL"],
        "прийменник": ["unique_PREP_values", "unique_PREP_values_intervals", "PREP"],
    }
    return tables_dict.get(part_of_speech, [])


def fetch_table_data(selected_db, part_of_speech):
    # отримання даних з таблиць на основі вибору частини мови
    stat_db = f"stat_{selected_db}.db"
    conn = sqlite3.connect(stat_db)
    cursor = conn.cursor()

    tables = get_tables_for_part_of_speech(part_of_speech)
    conn.close()
    return tables


def display_table_data(table_name, selected_db, frame):
    # очищення попереднього вмісту фрейму
    for widget in frame.winfo_children():
        widget.destroy()

    stat_db = f"stat_{selected_db}.db"
    conn = sqlite3.connect(stat_db)
    cursor = conn.cursor()

    try:
        cursor.execute(f'SELECT * FROM "{table_name}"')
        data = cursor.fetchall()
    except sqlite3.Error as e:
        # обробка помилки
        tk.Label(frame, text=f"Помилка: {e}", bg="white", fg="red").pack()
        conn.close()
        return

    if data:
        # отримання заголовків колонок
        cols = [desc[0] for desc in cursor.description]
        table_frame = tk.Frame(frame, bg="white")
        table_frame.pack(fill="both", expand=True)

        # параметри стилю для елементів таблиці
        label_kwargs = {
            "width": 20,
            "anchor": "w",
            "borderwidth": 1,
            "relief": "solid",
            "bg": "white",
            "padx": 4,
            "pady": 2
        }

        # виведення заголовків таблиці
        for i, col in enumerate(cols):
            tk.Label(table_frame, text=col, font=("Arial", 9, "bold"), **label_kwargs).grid(row=0, column=i,
                                                                                            sticky="nsew")

        # виведення рядків таблиці
        for i, row in enumerate(data, start=1):
            for j, value in enumerate(row):
                tk.Label(table_frame, text=str(value), font=("Arial", 9), **label_kwargs).grid(row=i, column=j,
                                                                                               sticky="nsew")
    else:
        tk.Label(frame, text="Таблиця порожня", bg="white", fg="gray").pack()

    conn.close()


def start_interface():
    root = tk.Tk()
    root.title("Обробка бази частин мови")
    root.geometry("900x500")

    main_frame = tk.Frame(root)
    main_frame.pack(fill="both", expand=True)

    left_frame = tk.Frame(main_frame, width=200)
    left_frame.pack(side="left", fill="y", padx=10, pady=10)

    right_frame = tk.Frame(main_frame, bg="white")
    right_frame.pack(side="right", fill="both", expand=True)

    # уніфікована ширина для всіх елементів керування
    widget_width = 30

    db_list = ["sample_1", "sample_2"]
    selected_db_var = tk.StringVar()

    # створення меню вибору бази даних
    db_menu = ttk.Combobox(left_frame, values=db_list, textvariable=selected_db_var, width=widget_width)
    db_menu.pack(pady=10)

    process_button = tk.Button(left_frame, text="Обробити базу",
                               width=widget_width, command=lambda: on_process(selected_db_var))
    process_button.pack(pady=5)
    process_button.pack_forget()  # приховування кнопки після початкового завантаження

    def on_db_select(event):
        process_button.pack(pady=5)  # показати після вибору
        update_tables()

    db_menu.bind("<<ComboboxSelected>>", on_db_select)

    # створення меню вибору частини мови
    pos_var = tk.StringVar()
    pos_menu = ttk.Combobox(left_frame, textvariable=pos_var,
                            values=["іменник", "дієслово", "прикметник", "прислівник", "сполучник",
                                    "дієслівно-іменниковий", "займенник", "числівник", "частка", "прийменник"],
                            width=widget_width)
    pos_menu.pack(pady=10)
    pos_menu.bind("<<ComboboxSelected>>", lambda event: update_tables())

    table_var = tk.StringVar()
    table_menu = ttk.Combobox(left_frame, textvariable=table_var, width=widget_width)
    table_menu.pack(pady=10)

    # оновлення меню таблиць після вибору частини мови
    def update_tables():
        selected_db = selected_db_var.get()
        part_of_speech = pos_var.get()
        if selected_db and part_of_speech:
            tables = fetch_table_data(selected_db, part_of_speech)
            update_table_menu(tables)

    def update_table_menu(tables):
        table_menu['values'] = tables
        table_var.set(tables[0] if tables else "")

    def on_show_table():
        selected_db = selected_db_var.get()
        table = table_var.get()
        if table:
            display_table_data(table, selected_db, right_frame)
        else:
            messagebox.showwarning("Помилка", "Оберіть таблицю для перегляду.")

    show_button = tk.Button(left_frame, text="Показати таблицю", width=widget_width, command=on_show_table)
    show_button.pack(pady=5)

    # кнопка для побудови полігону частот
    polygon_button = tk.Button(left_frame, text="Полігон частот за\n варіаційним рядом",
                               width=widget_width,
                               command=lambda: plot_variational_polygon(selected_db_var.get()))
    polygon_button.pack(pady=5)

    # кнопка для побудови полігону частот за інтервальним варіаційним рядом
    interval_polygon_button = tk.Button(left_frame, text="Полігон частот за\n інтервальним варіаційним рядом",
                                        width=widget_width,
                                        command=lambda: plot_interval_polygon(selected_db_var.get()))
    interval_polygon_button.pack(pady=5)

    root.mainloop()


start_interface()
