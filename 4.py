import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import sqlite3
import re
from tokenize_uk import tokenize_words
import pymorphy3

def read_and_preprocess(file_path):
    with open(file_path, encoding="utf-8") as file:
        text = file.read()
    exceptions = ['вул.', 'ін.', 'ІВВ', 'матер.', 'наук.', 'Наук.', 'ред.', 'проф.', 'ISBN', 'І.', 'Є.', 'р3',
                  '«Green Ways»', 'http://volynrada.gov.ua/news/yak-rozvivali-turizm-na-volini-v-ramkakh-regionalno'
                                  'yi-programi', 'НТУ', 'УДК', 'ББК', 'М.', 'АНВО', 'В.', 'УПЦ', 'Г.', 'О.', 'Л.', 'Ю.',
                  'Н.', 'М.', 'В.', 'Т.', 'К.', 'Я.', 'Л.Ю.', 'РВВ', 'ЛНТУ', 'Т.П.', 'С.', 'грн.', 'рр4', 'тис.',
                  'ПДВ', 'рис.', 'табл.', 'Рис.', 'США', 'т.п.', 'А.', 'И.', 'ГРК', 'КНТЕУ', '2-ге', 'вид.',
                  'вищ.', 'навч.', 'закл.', 'перероб.', 'допов.', 'Х.', 'Й.', '1м', 'ЗІЛ', '«Бичок»', 'посіб.',
                  'нац.', 'торг.-екон.', 'ун-т', 'кв.', '80-х', 'РАГСу', 'РАГС', 'млн.', 'обл.', 'Е.', 'Д.',
                  'СПб.', 'Изд-во', 'т.д.', 'ім.', 'ЛНУ', 'Вип.', 'т.ч.', 'П.', 'ЗАТ', 'Ф.', 'Ред.',
                  'кол.', 'НАУ', 'км.', 'г/л', 'куб.', 'м/год.', 'г/дм3', 'ПЗФ', 'з/п', 'р-ну', 'сер.',
                  'АСУ', 'ІС', 'ІДС', 'РП', 'Ін-т', 'журн.', 'всеукр.', 'Всеукр.', 'д-ра', '-ти', 'іОС', 'ДВНЗ',
                  'м/год.', 'г/дм3', 'ISO/IEC', 'ІІІ', 'ИТД', '«АртДжазКооперейшн»', 'Инфра-М', 'НДІ',
                  '"Укрпрофоздоровниця"', '"Тамед"']
    text = re.sub(r'\b(?:[А-ЯЁ]+\.)+[А-ЯЁ]+\b|\b[А-ЯЁ]+\.\b', '', text)
    for exception in exceptions:
        text = text.replace(exception, '')
    text = text.lower()
    text_without_digits = re.sub(r"\d", "", text)
    filtered_text = re.sub(r"[^\w\s'-]", "", text_without_digits)  # видаляє всі символи, крім букв, цифр, пробілів,
    # апострофів і тире.
    return filtered_text

def remove_roman_numerals(text):
    return re.sub(r'\b[ivxlcdm]+\b', '', text)

def count_and_divide(tokens, exceptions, max_tokens=20000):
    edited_list = []
    count = 0
    for token in tokens:
        if token not in exceptions:
            count += 1
            edited_list.append(token)
        if count == max_tokens:
            break
    return edited_list, count

def divide_on_samples(edited_list, sample_dict, sample_num):
    sample_list = []
    for word_form in edited_list:
        if word_form not in sample_dict:
            # Ініціалізуємо словоформу з нулями для 20 підсемплів
            sample_dict[word_form] = [word_form] + [0] * 20
        # Перевіряємо, чи є ще місце для нового підсемплу
        if len(sample_dict[word_form]) <= sample_num:
            # Додаємо нулі, якщо потрібно
            sample_dict[word_form] += [0] * (sample_num - len(sample_dict[word_form]) + 1)
        # Збільшуємо лічильник для відповідного підсемплу
        sample_dict[word_form][sample_num] += 1
        sample_list.append(word_form)
    return sample_list

