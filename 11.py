import tkinter as tk
from tkinter import messagebox
import re


# Функція сегментації слова на основі його частини мови
def segment_word(word, part_of_speech):
    word = word.lower()  # Перетворюємо слово в нижній регістр для коректної обробки

    # Обробка для іменників
    if part_of_speech == "Іменник":
        if len(word) > 6:
            if len(word) > 7:
                return f"{word[:-3]}-{word[-3:]}\n/-***/ Сегментується О.в. мн.(-ами)."
            else:
                return f"{word[:-2]}-{word[-2:]}\n/-**/ Сегментуються О.в. одн.(-ою), Д.в. мн.(-ам), М.в.(-ах) мн.."
        else:
            if word == "доньок":
                return f"{word}-0\nПозначається нульова флексія в Р.в. та Зн.в. множини."
            else:
                return (f"{word[:-1]}-{word[-1:]}\n/-*/ Cегментуються Н.в. одн.(-а), Р.в. одн.(-и), Д.в. та М.в. одн."
                        f"(-і), Зн.в. одн.(-у), Кл.в. одн.(-о), Н.в. та Кл.в. мн.(-и).")

    # Обробка для прикметників
    elif part_of_speech == "Прикметник":
        if len(word) > 5:
            if len(word) > 6:
                return (f"{word[:-3]}-{word[-3:]}\n/-***/ Сегментуються Р.в. та Зн.в. чол.р. одн.(-ого), Д.в. та М.в. "
                        f"чол.р. одн.(-ому), Р.в. сер.р. одн.(-ого), Д.в. та М.в. сер.р. одн.(-ому), О.в. мн.(-ими).")
            else:
                return (f"{word[:-2]}-{word[-2:]}\n/-**/ Сегментуються Н.в. та Зн.в. чол.р. одн.(-ий), О.в. чол.р. одн."
                        f"(-им), М.в. чол.р. одн.(-ім), Р.в. жін.р. одн.(-ої), Д.в. та М.в. жін.р. одн.(-ій), О.в. "
                        f"жін.р. одн.(-ою), О.в. сер.р. одн.(-им), М.в. сер.р. одн.(-ім), Р.в., Зн.в. та М.в. мн.(-их)"
                        f", Д.в. мн.(-им).")
        else:
            return (f"{word[:-1]}-{word[-1:]}\n/-*/ Сегментуються Н.в. жін.р. одн.(-а), Зн.в. жін.р. одн.(-у), Н.в.та "
                    f"Зн.в. сер.р. одн.(-е), Н.в. та Зн.в. множини (-і).")

    # Обробка для дієслів
    elif part_of_speech == "Дієслово":
        if len(word) > 5:
            if word.endswith("в"):
                return (f"{word[:-1]}-{word[-1:]}\n/-*/ Сегментуються 1 ос. од. теп. часу(-ю), 3 ос. од. теп. часу(-є),"
                        f" чол.р. од. мин. часу(-в-).")
            else:
                if len(word) > 11:
                    return (f"{word[:-6]}-{word[-6:-4]}-{word[-4:-3]}-{word[-3:]}\n/-**-*-***/ Сегментуються 1-3 ос. "
                            f"мн. майб. часу.")
                elif len(word) > 10:
                    return (f"{word[:-5]}-{word[-5:-3]}-{word[-3:-2]}-{word[-2:]}\n/-**-*-**/ Сегментуються 1-2 ос. "
                            f"одн. та мн. майб. часу.")
                elif len(word) > 8:
                    return (f"{word[:-4]}-{word[-4:-2]}-{word[-2:-1]}-{word[-1:]}\n/-**-*-*/ Сегментуються 1-3 ос. од."
                            f" майб. часу.")
                elif len(word) > 7:
                    return f"{word[:-2]}-{word[-2:-1]}-{word[-1:]}\n/-*-*/ Сегментуються минулий час (л-а, л-о, л-и)."
                elif len(word) > 6 and not "й" in word:
                    return f"{word[:-3]}-{word[-3:]}\n/-***/ Сегментуються 1-3 ос. мн. теп. часу."
                elif len(word) > 5 and not "й" in word:
                    return f"{word[:-2]}-{word[-2:]}\n/-**/ Сегментуються 1-2 ос. одн. та мн. теп. часу"
                elif "й" in word:
                    return f"{word[:-2]}-{word[-2:]}\n/-**/ Сегментуються теп. час та наказовий спосіб."
                else:
                    return f"{word[:-3]}-{word[-3:]}\n/-***/ Сегментуються 1-2 ос. одн. та мн. наказового способу."
        else:
            if "й" in word:
                return f"{word}-0\nПозначається нульова флексія 2 ос. од. наказ.способу."
            else:
                return (f"{word[:-1]}-{word[-1:]}\n/-*/ Сегментуються 1 ос. од. теп. часу(-ю), 3 ос. од. теп. часу(-є),"
                        f" чол.р. од. мин. часу(-в-).")

    return "Невідома частина мови або помилка."


# Функція для запуску графічного інтерфейсу
def run_interface():
    def on_submit():
        # Отримуємо введене слово та вибрану частину мови
        word = entry_word.get().strip()
        pos = pos_var.get()

        # Перевірка на коректність введеного слова
        if not word or re.search(r"[a-zA-Z0-9_]", word):
            messagebox.showwarning("Помилка", "Будь ласка, введіть коректне українське слово (без латиниці).")
        else:
            # Викликаємо функцію для сегментації слова
            result = segment_word(word, pos)
            # Очищаємо текстове поле та виводимо результат
            output_text.delete("1.0", tk.END)
            output_text.insert(tk.END, result)

    # Створюємо основне вікно
    root = tk.Tk()
    root.title("Сегментатор слів української мови")
    root.resizable(False, False)

    # Основний контейнер для віджетів
    main_frame = tk.Frame(root, padx=15, pady=15)
    main_frame.pack()

    # Частина мови
    tk.Label(main_frame, text="Виберіть частину мови:", anchor="w").grid(row=0, column=0, sticky="w", pady=5)
    pos_var = tk.StringVar(value="Іменник")
    pos_menu = tk.OptionMenu(main_frame, pos_var, "Іменник", "Прикметник", "Дієслово")
    pos_menu.config(width=20, anchor="w", justify="left")  # Вирівнювання ліворуч
    pos_menu.grid(row=0, column=1, pady=5)  # Притискаємо до лівого краю

    # Введення слова
    tk.Label(main_frame, text="Введіть слово:", anchor="w").grid(row=1, column=0, sticky="w", pady=5)
    entry_word = tk.Entry(main_frame, width=26)
    entry_word.grid(row=1, column=1, pady=5)

    # Кнопка для сегментації
    submit_btn = tk.Button(main_frame, text="Сегментувати", command=on_submit, width=20)
    submit_btn.grid(row=2, column=0, columnspan=2, pady=10)

    # Поле для виведення результату
    output_text = tk.Text(main_frame, width=40, height=10, wrap="word", font=("Courier", 10))
    output_text.grid(row=3, column=0, columnspan=2, pady=(0, 10))

    # Запуск інтерфейсу
    root.mainloop()


# Запуск програми
run_interface()
