import tkinter as tk
from tkinter import filedialog
import re
from collections import defaultdict
import stanza
import matplotlib.pyplot as plt

# Завантажую українську модель Stanza (один раз), далі створюю пайплайн для токенізації та POS-тегування
stanza.download('uk')
nlp = stanza.Pipeline(lang='uk', processors='tokenize,pos', use_gpu=False)

# Глобальні змінні, які зберігають інформацію про слова, їх частини мови і частоти
pos_dict_global = defaultdict(set)
pos_count_global = defaultdict(int)
all_words_global = []
word_frequencies_global = {}
word_pos_map = {}

# Функція для отримання частини мови слова — якщо немає, повертає UNKNOWN
def get_pos(word):
    return word_pos_map.get(word.lower(), 'UNKNOWN')

# Витягаю всі слова з текстового файлу, використовуючи регулярний вираз (тільки слова, без пунктуації)
def extract_words_from_file(filename):
    with open(filename, 'r', encoding='utf-8') as file:
        text = file.read()
    return re.findall(r'\b\w+\b', text.lower())

# Рахую, скільки разів кожне слово зустрічається в тексті
def count_word_frequencies(words):
    frequencies = defaultdict(int)
    for word in words:
        frequencies[word] += 1
    return frequencies

# Створюю словник частин мови: для кожного слова визначаю POS через Stanza
def create_pos_dictionary(words):
    global pos_dict_global, pos_count_global, word_pos_map
    text = ' '.join(words)
    doc = nlp(text)

    pos_dict = defaultdict(set)
    pos_counts = defaultdict(int)
    word_pos_map.clear()

    for sentence in doc.sentences:
        for word in sentence.words:
            token = word.text.lower()
            pos = word.upos or 'UNKNOWN'
            word_pos_map[token] = pos
            pos_dict[pos].add(token)
            pos_counts[pos] += 1

    pos_dict_global = pos_dict
    pos_count_global = pos_counts
    return word_pos_map

# Окрема функція для обчислення частоти службових частин мови — це вручну задані списки
def calculate_service_part_of_speech_frequencies(words):
    coordinating_count = 0
    subordinating_count = 0
    preposition_count = 0
    particle_count = 0

    # Власноруч зібрані списки службових слів
    coordinating_conjunctions = {'і', 'та', 'або', 'але', 'проте', 'однак', 'зате', 'таки'}
    subordinating_conjunctions = {'коли', 'якщо', 'щоб', 'тому що', 'хоча', 'доки', 'оскільки'}
    particles = {'би', 'б', 'хай', 'нехай', 'аби-', 'де-', 'чи-', 'що-', 'будь-', '-небудь', 'казна-', 'хтозна-', 'не',
                 'ні', 'ані', 'ось', 'осьде', 'он', 'от', 'ото', 'це', 'оце', 'якраз', 'ледве', 'просто', 'прямо',
                 'власне', 'майже', 'саме', 'тільки', 'ліше', 'хоч', 'хоч би', 'виключно'}

    # Перевіряю кожне слово, чи належить воно до службових
    for word in words:
        w = word.lower()
        pos = get_pos(w)
        if w in coordinating_conjunctions:
            coordinating_count += 1
        elif w in subordinating_conjunctions:
            subordinating_count += 1
        elif pos == 'ADP':
            preposition_count += 1
        elif w in particles or pos == 'PART':
            particle_count += 1

    return coordinating_count, subordinating_count, preposition_count, particle_count

# Відкриваю файл через вікно, зчитую, розраховую частоти, створюю POS-словник
def browse_file():
    global all_words_global, word_frequencies_global
    filename = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if filename:
        words = extract_words_from_file(filename)
        all_words_global = words
        word_frequencies = count_word_frequencies(words)
        word_frequencies_global = word_frequencies
        create_pos_dictionary(words)

        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Файл успішно завантажено.\n")
        result_text.insert(tk.END, "Оберіть частину мови з меню або натисніть кнопку для побудови діаграми чи таблиці.")

