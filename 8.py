import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

DB_PATH = "bilingual_dictionary.db"

# Ініціалізація БД та заповнення
def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vocab (
            ID INTEGER PRIMARY KEY,
            category TEXT,
            foreign_word TEXT NOT NULL,
            translation_ukr TEXT NOT NULL,
            UNIQUE(foreign_word, translation_ukr)
        )
    ''')
    words = [
        ("Кольори", "crvena", "червоний"), ("Кольори", "plava", "синій"),
        ("Кольори", "žuta", "жовтий"), ("Кольори", "crna", "чорний"),
        ("Кольори", "zelena", "зелений"), ("Кольори", "bijela", "білий"),
        ("Кольори", "ljubičasta", "фіолетовий"), ("Кольори", "siva", "сірий"),
        ("Кольори", "narančasta", "помаранчевий"), ("Кольори", "ružičasta", "рожевий"),
        ("Кольори", "smeđa", "коричневий"), ("Кольори", "srebrna", "сріблястий"),
        ("Кольори", "zlatna", "золотистий"), ("Кольори", "lila", "бузковий"),
        ("Предмети", "stolica", "стілець"), ("Предмети", "stol", "стіл"),
        ("Предмети", "prozor", "вікно"), ("Предмети", "vrata", "двері"),
        ("Предмети", "knjiga", "книга"), ("Предмети", "bilježnica", "зошит"),
        ("Предмети", "ormar", "шафа"), ("Предмети", "sat", "годинник"),
        ("Предмети", "olovka", "олівець"), ("Предмети", "računalo", "комп'ютер"),
        ("Предмети", "telefon", "телефон"), ("Предмети", "lampa", "лампа"),
        ("Предмети", "kugla", "м'яч"), ("Предмети", "dalekozor", "бінокль"),
        ("Їжа", "kruh", "хліб"), ("Їжа", "mlijeko", "молоко"),
        ("Їжа", "sir", "сир"), ("Їжа", "jabuka", "яблуко"),
        ("Їжа", "naranča", "апельсин"), ("Їжа", "meso", "м'ясо"),
        ("Їжа", "jaje", "яйце"), ("Їжа", "sladoled", "морозиво"),
        ("Їжа", "banana", "банан"), ("Їжа", "grožđe", "виноград"),
        ("Їжа", "mrkva", "морква"), ("Їжа", "krumpir", "картопля"),
        ("Їжа", "tjestenina", "макарони"), ("Їжа", "jogurt", "йогурт"),
        ("Тварини", "pas", "собака"), ("Тварини", "mačka", "кіт"),
        ("Тварини", "ptica", "птах"), ("Тварини", "konj", "кінь"),
        ("Тварини", "riba", "риба"), ("Тварини", "ovca", "вівця"),
        ("Тварини", "krava", "корова"), ("Тварини", "lav", "лев"),
        ("Тварини", "vuk", "вовк"), ("Тварини", "kornjača", "черепаха"),
        ("Тварини", "zec", "кролик"), ("Тварини", "vjeverica", "білка"),
        ("Тварини", "slon", "слон"), ("Тварини", "pile", "курка")
    ]
    # Додавання слів в базу, уникаючи дублікатів
    for category, foreign_word, translation_ukr in words:
        cursor.execute('''
            INSERT OR IGNORE INTO vocab (category, foreign_word, translation_ukr)
            VALUES (?, ?, ?)
        ''', (category, foreign_word, translation_ukr))
    conn.commit()
    conn.close()

# Завантаження слів за категорією та пошуком
def load_words_by_category():
    selected_category = category_combobox.get()
    search_text = search_entry.get().strip().lower() # Пошук без урахування регістру
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    if search_text:
        # Якщо введено пошуковий запит — фільтруємо за словом чи перекладом
        cursor.execute('''
            SELECT foreign_word, translation_ukr FROM vocab
            WHERE category = ? AND (LOWER(foreign_word) LIKE ? OR LOWER(translation_ukr) LIKE ?)
        ''', (selected_category, f'%{search_text}%', f'%{search_text}%'))
    else:
        # Інакше просто всі слова категорії
        cursor.execute("SELECT foreign_word, translation_ukr FROM vocab WHERE category = ?", (selected_category,))
    words = cursor.fetchall()
    conn.close()
    word_listbox.delete(0, tk.END) # Очищаємо список перед новим виводом
    for word in words:
        word_listbox.insert(tk.END, f"{word[0]} — {word[1]}") # Виводимо у форматі "іноземне — переклад"

# Додавання нового слова
def add_new_word():
    new_category = entry_new_category.get().strip()
    selected_category = add_category_combobox.get().strip()

    # Якщо введено нову категорію, використовуємо її, інакше — обрану з випадаючого списку
    category = new_category if new_category and new_category != "Або введіть нову категорію" else selected_category

    foreign_word = entry_foreign.get().strip()
    translation_ukr = entry_translation.get().strip()

    # Перевірка на заповненість усіх полів
    if not all([category, foreign_word, translation_ukr]):
        messagebox.showwarning("Помилка", "Заповніть усі поля!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO vocab (category, foreign_word, translation_ukr)
            VALUES (?, ?, ?)
        ''', (category, foreign_word, translation_ukr))
        conn.commit()
        messagebox.showinfo("Успіх", f"Слово додано в категорію: {category}")
        refresh_categories()
        add_category_combobox.set("")  # Очистити попереднє
        entry_new_category.delete(0, tk.END)  # Очистити нову категорію
        entry_foreign.delete(0, tk.END)
        entry_translation.delete(0, tk.END)
    except sqlite3.IntegrityError:
        messagebox.showerror("Помилка", "Таке слово вже існує.") # Обробка дубліката
    conn.close()


