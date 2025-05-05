import sqlite3
import random
from tkinter import *
from tkinter import ttk, messagebox

# Підключення до БД
connection = sqlite3.connect("pol_lab02.s3db")
cursor = connection.cursor()

# Словник усіх можливих відмінків - використовуються як ключі для запитів і відображення
cases = {
    "Називний одн. (sgN)": "sgN",
    "Родовий одн. (sgG)": "sgG",
    "Давальний одн. (sgD)": "sgD",
    "Знахідний одн. (sgA)": "sgA",
    "Орудний одн. (sgI)": "sgI",
    "Місцевий одн. (sgL)": "sgL",
    "Кличний одн. (sgV)": "sgV",
    "Називний множ. (plN)": "plN",
    "Родовий множ. (plG)": "plG",
    "Давальний множ. (plD)": "plD",
    "Знахідний множ. (plA)": "plA",
    "Орудний множ. (plI)": "plI",
    "Місцевий множ. (plL)": "plL",
    "Кличний множ. (plV)": "plV"
}
# Список міток і відповідних стовпців таблиці
case_labels = list(cases.keys())
case_columns = list(cases.values())

# головне вікно
root = Tk()
root.title("Граматика польської мови")
root.geometry("1100x650")

notebook = ttk.Notebook(root)
notebook.pack(fill=BOTH, expand=True)

# Вкладка "Головна"
frame_main = Frame(notebook)
notebook.add(frame_main, text="Головна")

# Таблиця для відображення слів та їхніх форм у різних відмінках
tree_all = ttk.Treeview(frame_main, columns=case_columns, show="headings", height=20)
for col in case_columns:
    tree_all.heading(col, text=col)
    tree_all.column(col, width=70)
tree_all.pack(padx=10, pady=10, fill=X)

# Завантаження всіх слів з бази у таблицю
def load_all_words():
    cursor.execute(f"SELECT {', '.join(case_columns)} FROM tnoun")
    for row in cursor.fetchall():
        tree_all.insert("", "end", values=row)

load_all_words()

# Блок пошуку слова у називному відмінку
frame_search = Frame(frame_main)
frame_search.pack(pady=10)

label_search = Label(frame_search, text="Пошук слова:", font=("Arial", 12))
label_search.grid(row=0, column=0, padx=5)

# Поле для введення або вибору слова
entry_word = ttk.Combobox(frame_search, font=("Arial", 12), width=30)
entry_word.grid(row=0, column=1, padx=5)

# Заповнення Combobox списком унікальних іменників у називному однини
def fill_combobox():
    cursor.execute("SELECT DISTINCT sgN FROM tnoun WHERE sgN IS NOT NULL")
    words = sorted([row[0] for row in cursor.fetchall()])
    entry_word["values"] = words
    entry_word.bind("<KeyRelease>", lambda e: update_combobox(words))

# Оновлення списку відповідно до введеного користувачем тексту
def update_combobox(word_list):
    typed = entry_word.get().lower()
    filtered = [w for w in word_list if w.lower().startswith(typed)]
    entry_word["values"] = filtered

fill_combobox()

# Текстове поле для виводу результатів пошуку
text_output = Text(frame_main, height=10, font=("Arial", 12))
text_output.pack(pady=5, padx=10, fill=X)


# Функція для показу всіх відмінкових форм вибраного слова
def show_word_forms():
    word = entry_word.get().strip()
    if not word:
        messagebox.showwarning("Помилка", "Введіть або оберіть слово.")
        return
    cursor.execute(f"SELECT {', '.join(case_columns)} FROM tnoun WHERE sgN = ?", (word,))
    result = cursor.fetchone()
    text_output.delete("1.0", END)
    if result:
        for label, form in zip(case_labels, result):
            text_output.insert(END, f"{label}: {form if form else '-'}\n")
    else:
        text_output.insert(END, "Слово не знайдено в базі.")

# Кнопка для запуску пошуку та показу результатів
btn_show = Button(frame_search, text="Показати відмінки", font=("Arial", 12), command=show_word_forms)
btn_show.grid(row=0, column=2, padx=5)

frame_quiz = Frame(notebook)
notebook.add(frame_quiz, text="Перевірка знань")

quiz_data = {} # Словник для зберігання даних поточного питання

label_question = Label(frame_quiz, text="Натисніть 'Почати тест'", font=("Arial", 14))
label_question.pack(pady=15)

btn_frame = Frame(frame_quiz)
btn_frame.pack(pady=10)

answer_buttons = [] # Список кнопок з відповідями, щоб їх можна було видалити при новому питанні

def choose_answer(user_choice):
    correct = quiz_data.get("correct")
    if user_choice == correct:
        messagebox.showinfo("Результат", "✅ Правильно!")
    else:
        messagebox.showerror("Результат", f"❌ Неправильно!\nПравильна форма: {correct}")

# Створення нового питання
def start_quiz():
    cursor.execute(f"SELECT {', '.join(case_columns)} FROM tnoun ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()
    if not row:
        return

    word_forms = dict(zip(case_columns, row))
    sgN = word_forms.get("sgN", "")
    quiz_data["word"] = sgN

    # Випадковий вибір правильного відмінка
    col_correct = random.choice(case_columns)
    form_correct = word_forms[col_correct] or "-"
    quiz_data["correct"] = form_correct

    # Взяти 3 інші форми цього слова (але з інших відмінків)
    other_forms = [v for k, v in word_forms.items() if k != col_correct and v]
    random.shuffle(other_forms)
    options = [form_correct] + other_forms[:3]
    random.shuffle(options)

    label_question.config(text=f"Слово: {sgN}\nОберіть {get_case_label(col_correct)}:")

    # Очистити старі кнопки
    for btn in answer_buttons:
        btn.destroy()
    answer_buttons.clear()

    # Створити кнопки з варіантами відповіді
    for opt in options:
        btn = Button(btn_frame, text=opt, font=("Arial", 12), width=25,
                     command=lambda choice=opt: choose_answer(choice))
        btn.pack(pady=2)
        answer_buttons.append(btn)

# Повернення мітки для назви відмінка
def get_case_label(col):
    for label, key in cases.items():
        if key == col:
            return label
    return col

btn_start = Button(frame_quiz, text="Почати тест", font=("Arial", 12), command=start_quiz)
btn_start.pack(pady=5)

root.mainloop()
connection.close()
