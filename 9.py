import nltk
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from nltk.corpus import stopwords, wordnet as wn
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

# Завантаження ресурсів для роботи з текстом
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('rte')


def improved_score_sentences(sentences):
    ps = PorterStemmer()
    stop_words = set(stopwords.words("english"))
    preprocessed = []

    # Попередня обробка кожного речення: токенізація, фільтрація, стемінг
    for sent in sentences:
        words = word_tokenize(sent.lower())
        filtered = [ps.stem(w) for w in words if w.isalnum() and w not in stop_words]
        preprocessed.append(" ".join(filtered))

    # Обчислення TF-IDF для кожного речення
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(preprocessed).toarray()
    tfidf_scores = tfidf_matrix.sum(axis=1)

    max_pos = len(sentences)
    position_scores = np.array([1 - (i / max_pos) for i in range(max_pos)])

    final_scores = tfidf_scores + position_scores
    return final_scores

# Формування самері на основі оцінок
def improved_summary(sentences, scores, max_sentences=5):
    top_indices = np.argsort(scores)[-max_sentences:][::-1]
    top_indices_sorted = sorted(top_indices)
    return " ".join([sentences[i] for i in top_indices_sorted])

# отримання RTE ознак
def rte_features(rtepair):
    extractor = nltk.RTEFeatureExtractor(rtepair)
    return {
        'text_words': extractor.text_words,
        'hyp_words': extractor.hyp_words,
        'word_overlap': len(extractor.overlap('word')),
        'ne_overlap': len(extractor.overlap('ne')),
        'hyp_extra_word': extractor.hyp_extra('word'),
        'hyp_extra_ne': extractor.hyp_extra('ne')
    }

#Головне вікно
root = tk.Tk()
root.title("Text Summarizer")
root.geometry("900x650")

# Відкриття файлу та автоматичне самерювання
def open_file():
    filepath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if not filepath:
        return
    with open(filepath, 'r', encoding='utf-8') as file:
        text = file.read()
    text_input.delete(1.0, tk.END)
    text_input.insert(tk.END, text)
    summarize_text()  # автоматично запускає після відкриття

# Основна функція для створення резюме
def summarize_text(*args):
    text = text_input.get(1.0, tk.END).strip()
    if not text:
        return

    sentences = sent_tokenize(text)
    if not sentences:
        messagebox.showerror("Помилка", "Текст не містить речень.")
        return

    # Кількість речень у підсумку з повзунка
    max_sentences = sentence_slider.get()
    max_sentences = min(max_sentences, len(sentences))

    scores = improved_score_sentences(sentences)
    summary = improved_summary(sentences, scores, max_sentences)

    # Обчислення відсотку стиснення
    original_wc = len(word_tokenize(text))
    summary_wc = len(word_tokenize(summary))
    compression_percent = 100 * (1 - summary_wc / original_wc)

    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, f"=== Резюме ({max_sentences} речень) ===\n")
    result_text.insert(tk.END, summary + "\n\n")
    result_text.insert(tk.END, f"🔻 Стиснення: {compression_percent:.2f}% "
                               f"({summary_wc} з {original_wc} слів)")

def show_entailments():
    entails = wn.synset('pronounce.v.01').entailments()
    messagebox.showinfo("Entailments", f"pronounce.v.01 entailments:\n{entails}")

def show_rte_features():
    rtepair = nltk.corpus.rte.pairs(['rte3_dev.xml'])[13]
    features = rte_features(rtepair)
    info = (
        f"Ключові слова з тексту: {features['text_words']}\n"
        f"Ключові слова з гіпотези: {features['hyp_words']}\n"
        f"Перекриття (слова): {features['word_overlap']}\n"
        f"Перекриття (NE): {features['ne_overlap']}\n"
        f"Зайві слова в гіпотезі: {features['hyp_extra_word']}\n"
        f"Зайві NE в гіпотезі: {features['hyp_extra_ne']}\n"
    )
    messagebox.showinfo("RTE Features", info)

main_canvas = tk.Canvas(root, borderwidth=0, highlightthickness=0)
scrollbar = tk.Scrollbar(root, orient="vertical", command=main_canvas.yview)
scrollable_frame = tk.Frame(main_canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all"))
)

window_id = main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="frame")
main_canvas.bind("<Configure>", lambda e: main_canvas.itemconfig("frame", width=e.width))

main_canvas.configure(yscrollcommand=scrollbar.set)
main_canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# === Віджети ТЕПЕР додаємо у scrollable_frame ===
btn_load = tk.Button(scrollable_frame, text="📂 Відкрити текстовий файл", command=open_file)
btn_load.pack(pady=10)

text_input = scrolledtext.ScrolledText(scrollable_frame, height=10, wrap=tk.WORD, font=("Arial", 12))
text_input.pack(fill='both', expand=False, padx=10, pady=5)

sentence_slider = tk.Scale(scrollable_frame, from_=1, to=20, orient=tk.HORIZONTAL, label="Кількість речень у резюме")
sentence_slider.set(5)
sentence_slider.pack(pady=5)
sentence_slider.bind("<ButtonRelease-1>", summarize_text)

result_text = scrolledtext.ScrolledText(scrollable_frame, wrap=tk.WORD, font=("Arial", 12))
result_text.pack(expand=True, fill='both', padx=10, pady=10)

btn_entail = tk.Button(scrollable_frame, text="🔎 Показати Entailments WordNet", command=show_entailments)
btn_entail.pack(pady=5)

btn_rte = tk.Button(scrollable_frame, text="📊 Показати RTE ознаки", command=show_rte_features)
btn_rte.pack(pady=5)

root.mainloop()