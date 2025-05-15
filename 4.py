import tkinter as tk
from tkinter import filedialog, messagebox
import sqlite3
import math

# список частин мови, які можна обрати для аналізу
PARTS_OF_SPEECH = ["ADJF", "ADVB", "CONJ", "GRND", "NOUN", "NPRO", "NUMR", "PRCL", "PREP", "VERB"]


# функція для обчислення статистики (χ²) за двома базами даних і виводу результату
def calculate_statistics(db1_path, db2_path, result_label, pos_choice):
    pos = pos_choice.get()  # отримуємо вибрану частину мови
    table_name = pos.lower()  # ім'я таблиці для збереження даних - маленькими літерами

    try:
        conn1 = sqlite3.connect(db1_path)
        cursor1 = conn1.cursor()

        conn2 = sqlite3.connect(db2_path)
        cursor2 = conn2.cursor()

        conn_new = sqlite3.connect('new_database.db')
        cursor_new = conn_new.cursor()

        # створюємо таблицю з назвою частини мови, з колонками К1-К20 (числові)
        columns = ", ".join([f"К{i} INTEGER" for i in range(1, 21)])
        cursor_new.execute(f"""CREATE TABLE IF NOT EXISTS {table_name} (
            Вибірка TEXT, {columns})""")

        # витягуємо рядки для обраної частини мови з обох баз і записуємо у нову таблицю
        for i, (conn, cursor, label) in enumerate([(conn1, cursor1, 'М1'), (conn2, cursor2, 'М2')]):
            cursor.execute("SELECT * FROM част_мови WHERE частина_мови=?", (pos,))
            row = cursor.fetchone()
            if row:
                cursor_new.execute(
                    f"INSERT INTO {table_name} VALUES (?, " + ",".join("?"*20) + ")",
                    (label, *row[2:22])
                )

        conn_new.commit()

        # рахуємо суму по кожній колонці (К1-К20) для обчислення статистики
        columns_str = ", ".join([f"К{i}" for i in range(1, 21)])
        query = f"SELECT {columns_str} FROM {table_name}"
        data = cursor_new.execute(query).fetchall()
        columns_sum = [sum(x) for x in zip(*data)]

        # додаємо рядок з сумами по колонках у таблицю
        cursor_new.execute(
            f"INSERT INTO {table_name} VALUES ('ΣК', {','.join(['?']*20)})",
            columns_sum
        )

        # додаємо колонку для сум по рядках (ΣМ), якщо вона ще не існує
        try:
            cursor_new.execute(f"ALTER TABLE {table_name} ADD COLUMN 'ΣМ' INTEGER")
        except sqlite3.OperationalError:
            pass  # колонка вже існує, просто ігноруємо помилку

        # рахуємо суму по кожному рядку і записуємо у колонку ΣМ
        rows_sum = cursor_new.execute(
            f"SELECT Вибірка, {columns_str} FROM {table_name}"
        ).fetchall()
        for row in rows_sum:
            row_sum = sum(row[1:])
            cursor_new.execute(f"UPDATE {table_name} SET 'ΣМ'=? WHERE Вибірка=?", (row_sum, row[0]))

        conn_new.commit()

        # обчислення χ² статистики
        cursor = conn_new.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        absolute_frequencies = {}
        for row in rows:
            for i in range(1, 21):
                key = f'K{i}M{row[0][1]}'  # формуємо ключ для словника (наприклад K1M1, K2M2)
                absolute_frequencies[key] = row[i]

        # беремо суми по колонках та рядках для формул обчислення χ²
        column_sums = {f'ΣK{i}': rows[2][i] for i in range(1, 21)}
        row_sums = {f'ΣМ{rows[i][0][1]}': rows[i][-1] for i in range(2)}

        squared_frequencies = {key: val ** 2 for key, val in absolute_frequencies.items()}
        column_row_products = {
            f'K{i}M{k}': column_sums[f'ΣK{i}'] * row_sums[f'ΣМ{k}']
            for i in range(1, 21) for k in range(1, 3)
        }

        # обчислюємо частки для формули χ²
        fractions = {}
        for i in range(1, 21):
            for k in range(1, 3):
                key = f'K{i}M{k}'
                numerator = squared_frequencies[key]
                denominator = column_row_products[key]
                fractions[key] = round(numerator / denominator, 5)

        sum_of_fractions = sum(fractions.values())
        result = round(sum_of_fractions - 1, 5)

        # добираємо суму ΣМ для рядка ΣК, щоб обчислити фінальний результат χ²
        sum_M_K = cursor.execute(
            f"SELECT ΣМ FROM {table_name} WHERE Вибірка='ΣК'"
        ).fetchone()[0]

        final_result = round(result * sum_M_K, 2)
        result_label.config(text=f"χ² для {pos}: {final_result}") # виводимо результат у label


        conn1.close()
        conn2.close()
        conn_new.close()

    except Exception as e:
        messagebox.showerror("Error", str(e)) # показуємо повідомлення при помилці


