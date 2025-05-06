import tkinter as tk
from tkinter import ttk, scrolledtext
import random
import nltk
from nltk.corpus import movie_reviews
from nltk.classify.scikitlearn import SklearnClassifier
from sklearn.svm import NuSVC
import pickle
import matplotlib.pyplot as plt
import io
import sys

nltk.download('movie_reviews')

# Завантаження відгуків з NLTK і їх перемішування
reviews = [(list(movie_reviews.words(fileid)), category)
           for category in movie_reviews.categories()
           for fileid in movie_reviews.fileids(category)]
random.shuffle(reviews)

# Підготовка списку найбільш частих слів
all_words = nltk.FreqDist(w.lower() for w in movie_reviews.words())
word_features = [word for word, _ in all_words.most_common(3800)]

# Функція для визначення наявності слова в тексті
def find_features(words):
    words = set(words)
    return {w: (w in words) for w in word_features}

# Створення навчальних та тестових наборів
featuresets = [(find_features(rev), category) for (rev, category) in reviews]
train_set = featuresets[:1800]
test_set = featuresets[1800:]

# Навчання
classifier = nltk.NaiveBayesClassifier.train(train_set)
with open("naivebayes_pickle", "wb") as save_classifier:
    pickle.dump(classifier, save_classifier)

with open("naivebayes_pickle", "rb") as classifier_f:
    classifier = pickle.load(classifier_f)

nu_svc_classifier = SklearnClassifier(NuSVC())
nu_svc_classifier.train(train_set)

# GUI функції
def show_top_words_custom():
    try:
        num = int(entry_top_n.get()) # Введене число для кількості слів
    except ValueError:
        num = 20 # За замовчуванням 20 слів
    top_words = all_words.most_common(num)
    output = "\n".join([f"{w}: {f}" for w, f in top_words]) # Формування тексту для виведення
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, output)

# Функція для показу точності класифікаторів
def show_accuracy():
    nb_acc = nltk.classify.accuracy(classifier, test_set) * 100
    nu_acc = nltk.classify.accuracy(nu_svc_classifier, test_set) * 100
    result = (f"Naive Bayes accuracy: {nb_acc:.2f}%\n"
              f"NuSVC accuracy: {nu_acc:.2f}%\n")
    result += ("Наївний баєсівський метод має вищу точність." if nb_acc > nu_acc
               else "NuSVC має вищу точність." if nu_acc > nb_acc
               else "Точності методів однакові.")
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, result)

# Функція для побудови графіка частоти слів
def plot_word_frequency():
    try:
        num = int(entry_top_n.get())
    except ValueError:
        num = 20
    word_freq = all_words.most_common(num)
    words, counts = zip(*word_freq)
    plt.bar(words, counts) # Побудова стовпчикової діаграми
    plt.xticks(rotation=45) # Поворот підписів на осі X
    plt.title(f"{num} найбільш уживаних слів")
    plt.show()

# Функція для повного аналізу класифікаторів
def show_full_analysis():
    nb_acc = nltk.classify.accuracy(classifier, test_set) * 100
    nu_acc = nltk.classify.accuracy(nu_svc_classifier, test_set) * 100
    buffer = io.StringIO()
    sys.stdout = buffer
    print(f"Naive Bayes Algorithm accuracy percent: {nb_acc:.1f}")
    print("20 найважливіших ознак:")
    classifier.show_most_informative_features(20)
    print(f"NuSVC Algorithm accuracy percent: {nu_acc:.1f}")
    sys.stdout = sys.__stdout__
    result = buffer.getvalue() # Отримання виводу в буфер
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, result)

# Функція для аналізу конкретного слова
def analyze_selected_word():
    word = word_combo.get().lower() # Отримання вибраного слова
    total = all_words[word] # Загальна кількість вживань
    pos_words = [w.lower() for fid in movie_reviews.fileids('pos') for w in movie_reviews.words(fid)]
    neg_words = [w.lower() for fid in movie_reviews.fileids('neg') for w in movie_reviews.words(fid)]
    pos_count = pos_words.count(word)
    neg_count = neg_words.count(word)
    result = (f"Слово '{word}' вживається всього {total} разів\n"
              f"У позитивних відгуках — {pos_count} разів\n"
              f"У негативних відгуках — {neg_count} разів")
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, result)

# Побудова GUI
root = tk.Tk()
root.title("Аналіз відгуків")

# Рядок 1 - кнопки
frame1 = tk.Frame(root)
frame1.pack(pady=5)

tk.Button(frame1, text="Порівняння точності", command=show_accuracy).grid(row=0, column=1, padx=5)
tk.Button(frame1, text="Графік частотного розподілу", command=plot_word_frequency).grid(row=0, column=2, padx=5)
tk.Button(frame1, text="Повний аналіз класифікаторів", command=show_full_analysis).grid(row=0, column=3, padx=5)

# Рядок 2 - для вибору слова
frame2 = tk.Frame(root)
frame2.pack(pady=5)

tk.Label(frame2, text="Аналіз слова:").pack(side=tk.LEFT, padx=5)
word_combo = ttk.Combobox(frame2, values=sorted(all_words.keys()), width=30)
word_combo.set("clinical")
word_combo.pack(side=tk.LEFT)
tk.Button(frame2, text="Аналізувати", command=analyze_selected_word).pack(side=tk.LEFT, padx=5)

# Рядок 3 — для введення кількості найуживаніших слів
frame3 = tk.Frame(root)
frame3.pack(pady=5)

tk.Label(frame3, text="Кількість найуживаніших слів:").pack(side=tk.LEFT, padx=5)

entry_top_n = tk.Entry(frame3, width=5)
entry_top_n.insert(0, "20")
entry_top_n.pack(side=tk.LEFT)


# Оновлення списку найуживаніших слів при введенні
def update_top_words(event=None):
    try:
        num = int(entry_top_n.get())
        if num < 1:
            raise ValueError
    except ValueError:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, "Будь ласка, введіть додатне число.")
        return
    top_words = all_words.most_common(num)
    output = "\n".join([f"{w}: {f}" for w, f in top_words])
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, output)

# Оновлення під час кожного введення символу
entry_top_n.bind("<KeyRelease>", update_top_words)

# Вивід
text_area = scrolledtext.ScrolledText(root, width=100, height=20, font=("Courier New", 10))
text_area.pack(padx=10, pady=10)

root.mainloop()
