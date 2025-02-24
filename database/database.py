import sqlite3
from sqlite3 import Error

conn = sqlite3.connect('database.db')


def create_table_if_not_exists():
    try:
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS words (word TEXT, w_id INTEGER PRIMARY KEY);""")
        c.execute("""CREATE TABLE IF NOT EXISTS categories (category TEXT, c_id INTEGER PRIMARY KEY);""")
        c.execute("""CREATE TABLE IF NOT EXISTS word_category (w_id INTEGER, c_id INTEGER, FOREIGN KEY(w_id) 
        REFERENCES words(w_id), FOREIGN KEY(c_id) REFERENCES categories(c_id));""")
        conn.commit()
    except Error as e:
        print("Error creating table")
        print(e)


def insert_category(category):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO categories (category) VALUES (?)", (category,))
        conn.commit()
    except Error as e:
        print("Error inserting category")

def add_word(word, category):
    try:
        c = conn.cursor()
        c.execute("INSERT INTO words (word) VALUES (?)", (word,))
        conn.commit()
        c.execute("SELECT w_id FROM words WHERE word=?", (word,))
        w_id = c.fetchone()[0]
        c.execute("SELECT c_id FROM categories WHERE category=?", (category,))
        c_id = c.fetchone()[0]
        c.execute("INSERT INTO word_category (w_id, c_id) VALUES (?, ?)", (w_id, c_id))
        conn.commit()
        return "success"
    except Error as e:
        return str(e)

def get_all_categories():
    try:
        c = conn.cursor()
        c.execute("SELECT category FROM categories")
        return c.fetchall()
    except Error as e:
        print("Error getting categories")
        return []

def get_words_by_category(category):
    try:
        c = conn.cursor()
        c.execute("SELECT c_id FROM categories WHERE category=?", (category,))
        c_id = c.fetchone()[0]
        c.execute("SELECT word FROM words WHERE w_id IN (SELECT w_id FROM word_category WHERE c_id=?)", (c_id,))
        return c.fetchall()
    except Error as e:
        print("Error getting words")
        return []

def remove_all():
    try:
        c = conn.cursor()
        c.execute("DELETE  FROM word_category")
        c.execute("DELETE  FROM words")
        c.execute("DELETE  FROM categories")
        conn.commit()
        return "success"
    except Error as e:
        return str(e)