def create_and_fill_databases(file1, file2):
    sample_1_dict = {}
    sample_2_dict = {}

    file_path_1 = file1
    text_1 = read_and_preprocess(file_path_1)
    text_without_roman_1 = remove_roman_numerals(text_1)
    tokens_regex_1 = re.findall(r"\b(?:[А-ЯЁа-яёіїєґҐ']+(?:-|—)?(?:'[А-ЯЁа-яёіїєґҐ]+)?)+\b", text_without_roman_1)
    tokens_tokenize_uk_1 = list(tokenize_words(text_without_roman_1))
    splitted_1 = tokens_regex_1 + tokens_tokenize_uk_1
    splitted_1 = [token for token in splitted_1 if token]
    additional_exceptions = ['л', 'с', 'м', '‘', 'га', 'км', 'кг', 'од', 'ил', 'ст', 'р', 'ок', 'осм', 'ос', "'", 'іт',
                             'інтернет-конф', 'смт', 'гр', 'ла', 'прикді', 'придніпровя', 'хіх']
    edited_list_1, count_1 = count_and_divide(splitted_1 + additional_exceptions, additional_exceptions)
    while count_1 < 20000:
        remaining_text_1 = read_and_preprocess(file_path_1)
        remaining_tokens_regex_1 = re.findall(r"\b(?:[А-ЯЁа-яёіїєґҐ']+(?:-|—)?(?:'[А-ЯЁа-яёіїєґҐ]+)?)+\b", remaining_text_1)
        remaining_tokens_tokenize_uk_1 = list(tokenize_words(remaining_text_1))
        remaining_splitted_1 = remaining_tokens_regex_1 + remaining_tokens_tokenize_uk_1
        remaining_splitted_1 = [token for token in remaining_splitted_1 if token]
        edited_list_1 = divide_on_samples(edited_list_1 + remaining_splitted_1 + additional_exceptions, sample_1_dict, 1)
        count_1 = len(edited_list_1)

    file_path_2 = file2
    text_2 = read_and_preprocess(file_path_2)
    text_without_roman_2 = remove_roman_numerals(text_2)
    tokens_regex_2 = re.findall(r"\b(?:[А-ЯЁа-яёіїєґҐ']+(?:-|—)?(?:'[А-ЯЁа-яёіїєґҐ]+)?)+\b", text_without_roman_2)
    tokens_tokenize_uk_2 = list(tokenize_words(text_without_roman_2))
    splitted_2 = tokens_regex_2 + tokens_tokenize_uk_2
    splitted_2 = [token for token in splitted_2 if token]
    edited_list_2, count_2 = count_and_divide(splitted_2 + additional_exceptions, additional_exceptions)
    while count_2 < 20000:
        remaining_text_2 = read_and_preprocess(file_path_2)
        remaining_tokens_regex_2 = re.findall(r"\b(?:[А-ЯЁа-яёіїєґҐ']+(?:-|—)?(?:'[А-ЯЁа-яёіїєґҐ]+)?)+\b", remaining_text_2)
        remaining_tokens_tokenize_uk_2 = list(tokenize_words(remaining_text_2))
        remaining_splitted_2 = remaining_tokens_regex_2 + remaining_tokens_tokenize_uk_2
        remaining_splitted_2 = [token for token in remaining_splitted_2 if token]
        edited_list_2 = divide_on_samples(edited_list_2 + remaining_splitted_2 + additional_exceptions, sample_2_dict, 2)
        count_2 = len(edited_list_2)

    sample_1_dict = {}
    sample_2_dict = {}

    for i in range(20):
        sub_sample_start = i * 1000
        sub_sample_end = (i + 1) * 1000
        sub_sample_1 = edited_list_1[sub_sample_start:sub_sample_end]
        sub_sample_counts = {}
        for word_form in sub_sample_1:
            sub_sample_counts[word_form] = sub_sample_counts.get(word_form, 0) + 1
        for word_form, count in sub_sample_counts.items():
            if word_form not in sample_1_dict:
                sample_1_dict[word_form] = [word_form] + [0] * 20
            sample_1_dict[word_form][i + 1] = count

    # Прокручуємо 20 циклів для другого файлу
    for i in range(20):
        # Витягуємо наступні 1000 слів зі списку edited_list_2
        sub_sample_start = i * 1000
        sub_sample_end = (i + 1) * 1000
        sub_sample_2 = edited_list_2[sub_sample_start:sub_sample_end]
        # Підрахуємо випадки появи кожної словоформи у підвибірці
        sub_sample_counts = {}
        for word_form in sub_sample_2:
            sub_sample_counts[word_form] = sub_sample_counts.get(word_form, 0) + 1
        # Оновлюємо sample_2_dict підрахунками для поточної підвибірки
        for word_form, count in sub_sample_counts.items():
            if word_form not in sample_2_dict:
                sample_2_dict[word_form] = [word_form] + [0] * 20  # Ініціалізація нулями для 20 підзразків
            # Оновлюємо кількість для поточної підвибірки
            sample_2_dict[word_form][i + 1] = count

    # Отримання списку значень (values) зі словника
    values1 = list(sample_1_dict.values())
    # Додаємо загальну частоту до кожного підсписку в values1
    for sublist in values1:
        sublist.insert(1, sum(sublist[1:]))  # Вставляємо загальну частоту на другу позицію
    # Сортуємо за загальною частотою в порядку спадання
    values1_ordered = sorted(values1, key=lambda x: x[1], reverse=True)
    # Отримуємо спискок значень (values) зі словника для другої вибірки
    values2 = list(sample_2_dict.values())
    # Додаємо загальну частоту до кожного підсписку в values2
    for sublist in values2:
        sublist.insert(1, sum(sublist[1:]))  # Вставте загальну частоту на другу позицію
    # Сортуємо за загальною частотою в порядку спадання
    values2_ordered = sorted(values2, key=lambda x: x[1], reverse=True)
    # Ініціалізуємо pymorphy3 для української мови
    morph = pymorphy3.MorphAnalyzer(lang='uk')
    conn = sqlite3.connect('sample_1.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS част_словоформ
                      (словоформа TEXT PRIMARY KEY NOT NULL,
                      загальна_частота INTEGER,
                      підв_1 INTEGER,
                      підв_2 INTEGER,
                      підв_3 INTEGER,
                      підв_4 INTEGER,
                      підв_5 INTEGER,
                      підв_6 INTEGER,
                      підв_7 INTEGER,
                      підв_8 INTEGER,
                      підв_9 INTEGER,
                      підв_10 INTEGER,
                      підв_11 INTEGER,
                      підв_12 INTEGER,
                      підв_13 INTEGER,
                      підв_14 INTEGER,
                      підв_15 INTEGER,
                      підв_16 INTEGER,
                      підв_17 INTEGER,
                      підв_18 INTEGER,
                      підв_19 INTEGER,
                      підв_20 INTEGER)
     ''')
    # Додаємо дані з values1_ordered до таблиці ЧС_словоформ
    for i in values1_ordered:
        cursor.execute("""
            INSERT INTO част_словоформ VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, i)
    conn.commit()
    conn.close()
    conn = sqlite3.connect('sample_2.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS част_словоформ
                      (словоформа TEXT PRIMARY KEY NOT NULL,
                      загальна_частота INTEGER,
                      підв_1 INTEGER,
                      підв_2 INTEGER,
                      підв_3 INTEGER,
                      підв_4 INTEGER,
                      підв_5 INTEGER,
                      підв_6 INTEGER,
                      підв_7 INTEGER,
                      підв_8 INTEGER,
                      підв_9 INTEGER,
                      підв_10 INTEGER,
                      підв_11 INTEGER,
                      підв_12 INTEGER,
                      підв_13 INTEGER,
                      підв_14 INTEGER,
                      підв_15 INTEGER,
                      підв_16 INTEGER,
                      підв_17 INTEGER,
                      підв_18 INTEGER,
                      підв_19 INTEGER,
                      підв_20 INTEGER)
     ''')
    # Додаємр дані з values2_ordered до нової таблиці част_словоформ
    for i in values2_ordered:
        cursor.execute("""
            INSERT INTO част_словоформ VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, i)
    conn.commit()
    conn.close()

    conn = sqlite3.connect('sample_1.db')
    cursor = conn.cursor()

    def create_table():
        cursor.execute('''CREATE TABLE IF NOT EXISTS част_мови
            (частина_мови TEXT PRIMARY KEY NOT NULL,
             загальна_частота INTEGER,
             підв_1 INTEGER,
             підв_2 INTEGER,
             підв_3 INTEGER,
             підв_4 INTEGER,
             підв_5 INTEGER,
             підв_6 INTEGER,
             підв_7 INTEGER,
             підв_8 INTEGER,
             підв_9 INTEGER,
             підв_10 INTEGER,
             підв_11 INTEGER,
             підв_12 INTEGER,
             підв_13 INTEGER,
             підв_14 INTEGER,
             підв_15 INTEGER,
             підв_16 INTEGER,
             підв_17 INTEGER,
             підв_18 INTEGER,
             підв_19 INTEGER,
             підв_20 INTEGER)
        ''')
    create_table()

    def count_parts_of_speech(sample_dict):
        part_of_speech_counts = {}
        for word_form, counts_per_subsample in sample_dict.items():
            for i, count in enumerate(counts_per_subsample[1:], start=1):
                # Визначення частини мови за допомогою pymorphy3
                parsed_word = morph.parse(word_form)[0]
                part_of_speech = parsed_word.tag.POS
                # Перевірка, чи частина мови не є None перед оновленням лічильників
                if part_of_speech is not None:
                    # Оновлення лічильників у словнику part_of_speech_counts
                    if part_of_speech not in part_of_speech_counts:
                        part_of_speech_counts[part_of_speech] = [part_of_speech] + [0] * max(20, i)
                    while len(part_of_speech_counts[part_of_speech]) <= i:
                        part_of_speech_counts[part_of_speech].append(0)
                    part_of_speech_counts[part_of_speech][i] += count
        return part_of_speech_counts

    # Рахуємо частини мови за кожним зразком
    parts_of_speech_1 = count_parts_of_speech(sample_1_dict)

    def insert_data_into_table(sample_name, part_of_speech_counts):
        # Вставляємо дані в таблицю
        for values in part_of_speech_counts.values():
            cursor.execute(f'''
                INSERT INTO {sample_name} VALUES {tuple(values)}
            ''')

    # Викликаємо функцію insert_data_into_table, щоб вставити дані в таблицю
    insert_data_into_table('част_мови', parts_of_speech_1)
    cursor.execute('''SELECT * FROM част_мови ORDER BY загальна_частота DESC''')
    sorted_data = cursor.fetchall()
    cursor.execute('''DELETE FROM част_мови''')
    # Вставка відсортованиз даних
    for row in sorted_data:
        cursor.execute('''INSERT INTO част_мови VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', row)
    conn.commit()
    conn.close()

    conn = sqlite3.connect('sample_2.db')
    cursor = conn.cursor()
    # Визначаємо функцію для створення таблиці для заданого зразка
    def create_table():
        cursor.execute('''CREATE TABLE IF NOT EXISTS част_мови
            (част_мови TEXT,
             загальна_частота INTEGER,
             підв_1 INTEGER,
             підв_2 INTEGER,
             підв_3 INTEGER,
             підв_4 INTEGER,
             підв_5 INTEGER,
             підв_6 INTEGER,
             підв_7 INTEGER,
             підв_8 INTEGER,
             підв_9 INTEGER,
             підв_10 INTEGER,
             підв_11 INTEGER,
             підв_12 INTEGER,
             підв_13 INTEGER,
             підв_14 INTEGER,
             підв_15 INTEGER,
             підв_16 INTEGER,
             підв_17 INTEGER,
             підв_18 INTEGER,
             підв_19 INTEGER,
            підв_20 INTEGER)
        ''')
    create_table()

    def count_parts_of_speech(sample_dict):
        part_of_speech_counts = {}
        for word_form, counts_per_subsample in sample_dict.items():
            for i, count in enumerate(counts_per_subsample[1:], start=1):
                # Визначення частини мови за допомогою pymorphy3
                parsed_word = morph.parse(word_form)[0]
                part_of_speech = parsed_word.tag.POS
                #          Перевірка, чи частина мови не є None перед оновленням лічильників
                if part_of_speech is not None:
                    # Оновлення лічильників у словнику part_of_speech_counts
                    if part_of_speech not in part_of_speech_counts:
                        part_of_speech_counts[part_of_speech] = [part_of_speech] + [0] * max(20, i)
                    #                # Переконання, що довжина списку достатня
                    while len(part_of_speech_counts[part_of_speech]) <= i:
                        part_of_speech_counts[part_of_speech].append(0)
                    part_of_speech_counts[part_of_speech][i] += count
        return part_of_speech_counts

    # Рахуємо частини мови за кожним зразком
    parts_of_speech_2 = count_parts_of_speech(sample_2_dict)

    def insert_data_into_table(sample_name, part_of_speech_counts):
        #  Вставляємо дані в таблицю
        for values in part_of_speech_counts.values():
            cursor.execute(f'''
                INSERT INTO {sample_name} VALUES {tuple(values)}
            ''')
    # Викликаємо функцію insert_data_into_table, щоб вставити дані в таблицю
    insert_data_into_table('част_мови', parts_of_speech_2)
    # Запрос для відсортування таблиці част_мови за спаданням загальної частоти
    cursor.execute('''SELECT * FROM част_мови ORDER BY загальна_частота DESC''')
    sorted_data = cursor.fetchall()
    cursor.execute('''DELETE FROM част_мови''')
    # Вставка відсортованиз даних
    for row in sorted_data:
        cursor.execute('''INSERT INTO част_мови VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', row)
    conn.commit()
    conn.close()

    conn = sqlite3.connect('sample_1.db')
    cursor = conn.cursor()

    # Створення таблиці ЧС_лем
    cursor.execute('''CREATE TABLE IF NOT EXISTS ЧС_лем
                      (лема TEXT,
                      загальна_частота INTEGER,
                      підв_1 INTEGER,
                      підв_2 INTEGER,
                      підв_3 INTEGER,
                      підв_4 INTEGER,
                      підв_5 INTEGER,
                      підв_6 INTEGER,
                      підв_7 INTEGER,
                      підв_8 INTEGER,
                      підв_9 INTEGER,
                      підв_10 INTEGER,
                      підв_11 INTEGER,
                      підв_12 INTEGER,
                      підв_13 INTEGER,
                      підв_14 INTEGER,
                      підв_15 INTEGER,
                      підв_16 INTEGER,
                      підв_17 INTEGER,
                      підв_18 INTEGER,
                      підв_19 INTEGER,
                      підв_20 INTEGER)
     ''')

    def count_lemmas(sample_dict):
        lemma_counts = {}
        for word_form, counts_per_subsample in sample_dict.items():
            for i, count in enumerate(counts_per_subsample[1:], start=1):  # використовується функція enumerate, щоб
                #        отримати індекс (i) та відповідну частоту (count) для кожної субвибірки, починаючи з першої
                #        (індекс 1).
                # Лематизація слова
                lemma = morph.parse(word_form)[0].normal_form
                # Оновлення лічильника в словникові лем
                if lemma not in lemma_counts:
                    lemma_counts[lemma] = [lemma] + [0] * max(20, i)
                # Переконаємось, що довжина списку достатня
                while len(lemma_counts[lemma]) <= i:
                    lemma_counts[lemma].append(0)
                lemma_counts[lemma][i] += count
        return lemma_counts


    lemmas_1 = count_lemmas(sample_1_dict)

    for values in lemmas_1.values():
        cursor.execute(f'''
            INSERT INTO ЧС_лем VALUES {tuple(values)}
        ''')

    # Запит для відсортування таблиці ЧС_лем за спаданням загальної частоти
    cursor.execute('''SELECT * FROM ЧС_лем ORDER BY загальна_частота DESC''')
    sorted_data = cursor.fetchall()
    cursor.execute('''DELETE FROM ЧС_лем''')
    # Вставка відсортованиз даних
    for row in sorted_data:
        cursor.execute('''INSERT INTO ЧС_лем VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', row)
    conn.commit()
    conn.close()

    conn = sqlite3.connect('sample_2.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ЧС_лем
                      (лема TEXT,
                      загальна_частота INTEGER,
                      підв_1 INTEGER,
                      підв_2 INTEGER,
                      підв_3 INTEGER,
                      підв_4 INTEGER,
                      підв_5 INTEGER,
                      підв_6 INTEGER,
                      підв_7 INTEGER,
                      підв_8 INTEGER,
                      підв_9 INTEGER,
                      підв_10 INTEGER,
                      підв_11 INTEGER,
                      підв_12 INTEGER,
                      підв_13 INTEGER,
                      підв_14 INTEGER,
                      підв_15 INTEGER,
                      підв_16 INTEGER,
                      підв_17 INTEGER,
                      підв_18 INTEGER,
                      підв_19 INTEGER,
                      підв_20 INTEGER)
     ''')
    conn.commit()
    conn.close()

    def count_lemmas(sample_dict):
        lemma_counts = {}
        for word_form, counts_per_subsample in sample_dict.items():
            for i, count in enumerate(counts_per_subsample[1:], start=1):
                lemma = morph.parse(word_form)[0].normal_form
                if lemma not in lemma_counts:
                    lemma_counts[lemma] = [lemma] + [0] * max(20, i)
                while len(lemma_counts[lemma]) <= i:
                    lemma_counts[lemma].append(0)
                lemma_counts[lemma][i] += count
        return lemma_counts

    lemmas_2 = count_lemmas(sample_2_dict)

    conn = sqlite3.connect('sample_2.db')
    cursor = conn.cursor()
    for values in lemmas_2.values():
        cursor.execute(f'''
            INSERT INTO ЧС_лем VALUES {tuple(values)}
        ''')

    # Запит для відсортування таблиці ЧС_лем за спаданням загальної частоти
    cursor.execute('''SELECT * FROM ЧС_лем ORDER BY загальна_частота DESC''')
    sorted_data = cursor.fetchall()
    cursor.execute('''DELETE FROM ЧС_лем''')
    # Вставка відсортованиз даних
    for row in sorted_data:
        cursor.execute('''INSERT INTO ЧС_лем VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', row)
    conn.commit()
    conn.close()

    conn = sqlite3.connect('sample_1.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS зведена_таблиця
                      (word_id INTEGER PRIMARY KEY ,
                      словоформа TEXT,
                      лема TEXT,
                      частина_мови TEXT,
                      загальна_частота INTEGER,
                      підв_1 INTEGER,
                      підв_2 INTEGER,
                      підв_3 INTEGER,
                      підв_4 INTEGER,
                      підв_5 INTEGER,
                      підв_6 INTEGER,
                      підв_7 INTEGER,
                      підв_8 INTEGER,
                      підв_9 INTEGER,
                      підв_10 INTEGER,
                      підв_11 INTEGER,
                      підв_12 INTEGER,
                      підв_13 INTEGER,
                      підв_14 INTEGER,
                      підв_15 INTEGER,
                      підв_16 INTEGER,
                      підв_17 INTEGER,
                      підв_18 INTEGER,
                      підв_19 INTEGER,
                      підв_20 INTEGER)
    ''')

    full_table = []
    for row in values1_ordered:
        row_new = [
            row[0],
            morph.parse(row[0])[0].normal_form, # Визначаємо леми за допомогою бібліотеки pymorphy2,
            morph.parse(row[0])[0].tag.POS,     # та частину мови
        ]
        row_new.extend(row[1:]) # додаємо решту стовпчиків із частотами словоформ в рядок
        full_table.append(row_new) # додаємо отриманий рядок в список

    for row in full_table:
        cursor.execute("""INSERT OR IGNORE INTO зведена_таблиця(
                      словоформа,
                      лема,
                      частина_мови,
                      загальна_частота,
                      підв_1,
                      підв_2,
                      підв_3,
                      підв_4,
                      підв_5,
                      підв_6,
                      підв_7,
                      підв_8,
                      підв_9,
                      підв_10,
                      підв_11,
                      підв_12,
                      підв_13,
                      підв_14,
                      підв_15,
                      підв_16,
                      підв_17,
                      підв_18,
                      підв_19,
                      підв_20)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", row)

    conn.commit()
    conn.close()

    conn = sqlite3.connect('sample_2.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS зведена_таблиця
                      (word_id INTEGER PRIMARY KEY ,
                      словоформа TEXT,
                      лема TEXT,
                      частина_мови TEXT,
                      загальна_частота INTEGER,
                      підв_1 INTEGER,
                      підв_2 INTEGER,
                      підв_3 INTEGER,
                      підв_4 INTEGER,
                      підв_5 INTEGER,
                      підв_6 INTEGER,
                      підв_7 INTEGER,
                      підв_8 INTEGER,
                      підв_9 INTEGER,
                      підв_10 INTEGER,
                      підв_11 INTEGER,
                      підв_12 INTEGER,
                      підв_13 INTEGER,
                      підв_14 INTEGER,
                      підв_15 INTEGER,
                      підв_16 INTEGER,
                      підв_17 INTEGER,
                      підв_18 INTEGER,
                      підв_19 INTEGER,
                      підв_20 INTEGER)
    ''')

    full_table = []
    for row in values2_ordered:
        row_new = [
            row[0],
            morph.parse(row[0])[0].normal_form, # Визначаємо леми за допомогою бібліотеки pymorphy2,
            morph.parse(row[0])[0].tag.POS,     # та частину мови
        ]
        row_new.extend(row[1:]) # додаємо решту стовпчиків із частотами словоформ в рядок
        full_table.append(row_new) # додаємо отриманий рядок в список

    for row in full_table:
        cursor.execute("""INSERT OR IGNORE INTO зведена_таблиця(
                      словоформа,
                      лема,
                      частина_мови,
                      загальна_частота,
                      підв_1,
                      підв_2,
                      підв_3,
                      підв_4,
                      підв_5,
                      підв_6,
                      підв_7,
                      підв_8,
                      підв_9,
                      підв_10,
                      підв_11,
                      підв_12,
                      підв_13,
                      підв_14,
                      підв_15,
                      підв_16,
                      підв_17,
                      підв_18,
                      підв_19,
                      підв_20)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", row)

    conn.commit()
    conn.close()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Частотний аналізатор текстів")
        self.file1_path = ""
        self.file2_path = ""

        # Фрейм для кнопок
        self.button_frame = tk.Frame(root)
        self.button_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        # Кнопки з вирівнюванням ліворуч
        tk.Button(self.button_frame, text="Обрати перший файл", command=self.select_file1).pack(fill=tk.X, pady=5)
        tk.Button(self.button_frame, text="Обрати другий файл", command=self.select_file2).pack(fill=tk.X, pady=5)
        tk.Button(self.button_frame, text="Запустити обробку", command=self.start_processing).pack(fill=tk.X, pady=10)

        self.status_label = tk.Label(self.button_frame, text="", fg="blue")
        self.status_label.pack(fill=tk.X, pady=5)

        tk.Button(self.button_frame, text="Показати зведену таблицю", command=self.show_combined).pack(fill=tk.X,
                                                                                                       pady=5)
        tk.Button(self.button_frame, text="Показати частотний словник лем", command=self.show_lemmas).pack(fill=tk.X,
                                                                                                           pady=5)
        tk.Button(self.button_frame, text="Показати частотний словник словоформ", command=self.show_wordforms).pack(
            fill=tk.X, pady=5)
        tk.Button(self.button_frame, text="Показати частотний словник частин мови", command=self.show_pos).pack(
            fill=tk.X, pady=5)

        # Фрейм для дерева (таблиці)
        self.tree_frame = tk.Frame(root)
        self.tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Використання grid всередині frame
        self.tree_frame.grid_rowconfigure(0, weight=1)
        self.tree_frame.grid_columnconfigure(0, weight=1)

        self.tree = ttk.Treeview(self.tree_frame)
        self.tree.grid(row=0, column=0, sticky="nsew")

        # Вертикальний скрол
        self.scrollbar_y = tk.Scrollbar(self.tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.scrollbar_y.grid(row=0, column=1, sticky="ns")
        self.tree.config(yscrollcommand=self.scrollbar_y.set)

        # Горизонтальний скрол
        self.scrollbar_x = tk.Scrollbar(self.tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.scrollbar_x.grid(row=1, column=0, sticky="ew")
        self.tree.config(xscrollcommand=self.scrollbar_x.set)

    def select_file1(self):
        self.file1_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        self.status_label.config(text=f"Файл 1: {self.file1_path}")

    def select_file2(self):
        self.file2_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
        self.status_label.config(text=f"Файл 2: {self.file2_path}")

    def start_processing(self):
        if not self.file1_path or not self.file2_path:
            messagebox.showerror("Помилка", "Оберіть обидва файли.")
            return
        self.status_label.config(text="Обробка виконується...")
        threading.Thread(target=self.process_data).start()

    def process_data(self):
        try:
            create_and_fill_databases(self.file1_path, self.file2_path)
            self.status_label.config(text="Обробка завершена.")
        except Exception as e:
            messagebox.showerror("Помилка", str(e))
            self.status_label.config(text="Помилка обробки.")

    def show_combined(self):
        self.show_table("sample_1.db", "зведена_таблиця",
                        ["словоформа", "лема", "частина_мови", "загальна_частота"] + [f"підв_{i}" for i in
                                                                                      range(1, 21)])

    def show_lemmas(self):
        self.show_table("sample_1.db", "ЧС_лем",
                        ["лема", "загальна_частота"] + [f"підв_{i}" for i in range(1, 21)])

    def show_wordforms(self):
        self.show_table("sample_1.db", "част_словоформ",
                        ["словоформа", "загальна_частота"] + [f"підв_{i}" for i in range(1, 21)])

    def show_pos(self):
        self.show_table("sample_1.db", "част_мови",
                        ["частина_мови", "загальна_частота"] + [f"підв_{i}" for i in range(1, 21)])

    def show_table(self, db_name, table_name, columns):
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute(f"SELECT {', '.join(columns)} FROM {table_name} ORDER BY загальна_частота DESC LIMIT 100")
            rows = cursor.fetchall()
            conn.close()

            self.tree.delete(*self.tree.get_children())
            self.tree["columns"] = columns
            for col in columns:
                self.tree.heading(col, text=col)
                self.tree.column(col, anchor="center")
            self.tree["show"] = "headings"

            for row in rows:
                self.tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showerror("Помилка", str(e))


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("1000x600")
    app = App(root)
    root.mainloop()