# Оновлення категорій у всіх комбобоксах
def refresh_categories():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM vocab ORDER BY category")
    categories = [row[0] for row in cursor.fetchall()]
    conn.close()
    category_combobox['values'] = categories
    add_category_combobox['values'] = categories
    # Якщо є категорії — автоматично вибираємо першу
    if categories:
        category_combobox.set(categories[0])
        add_category_combobox.set(categories[0])
        load_words_by_category()

# GUI
init_database()
root = tk.Tk()
root.title("Білінгвальний словник")
notebook = ttk.Notebook(root) # Створюємо вкладки
notebook.pack(expand=True, fill="both")

# Вкладка "Словник"
frame_dict = ttk.Frame(notebook)
notebook.add(frame_dict, text="Словник")

ttk.Label(frame_dict, text="Оберіть категорію:").pack(pady=5)
category_combobox = ttk.Combobox(frame_dict, state="readonly")
category_combobox.pack()
category_combobox.bind("<<ComboboxSelected>>", lambda e: load_words_by_category()) # Автозавантаження

ttk.Label(frame_dict, text="Пошук слова:").pack(pady=5)
search_entry = ttk.Entry(frame_dict, width=30)
search_entry.pack()
ttk.Button(frame_dict, text="Пошук", command=load_words_by_category).pack(pady=5)

word_listbox = tk.Listbox(frame_dict, width=40, height=20) # Вивід слів
word_listbox.pack(pady=10)

# Вкладка "Додати слово"
frame_add = ttk.Frame(notebook)
notebook.add(frame_add, text="Додати слово")

ttk.Label(frame_add, text="Оберіть категорію або введіть нову:").pack(pady=5)
add_category_combobox = ttk.Combobox(frame_add, width=30) # Вибір існуючої категорії
add_category_combobox.pack(pady=2)

entry_new_category = ttk.Entry(frame_add, width=30) # Поле для нової категорії
entry_new_category.pack(pady=2)
entry_new_category.insert(0, "Або введіть нову категорію")

ttk.Label(frame_add, text="Іноземне слово:").pack(pady=2)
entry_foreign = ttk.Entry(frame_add, width=30)
entry_foreign.pack()

ttk.Label(frame_add, text="Переклад українською:").pack(pady=2)
entry_translation = ttk.Entry(frame_add, width=30)
entry_translation.pack()

ttk.Button(frame_add, text="Додати слово", command=add_new_word).pack(pady=10)

# Завантаження категорій при запуску
refresh_categories()

root.mainloop()