# функція для обчислення критерію Стьюдента (t-критерій) для статистичних баз
def calculate_t_criterion(stat_db1_path, stat_db2_path, pos_tag):
    table_name = f"unique_{pos_tag}_values" # ім'я таблиці зі статистикою

    try:
        conn1 = sqlite3.connect(stat_db1_path)
        cursor1 = conn1.cursor()
        row1 = cursor1.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 1").fetchone()
        sum_ni_x = row1[1]
        sum_xini_x = row1[2]
        sum_sq_dev_ni_x = row1[3]
        average_x = sum_xini_x / sum_ni_x
        average_x = round(average_x, 2 if average_x >= 1 else 3)

        conn2 = sqlite3.connect(stat_db2_path)
        cursor2 = conn2.cursor()
        row2 = cursor2.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT 1").fetchone()
        sum_ni_y = row2[1]
        sum_xini_y = row2[2]
        sum_sq_dev_ni_y = row2[3]
        average_y = sum_xini_y / sum_ni_y
        average_y = round(average_y, 2 if average_y >= 1 else 3)

        # обчислюємо t-значення за формулою
        numerator = abs(average_x - average_y)
        denominator = math.sqrt(
            (sum_sq_dev_ni_x + sum_sq_dev_ni_y) / (sum_ni_x + sum_ni_y - 2) *
            ((sum_ni_x + sum_ni_y) / (sum_ni_x * sum_ni_y))
        )
        t_value = round(numerator / denominator, 2)
        return t_value # повертаємо t-значення

        conn1.close()
        conn2.close()

    except Exception as e:
        messagebox.showerror("Помилка обчислення", str(e))
        return None


# функція для запуску всіх обчислень після натискання кнопки
def run_all_calculations():
    db1 = entry1.get()  # шлях до першої бази даних
    db2 = entry2.get()
    stat_db1 = stat_entry1.get()  # шлях до першої статистичної бази
    stat_db2 = stat_entry2.get()
    pos = pos_choice.get()  # вибрана частина мови

    calculate_statistics(db1, db2, result_label, pos_choice)  # обчислюємо χ²

    t_value = calculate_t_criterion(stat_db1, stat_db2, pos)  # обчислюємо t-критерій
    if t_value is not None:
        # дописуємо результат t-критерію в текст результату
        result_label.config(text=result_label.cget("text") + f"\nКритерій Стьюдента для {pos}: {t_value}")


# функція для вибору файлу бази через діалог і вставки шляху у поле вводу
def select_db(title, entry):
    file_path = filedialog.askopenfilename(title=title, filetypes=[("SQLite DB", "*.db")])
    if file_path:
        entry.delete(0, tk.END)
        entry.insert(0, file_path)


# графічний інтерфейс
root = tk.Tk()
root.title("Аналізатор χ² та критерію Стьюдента")

frame = tk.Frame(root, padx=10, pady=10)
frame.pack()

# вибір файлів баз даних для зразків
tk.Label(frame, text="Оберіть sample_1.db:").grid(row=0, column=0, sticky="e")
entry1 = tk.Entry(frame, width=40)
entry1.grid(row=0, column=1)
tk.Button(frame, text="Переглянути", command=lambda: select_db("Choose Sample 1 DB", entry1)).grid(row=0, column=2)

tk.Label(frame, text="Оберіть sample_2.db:").grid(row=1, column=0, sticky="e")
entry2 = tk.Entry(frame, width=40)
entry2.grid(row=1, column=1)
tk.Button(frame, text="Переглянути", command=lambda: select_db("Choose Sample 2 DB", entry2)).grid(row=1, column=2)

# вибір файлів статистичних баз даних
tk.Label(frame, text="Оберіть stat_sample_1.db:").grid(row=5, column=0, sticky="e")
stat_entry1 = tk.Entry(frame, width=40)
stat_entry1.grid(row=5, column=1)
tk.Button(frame, text="Переглянути", command=lambda: select_db("Choose Stat Sample 1 DB", stat_entry1)).grid(row=5, column=2)

tk.Label(frame, text="Оберіть stat_sample_2.db:").grid(row=6, column=0, sticky="e")
stat_entry2 = tk.Entry(frame, width=40)
stat_entry2.grid(row=6, column=1)
tk.Button(frame, text="Переглянути", command=lambda: select_db("Choose Stat Sample 2 DB", stat_entry2)).grid(row=6, column=2)

# вибір частини мови для аналізу
tk.Label(frame, text="Частина мови:").grid(row=4, column=0, sticky="e")
pos_choice = tk.StringVar(value=PARTS_OF_SPEECH[0])
tk.OptionMenu(frame, pos_choice, *PARTS_OF_SPEECH).grid(row=4, column=1, sticky="w")

# кнопка запуску розрахунків
tk.Button(frame, text="Обчислити", command=run_all_calculations).grid(row=7, column=0, columnspan=3, pady=5)

# мітка для виводу результатів
result_label = tk.Label(frame, text="Результат з'явиться тут", fg="blue")
result_label.grid(row=8, column=0, columnspan=3, pady=10)

root.mainloop()