# Виводжу всі слова певної частини мови і рахую покриття
def show_words_by_pos(*args):
    selected_pos = pos_var.get()
    if selected_pos in pos_dict_global:
        words_list = sorted(pos_dict_global[selected_pos])
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"Слова з частиною мови '{selected_pos}':\n\n")
        result_text.insert(tk.END, ", ".join(words_list))

        total_words = len(all_words_global)

        # Підрахунок кількості слів певної частини мови в тексті
        pos_count_text = sum(1 for w in all_words_global if get_pos(w) == selected_pos)
        # Кількість унікальних слів певної частини мови
        pos_count_dict = len(pos_dict_global[selected_pos])

        # Покриття словника = кількість унікальних слів певної частини мови / загальна кількість слів
        coverage_dict = (pos_count_dict / total_words) * 100 if total_words else 0
        # Покриття тексту = кількість слів певної частини мови / загальна кількість слів
        coverage_text = (pos_count_text / total_words) * 100 if total_words else 0

        result_text.insert(tk.END, f"\n\nПокриття словника {selected_pos}: {coverage_dict:.2f}%")
        result_text.insert(tk.END, f"\nПокриття тексту {selected_pos}: {coverage_text:.2f}%")
    else:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, f"Слів з частиною мови '{selected_pos}' не знайдено.")

# Малюю кругову діаграму по частинах мови
def plot_pos_frequencies():
    if not pos_count_global:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Немає даних для візуалізації. Завантажте текстовий файл.")
        return

    labels = list(pos_count_global.keys())
    sizes = list(pos_count_global.values())

    plt.figure(figsize=(8, 6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.title('Розподіл частин мови у тексті')
    plt.axis('equal')
    plt.show()

# Таблиця: слово — частота — частина мови, плюс службові слова
def show_frequency_table():
    if not word_frequencies_global:
        result_text.delete(1.0, tk.END)
        result_text.insert(tk.END, "Не завантажено жодного тексту.")
        return

    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, "Таблиця частотності слів:\n\n")
    result_text.insert(tk.END, f"{'Слово'.ljust(20)}{'Частота'.ljust(10)}{'Частина мови'}\n")
    result_text.insert(tk.END, "-" * 50 + "\n")

    for word, freq in sorted(word_frequencies_global.items(), key=lambda item: item[1], reverse=True):
        pos = get_pos(word)
        result_text.insert(tk.END, f"{word.ljust(20)}{str(freq).ljust(10)}{pos}\n")

    # Додаємо службові частини мови
    words = all_words_global
    coor, subor, prep, part = calculate_service_part_of_speech_frequencies(words)
    total_words = len(words)

    result_text.insert(tk.END, "\nСлужбові частини мови:\n")
    result_text.insert(tk.END, f"Сурядні сполучники: {coor} ({(coor / total_words) * 100:.2f}%)\n")
    result_text.insert(tk.END, f"Підрядні сполучники: {subor} ({(subor / total_words) * 100:.2f}%)\n")


# Головне вікно
root = tk.Tk()
root.title("Аналізатор частин мови")
root.geometry("700x600")

# Панель з кнопками в один рядок
button_frame = tk.Frame(root)
button_frame.pack(pady=10)

# Кнопки
tk.Button(button_frame, text="Вибрати файл", command=browse_file).pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="Діаграма POS", command=plot_pos_frequencies).pack(side=tk.LEFT, padx=5)
tk.Button(button_frame, text="Таблиця частот", command=show_frequency_table).pack(side=tk.LEFT, padx=5)

# Меню вибору частини мови
pos_var = tk.StringVar(root)
pos_var.set("NOUN")
pos_var.trace("w", show_words_by_pos)

tk.OptionMenu(button_frame, pos_var,
              "NOUN", "VERB", "ADJ", "ADV", "PRON", "PROPN", "ADP", "AUX",
              "CCONJ", "SCONJ", "PART", "INTJ", "NUM", "DET", "UNKNOWN").pack(side=tk.LEFT, padx=5)

# Текстове поле для результатів
result_text = tk.Text(root, height=28, width=85)  # Зменшена ширина
result_text.pack(pady=10)

root.mainloop()