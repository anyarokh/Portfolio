import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import nltk
from nltk.corpus import movie_reviews
from nltk.classify.scikitlearn import SklearnClassifier
from sklearn.svm import NuSVC
import pickle
import matplotlib.pyplot as plt

nltk.download('movie_reviews')

# Підготовка даних
reviews = [(list(movie_reviews.words(fileid)), category)
           for category in movie_reviews.categories()
           for fileid in movie_reviews.fileids(category)]
random.shuffle(reviews)

all_words = nltk.FreqDist(w.lower() for w in movie_reviews.words())
word_features = [word for word, _ in all_words.most_common(3800)]

def find_features(words):
    words = set(words)
    return {w: (w in words) for w in word_features}

featuresets = [(find_features(rev), category) for (rev, category) in reviews]
train_set = featuresets[:1800]
test_set = featuresets[1800:]

classifier = nltk.NaiveBayesClassifier.train(train_set)
nu_svc_classifier = SklearnClassifier(NuSVC())
nu_svc_classifier.train(train_set)

# Функції для кнопок
def show_top_words():
    top_words = all_words.most_common(20)
    output = "\n".join([f"{w}: {f}" for w, f in top_words])
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, output)

def analyze_clinical():
    total = all_words["clinical"]
    pos_words = [w.lower() for fid in movie_reviews.fileids('pos') for w in movie_reviews.words(fid)]
    neg_words = [w.lower() for fid in movie_reviews.fileids('neg') for w in movie_reviews.words(fid)]
    pos_count = pos_words.count("clinical")
    neg_count = neg_words.count("clinical")

    result = (f"Слово 'clinical' вживається всього {total} разів\n"
              f"У позитивних відгуках — {pos_count} разів\n"
              f"У негативних відгуках — {neg_count} разів")
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, result)

def show_accuracy():
    nb_acc = nltk.classify.accuracy(classifier, test_set) * 100
    nu_acc = nltk.classify.accuracy(nu_svc_classifier, test_set) * 100
    result = (f"Naive Bayes accuracy: {nb_acc:.2f}%\n"
              f"NuSVC accuracy: {nu_acc:.2f}%\n")

    if nb_acc > nu_acc:
        result += "Наївний баєсівський метод має вищу точність."
    elif nb_acc < nu_acc:
        result += "NuSVC має вищу точність."
    else:
        result += "Точності методів однакові."

    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, result)

def show_common_words_in_file():
    file_words = set(movie_reviews.words('pos/cv014_13924.txt'))
    common_words = [word for word in word_features if word in file_words]
    output = ", ".join(common_words)
    text_area.delete(1.0, tk.END)
    text_area.insert(tk.END, output)

# Функція для побудови графіка частотного розподілу слів
def plot_word_frequency():
    word_freq = all_words.most_common(20)
    words, counts = zip(*word_freq)
    plt.bar(words, counts)
    plt.xticks(rotation=45)
    plt.title("20 найбільш уживаних слів")
    plt.show()

# Побудова GUI
root = tk.Tk()
root.title("Аналіз відгуків")

frame = tk.Frame(root)
frame.pack(pady=10)

# Розташування кнопок в рядочок
buttons = [
    ("20 найуживаніших слів", show_top_words),
    ("Аналіз слова 'clinical'", analyze_clinical),
    ("Порівняння точності", show_accuracy),
    ("Слова з 3800 найуживаніших", show_common_words_in_file),
    ("Графік частотного розподілу", plot_word_frequency)
]

# Додаємо кнопки до фрейму
for idx, (text, command) in enumerate(buttons):
    tk.Button(frame, text=text, command=command).grid(row=0, column=idx, padx=5)

text_area = scrolledtext.ScrolledText(root, width=100, height=20, font=("Courier New", 10))
text_area.pack(padx=10, pady=10)

root.mainloop()
