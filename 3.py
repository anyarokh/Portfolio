# імпортую бібліотеки для інтерфейсу, бази даних, математичних обчислень та роботи з файлами
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import math
import os

# визначаю список баз даних, які можна обрати
DB_OPTIONS = ["stat_sample_1.db", "stat_sample_2.db"]
# перелік частин мови, з якими працюватиму
POS_OPTIONS = ["ADJF", "ADVB", "CONJ", "GRND", "NOUN", "NPRO", "NUMR", "PRCL", "PREP", "VERB"]

# створюю головне вікно програми
root = tk.Tk()
root.title("Аналіз мовних частин")

# створюю змінні для збереження обраної бази та частини мови
selected_db = tk.StringVar(value=DB_OPTIONS[0])
selected_pos = tk.StringVar(value=POS_OPTIONS[0])


# функція, яка виконує розрахунки статистики для вибраної частини мови
def calculate_statistics():
    db_path = selected_db.get()
    pos = selected_pos.get()

    # перевіряю, чи існує обрана база даних
    if not os.path.exists(db_path):
        messagebox.showerror("Помилка", f"База даних '{db_path}' не знайдена.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # отримую список таблиць у базі
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()

        output_text.delete("1.0", tk.END)  # очищаю текстове поле перед новим виводом
        filename = f"results_{pos}_{db_path.replace('.db', '')}.txt"  # створюю назву файлу для збереження результатів

        with open(filename, 'w', encoding='utf-8') as f:
            for table in tables:
                table_name = table[0]
                # обробляю тільки таблицю, яка відповідає поточній частині мови
                if table_name == f"unique_{pos}_values":
                    # отримую загальну кількість вживань
                    cursor.execute(f"SELECT SUM(ni) FROM {table_name}")
                    total_ni = cursor.fetchone()[0]
                    if not total_ni or total_ni == 0:
                        continue

                    # отримую суму добутків xi * ni
                    cursor.execute(f"SELECT SUM(xini) FROM {table_name}")
                    total_xini = cursor.fetchone()[0]
                    average_frequency = total_xini / total_ni

                    # форматую середню частоту залежно від її значення
                    if average_frequency >= 1:
                        average_frequency = round(average_frequency, 2)
                    else:
                        avg_str = "{:.3f}".format(average_frequency)
                        if avg_str[-1] == '0' and avg_str[-2] == '0':
                            average_frequency = round(average_frequency, 2)
                        elif avg_str[-1] == '0':
                            average_frequency = round(average_frequency, 3)
                        else:
                            average_frequency = round(average_frequency, 2)

                    # отримую суму квадратів відхилень, помножених на ni
                    cursor.execute(f'SELECT SUM("dispersion") FROM {table_name}')
                    total_dif = cursor.fetchone()[0]

                    if total_dif is None:
                        continue

                    # обчислюю стандартне відхилення
                    standard_deviation = math.sqrt(total_dif / total_ni)
                    standard_deviation_rounded = round(standard_deviation, 2)

                    # обчислюю міру коливання середньої частоти
                    coef_var_freq = standard_deviation_rounded / math.sqrt(total_ni)
                    coef_var_freq_rounded = round(coef_var_freq, 2)

                    # обчислюю інтервали коливань для 68% і 95%
                    interval_68 = (
                        round(average_frequency - coef_var_freq_rounded, 2),
                        round(average_frequency + coef_var_freq_rounded, 2)
                    )
                    interval_95 = (
                        round(average_frequency - 2 * coef_var_freq_rounded, 2),
                        round(average_frequency + 2 * coef_var_freq_rounded, 2)
                    )

                    # коефіцієнт варіації
                    coef_variation = round(standard_deviation_rounded / average_frequency, 2)

                    # коефіцієнт стабільності
                    stability_coef = 1 - (standard_deviation_rounded / (average_frequency * math.sqrt(total_ni - 1)))
                    stability_rounded = round(stability_coef, 2)

                    # відносна похибка
                    relative_error = (1.96 * coef_var_freq_rounded) / average_frequency
                    relative_error_rounded = round(relative_error, 3)

                    # формую рядок з результатами
                    result = (
                        f"Середня частота для {table_name}: {average_frequency}\n"
                        f"Середнє квадратичне відхилення для {table_name}: {standard_deviation_rounded}\n"
                        f"Міра коливання середньої частоти для {table_name}: {coef_var_freq_rounded}\n"
                        f"Смуга коливання для 68 % для {table_name}: {interval_68}\n"
                        f"Смуга коливання для 95 % для {table_name}: {interval_95}\n"
                        f"Коефіцієнт варіації (v) для {table_name}: {coef_variation}\n"
                        f"Коефіцієнт стабільності (D) для {table_name}: {stability_rounded}\n"
                        f"Відносна похибка для {table_name}: {relative_error_rounded}\n\n"
                    )
                    # додаю результат у вікно й файл
                    output_text.insert(tk.END, result)
                    f.write(result)
        # повідомляю про успішне збереження результатів
        messagebox.showinfo("Успіх", f"Результати збережено у '{filename}'")
        conn.close()

    except Exception as e:
        # у разі помилки виводжу повідомлення
        messagebox.showerror("Помилка", str(e))


# створюю інтерфейс для вибору бази даних
ttk.Label(root, text="Оберіть базу даних:").grid(row=0, column=0, sticky='w', padx=5, pady=5)
ttk.OptionMenu(root, selected_db, DB_OPTIONS[0], *DB_OPTIONS).grid(row=0, column=1, padx=5)
# створюю інтерфейс для вибору частини мови
ttk.Label(root, text="Оберіть частину мови:").grid(row=1, column=0, sticky='w', padx=5, pady=5)
ttk.OptionMenu(root, selected_pos, POS_OPTIONS[0], *POS_OPTIONS).grid(row=1, column=1, padx=5)
# кнопка запуску розрахунків
ttk.Button(root, text="Розрахувати", command=calculate_statistics).grid(row=2, column=0, columnspan=2, pady=10)
# поле для виведення результатів
output_text = tk.Text(root, width=90, height=30)
output_text.grid(row=3, column=0, columnspan=2, padx=10, pady=10)
# запускаю головний цикл інтерфейсу
root.mainloop()
