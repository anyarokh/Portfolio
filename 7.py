import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import pymorphy3
from collections import Counter
import re
import sqlite3
import csv
from matplotlib import pyplot as plt

# Ініціалізую морфологічний аналізатор для української мови
morph = pymorphy3.MorphAnalyzer(lang='uk')

# Глобальні словники для зберігання частот і тональностей слів
freq_dict = {}
tone_dict = {}
file_path = ""

# Функція вибору текстового файлу та морфологічного аналізу його змісту
def choose_file():
    global file_path, freq_dict
    # Вибір файлу через стандартне вікно
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if not file_path:
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # Токенізація та нормалізація слів до початкової форми
    tokens = re.findall(r'\b\w+\b', text.lower())
    normalized_tokens = [morph.parse(word)[0].normal_form for word in tokens]
    freq_dict = Counter(normalized_tokens) # підрахунок частотності

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS frequency (
            word TEXT PRIMARY KEY,
            count INTEGER
        )
    ''')
    cursor.execute('DELETE FROM frequency') # очищаю таблицю перед новим аналізом

    # Вставляю або оновлюю частотність слів
    for word, count in freq_dict.items():
        cursor.execute('''
            INSERT INTO frequency (word, count) 
            VALUES (?, ?)
            ON CONFLICT(word) DO UPDATE SET count=count+excluded.count
        ''', (word, count))

    conn.commit()
    conn.close()

    output_area.config(state='normal')
    output_area.delete(1.0, tk.END)
    output_area.insert(tk.END, f"✅ Файл обрано та проаналізовано.\nВсього унікальних слів: {len(freq_dict)}")
    output_area.config(state='disabled')


# Аналіз наявності позитивної та негативної лексики згідно з файлом словника тональності
def analyze_text():
    global tone_dict
    # Завантажую словник тональностей, якщо ще не завантажено
    if not tone_dict:
        try:
            with open('tone-dict-uk.tsv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')
                for row in reader:
                    if len(row) == 2:
                        word, tone = row
                        tone_dict[word] = int(tone)
        except FileNotFoundError:
            messagebox.showerror("Помилка", "Не знайдено файл 'tone-dict-uk.tsv'")
            return

    # Отримую всі слова з бази даних
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT word FROM frequency')
    words = [row[0] for row in cursor.fetchall()]
    conn.close()

    # Розділяю слова за тональністю
    positive = set()
    negative = set()

    for word in words:
        if word in tone_dict:
            tone = tone_dict[word]
            if tone > 0:
                positive.add(word)
            elif tone < 0:
                negative.add(word)

    output_area.config(state='normal')
    output_area.delete(1.0, tk.END)
    output_area.insert(tk.END, f"✅ Кількість унікальних слів із позитивною лексикою: {len(positive)}\n")
    output_area.insert(tk.END, f"❌ Кількість унікальних слів із негативною лексикою: {len(negative)}")
    output_area.config(state='disabled')



# Вивід 10 найчастотніших слів з бази
def show_top_words():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT word, count FROM frequency ORDER BY count DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()

    result = "🔝 ТОП-10 найчастотніших слів:\n\n"
    result += "\n".join([f"{word}: {count}" for word, count in rows])

    output_area.config(state='normal')
    output_area.delete(1.0, tk.END)
    output_area.insert(tk.END, result)
    output_area.config(state='disabled')

# Повний список усіх слів з частотами
def show_all_frequencies():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT word, count FROM frequency ORDER BY count DESC')
    rows = cursor.fetchall()
    conn.close()

    result = "📋 Частотність усіх слів:\n\n"
    result += "\n".join([f"{word}: {count}" for word, count in rows])

    output_area.config(state='normal')
    output_area.delete(1.0, tk.END)
    output_area.insert(tk.END, result)
    output_area.config(state='disabled')


# Аналіз емоційного забарвлення слів + візуалізація
def analyze_emotive_lexicon():
    global tone_dict
    # Повторно завантажую словник тональностей, якщо потрібно
    if not tone_dict:
        try:
            with open('tone-dict-uk.tsv', 'r', encoding='utf-8') as f:
                reader = csv.reader(f, delimiter='\t')
                for row in reader:
                    if len(row) == 2:
                        word, tone = row
                        tone_dict[word] = int(tone)
        except FileNotFoundError:
            messagebox.showerror("Помилка", "Не знайдено файл 'tone-dict-uk.tsv'")
            return

    # Отримую частоти з бази
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT word, count FROM frequency')
    frequency_words = cursor.fetchall()
    conn.close()

    # Визначаю емоційно забарвлені слова
    emotive_words = []
    for word, count in frequency_words:
        if word in tone_dict:
            tone = tone_dict[word]
            emotive_words.append((word, count, tone))

    # Розділення за тоном
    positive_words = [(w, c, t) for w, c, t in emotive_words if t > 0]
    negative_words = [(w, c, t) for w, c, t in emotive_words if t < 0]
    neutral_words = [(w, c, t) for w, c, t in emotive_words if t == 0]

    result = "😃 Позитивна лексика:\n" + "\n".join([f"{w}: {c} (тональність {t})" for w, c, t in positive_words[:10]])
    result += "\n\n😠 Негативна лексика:\n" + "\n".join([f"{w}: {c} (тональність {t})" for w, c, t in negative_words[:10]])
    result += "\n\n😐 Нейтральна лексика:\n" + "\n".join([f"{w}: {c} (тональність {t})" for w, c, t in neutral_words[:10]])

    output_area.config(state='normal')
    output_area.delete(1.0, tk.END)
    output_area.insert(tk.END, result)
    output_area.config(state='disabled')

    # Побудова стовпчикової діаграми емоційної лексики
    values = [len(positive_words), len(negative_words)]
    labels = ['Позитивна', 'Негативна']
    plt.figure(figsize=(6, 4))
    plt.bar(labels, values, color=['green', 'red'])
    plt.title('Емоційна лексика (кількість слів)')
    plt.ylabel('Кількість')
    for i, val in enumerate(values):
        plt.text(i, val + 0.3, str(val), ha='center')
    plt.tight_layout()
    plt.show()

# GUI
root = tk.Tk()
root.title("Text Analyzer")
root.geometry("900x600")

# Панель з кнопками ліворуч
button_frame = tk.Frame(root, padx=10, pady=10)
button_frame.pack(side=tk.LEFT, fill=tk.Y)

tk.Button(button_frame, text="📂 Обрати файл", width=25, command=choose_file).pack(pady=5)
tk.Button(button_frame, text="📊 Аналіз тексту", width=25, command=analyze_text).pack(pady=5)
tk.Button(button_frame, text="🔝 ТОП-10 слів", width=25, command=show_top_words).pack(pady=5)
tk.Button(button_frame, text="📋 Усі слова", width=25, command=show_all_frequencies).pack(pady=5)
tk.Button(button_frame, text="😃 Емотивна лексика", width=25, command=analyze_emotive_lexicon).pack(pady=5)

# Область для результатів
output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Arial", 12))
output_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
output_area.config(state='disabled')

root.mainloop()
