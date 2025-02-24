import requests
import random
import pyperclip as pc
import os
import tempfile
import threading
import time
import simpleaudio as sa
from gtts import gTTS
from pydub import AudioSegment
from tkinter import ttk
import database.database as db
import tkinter as tk
from tkinter import simpledialog, messagebox
from dotenv import load_dotenv

load_dotenv()

base_url = "https://api.metisai.ir/api/v1/chat"
api_key = os.environ.get("METIS_API_KEY")
bot_api = os.environ.get("METIS_BOT_API")

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

def get_chat_sessions_for_bot(bot_id, page=0, size=10):
    """
    Get a list of chat sessions for a bot.
    """
    url = f"{base_url}/session?botId={bot_id}&page={page}&size={size}"
    response = requests.get(url, headers=headers)
    return response.json()

def send_message(session_id, content, message_type="USER"):
    """
    Send a message in a chat session.
    """
    url = f"{base_url}/session/{session_id}/message"
    data = {
        "message": {
            "content": content,
            "type": message_type
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return response.json()

def create_chat_session(bot_id, user=None, initial_messages=None):
    """
    Create a new chat session.
    """
    url = f"{base_url}/session"
    data = {
        "botId": bot_id,
        "user": user,
        "initialMessages": initial_messages or []
    }
    response = requests.post(url, headers=headers, json=data)
    print(response)
    return response.json()


def get_passage(session,category):
    words = db.get_words_by_category(category)
    if len(words) == 0:
        return "No words in category"
    targets = []
    if len(words) > 5:
        targets = random.sample(words, 5)
    else:
        targets = words
    message = f"write a passage using the following words: {', '.join([word[0] for word in targets])}"
    print(message)
    resp = send_message(session, message)
    print(resp.get('content'))
    return resp.get('content') , targets


def add_category(category):
    db.insert_category(category)

def add_word(word, category):
    # check if category exists
    categories = db.get_all_categories()
    if (category,) not in categories:
        add_category(category)
    db.add_word(word, category)

def add_word_from_clipboard(category):
    words = pc.paste().split()
    for word in words:
        add_word(word, category)

def get_all_categories():
    cate = db.get_all_categories()
    res = [s[0] for s in cate]
    return res

def remove_all():
    return db.remove_all()

def get_word_by_category(category):
    all_words = db.get_words_by_category(category)
    return [word[0] for word in all_words]





class AddWordsDialog(simpledialog.Dialog):
    def body(self, master):
        frame = ttk.Frame(master, padding=10)
        frame.grid(sticky="ew")

        ttk.Label(frame, text="Select Category:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.dropdown = ttk.Combobox(frame, textvariable=self.category_var, state="readonly", width=25)
        self.dropdown['values'] = get_all_categories()
        self.dropdown.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Enter Word:", font=("Arial", 10, "bold")).grid(row=1, column=0, padx=5, pady=5)
        self.word_entry = ttk.Entry(frame, width=28)
        self.word_entry.grid(row=1, column=1, padx=5, pady=5)

        return self.word_entry

    def apply(self):
        selected_value = self.category_var.get()
        text_input = self.word_entry.get().strip()
        if selected_value and text_input:
            add_word(text_input, selected_value)
        else:
            messagebox.showerror("Error", "Please select a category and enter a word")


class WordSceneDialog(simpledialog.Dialog):
    def body(self, master):
        frame = ttk.Frame(master, padding=10)
        frame.grid(sticky="ew")

        ttk.Label(frame, text="Select Category:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.dropdown = ttk.Combobox(frame, textvariable=self.category_var, state="readonly", width=25)
        self.dropdown['values'] = get_all_categories()
        self.dropdown.grid(row=0, column=1, padx=5, pady=5)

        return self.dropdown

    def apply(self):
        selected_value = self.category_var.get()
        if selected_value:
            ShowWordsDialog(self.parent, selected_value)
        else:
            messagebox.showerror("Error", "Please select a category")


class WordSceneDialog2(simpledialog.Dialog):
    def body(self, master):
        frame = ttk.Frame(master, padding=10)
        frame.grid(sticky="ew")

        ttk.Label(frame, text="Select Category:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.dropdown = ttk.Combobox(frame, textvariable=self.category_var, state="readonly", width=25)
        self.dropdown['values'] = get_all_categories()
        self.dropdown.grid(row=0, column=1, padx=5, pady=5)

        return self.dropdown

    def apply(self):
        selected_value = self.category_var.get()
        if selected_value:
            res = get_passage(section, selected_value)
            passage, targets = res
            GetPassageDialog(self, targets, passage)
        else:
            messagebox.showerror("Error", "Please select a category")


class ShowWordsDialog(simpledialog.Dialog):
    def __init__(self, parent, category):
        self.category = category
        super().__init__(parent, title=f"Words in {category}")

    def body(self, master):
        frame = ttk.Frame(master, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"Words in category: {self.category}", font=("Arial", 12, "bold")).pack(pady=5)
        self.listbox = tk.Listbox(frame, height=8, width=30)
        self.listbox.pack(pady=5)

        words = get_word_by_category(self.category)
        for word in words:
            self.listbox.insert(tk.END, word)

        ttk.Button(frame, text="Close", command=self.destroy).pack(pady=5)


class AddCategoryDialog(simpledialog.Dialog):
    def body(self, master):
        frame = ttk.Frame(master, padding=10)
        frame.grid(sticky="ew")

        ttk.Label(frame, text="Enter Category:", font=("Arial", 10, "bold")).grid(row=0, column=0, padx=5, pady=5)
        self.entry = ttk.Entry(frame, width=28)
        self.entry.grid(row=0, column=1, padx=5, pady=5)

        return self.entry

    def apply(self):
        category = self.entry.get().strip()
        if category and category not in get_all_categories():
            add_category(category)
        else:
            messagebox.showerror("Error", "Invalid category or already exists")





class GetPassageDialog(simpledialog.Dialog):
    def __init__(self, parent, targets, passage):
        self.passage = passage
        self.targets = targets
        super().__init__(parent)

    def body(self, master):
        frame = ttk.Frame(master, padding=10)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Passage", font=("Arial", 12, "bold")).pack(pady=5)
        ttk.Label(frame, text=self.passage, wraplength=300, justify="center").pack(pady=5)

        # Label to display the selected word
        self.display_label = ttk.Label(frame, text="", font=("Arial", 12, "bold"), foreground="blue")
        self.display_label.pack(pady=5)

        # Button to listen to passage
        ttk.Button(frame, text="🔊 Listen", command=self.speak_passage).pack(pady=5)

        # Button to show the selected word
        ttk.Button(frame, text="Show Word", command=self.show_selected_word).pack(pady=5)

    def speak_passage(self):
        def play_audio():
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_mp3, \
                        tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_wav:
                    tts = gTTS(self.passage)
                    tts.save(temp_mp3.name)

                    # Ensure ffmpeg works correctly
                    audio = AudioSegment.from_file(temp_mp3.name, format="mp3")
                    audio.export(temp_wav.name, format="wav")

                    wave_obj = sa.WaveObject.from_wave_file(temp_wav.name)
                    play_obj = wave_obj.play()

                    # Wait for playback in a safe way
                    threading.Thread(target=self.delayed_cleanup, args=(play_obj, temp_mp3.name, temp_wav.name),
                                     daemon=True).start()

            except Exception as e:
                print(f"Error in audio playback: {e}")

        threading.Thread(target=play_audio, daemon=True).start()

    def delayed_cleanup(self, play_obj, temp_mp3, temp_wav):
        """Wait for playback to fully finish before deleting temp files."""
        play_obj.wait_done()  # This waits safely
        time.sleep(0.5)  # Small delay to ensure the file is fully released

        try:
            os.remove(temp_mp3)
            os.remove(temp_wav)
            print("Temporary files deleted safely.")
        except Exception as e:
            print(f"Error deleting files: {e}")

    def show_selected_word(self):
        edited = [x[0] for x in self.targets]
        self.display_label.config(text=f"Selected: {edited}")


class GetWordClipBoard(simpledialog.Dialog):
    def body(self, master):
        frame = ttk.Frame(master,padding=10)
        frame.grid(sticky="ew")
        group_name_tb = ttk.Label(frame, text="Enter Category:", font=("Arial", 10, "bold"))
        group_name_tb.grid(row=0, column=0, padx=5, pady=5)
        self.category_var = tk.StringVar()
        self.dropdown = ttk.Combobox(frame, textvariable=self.category_var, state="readonly", width=25)
        self.dropdown['values'] = get_all_categories()
        self.dropdown.grid(row=0, column=1, padx=5, pady=5)
        return self.dropdown

    def apply(self):
        selected_value = self.category_var.get()
        if selected_value:
            add_word_from_clipboard(selected_value)
        else:
            messagebox.showerror("Error", "Please select a category")



class MainApplication(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Main Scene")
        self.geometry("350x450")
        self.configure(bg="#f0f0f0")

        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Welcome!", font=("Arial", 14, "bold")).pack(pady=10)

        button_style = {"padding": 5, "width": 20,"cursor" : "hand2"}

        ttk.Button(frame, text="Add Category", command=self.add_category, **button_style).pack(pady=5)
        ttk.Button(frame, text="Show Words", command=self.show_words, **button_style).pack(pady=5)
        ttk.Button(frame, text="Add Word", command=self.add_word, **button_style).pack(pady=5)
        ttk.Button(frame, text="Get Passage", command=self.get_passage, **button_style).pack(pady=5)
        ttk.Button(frame, text="Quit", command=self.quit, **button_style).pack(pady=5)
        ttk.Button(frame, text="Remove All", command=self.remove_everything, **button_style).pack(pady=5)
        ttk.Button(frame, text="Get Word from Clipboard", command=self.get_word_clipboard, **button_style).pack(pady=5)

    def add_category(self):
        AddCategoryDialog(self)

    def show_words(self):
        WordSceneDialog(self)

    def add_word(self):
        AddWordsDialog(self)

    def get_passage(self):
        WordSceneDialog2(self)

    def get_word_clipboard(self):
        GetWordClipBoard(self)

    def remove_everything(self):
        remove_all()


if __name__ == "__main__":
    db.create_table_if_not_exists()
    sections = get_chat_sessions_for_bot(bot_api)

    section = sections[0].get('id') if sections else create_chat_session(bot_api)

    app = MainApplication()
    app.mainloop()

