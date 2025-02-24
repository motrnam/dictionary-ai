import os

import requests
import random
import pyperclip as pc

import database.database as db

base_url = "https://api.metisai.ir/api/v1/chat"
api_key = os.environ.get("METIS_API_KEY")
bot_api = os.environ.get("METIS_BOT_API")
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

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



from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Center
from textual.screen import Screen,ModalScreen
from textual.widgets import Button, Label, Select,Input , ListView,ListItem


class AddWords(ModalScreen[str]):
    """A modal popup window with a dropdown and OK/Cancel buttons."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def compose(self) -> ComposeResult:
        """Compose the popup content."""
        categories = get_all_categories()
        with Container(id="popup-container"):
            with Vertical(id="popup-content"):
                yield Label("Select an item:", id="popup-label1")
                yield Select(
                    options=[(cat, cat) for cat in categories],
                    id="dropdown",
                    prompt="Select an option",
                )
                yield Label("Enter a word:", id="popup-label")
                yield Input(placeholder="word", id="text_input5")
                with Center():
                    yield Button("OK", id="btn-ok", variant="primary")
                    yield Button("Cancel", id="btn-cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-ok":
            # Get the selected value from the dropdown
            dropdown = self.query_one("#dropdown", Select)
            selected_value = dropdown.value
            text_input = self.query_one("#text_input5", Input).value
            if selected_value and text_input and text_input != "":
                add_word(text_input, selected_value)
                self.dismiss(selected_value)
            else:
                self.notify("Please select an item first!", title="Error", severity="error")
        elif event.button.id == "btn-cancel":
            # Dismiss the popup without returning a value
            self.dismiss(None)

class WordScene(ModalScreen[str]):
    """A modal popup window with a dropdown and OK/Cancel buttons."""

    def __init__(self, feedback):
        super().__init__()
        self.feedback = feedback

    def compose(self) -> ComposeResult:
        """Compose the popup content."""
        categories = get_all_categories()
        with Container(id="popup-container"):
            with Vertical(id="popup-content"):
                yield Label("Select an item:", id="popup-label")
                yield Select(
                    options=[(cat, cat) for cat in categories],
                    id="dropdown",
                    prompt="Select an option",
                )
                with Center():
                    yield Button("OK", id="btn-ok", variant="primary")
                    yield Button("Cancel", id="btn-cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-ok":
            # Get the selected value from the dropdown
            dropdown = self.query_one("#dropdown", Select)
            selected_value = dropdown.value
            if selected_value:
                # Dismiss the popup and return the selected value
                self.dismiss(selected_value)
                self.feedback(selected_value)
            else:
                self.notify("Please select an item first!", title="Error", severity="error")
        elif event.button.id == "btn-cancel":
            # Dismiss the popup without returning a value
            self.dismiss(None)

class ShowWords(ModalScreen[str]):
    def __init__(self, category: str):
        super().__init__()
        self.category = category
        self.words = get_word_by_category(category)  # Ensure this function exists

    def compose(self) -> ComposeResult:
        yield Container(
            Vertical(
                Label(f"Words in category {self.category}", id="popup-label"),
                ListView(
                    *[ListItem(Label(word)) for word in self.words],  # Wrap word in Label
                    id="list_view"
                ),
                Button("Back", id="back_button"),
                id="popup-content",
            ),
            id="popup-container"
        )

    def on_button_pressed(self, event) -> None:
        if event.button.id == "back_button":
            self.dismiss()

class AddCategory(ModalScreen[str]):
    def __init__(self, callback: callable):
        super().__init__()
        self.callback = callback  # Callback function to send feedback

    def compose(self) -> ComposeResult:
        """Compose the popup scene content."""
        with Container(id="popup-container-category"):
            with Vertical(id="popup-content-category"):
                yield Label("Enter a value:", id="popup-label")
                yield Input(placeholder="Type something...", id="text_input")
                with Center():
                    yield Button("OK", id="btn-ok", variant="primary")
                    yield Button("Cancel", id="btn-cancel", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn-ok":
            text_input = self.query_one("#text_input", Input)
            entered_value = text_input.value.strip()
            if entered_value and entered_value != "" and entered_value not in get_all_categories():
                add_category(entered_value)
                self.callback(entered_value)
            else:
                self.notify("Category is not added", title="Error", severity="error")
            self.app.pop_screen()  # Close the popup
        elif event.button.id == "btn-cancel":
            self.app.pop_screen()  # Close the popup

class MainScene(Screen):
    def compose(self) -> ComposeResult:
        """Create UI components."""
        yield Container(
            Vertical(
                Button("Add Category", id="add_category"),
                Button("Show words", id="show_words"),
                Button("Add word", id="add_word"),
                Button("Add word from clipboard", id="add_word_from_clipboard"),
                Button("Get Passage", id="get_passage"),
                Button("Quit", id="btn_quit"),
                Button("Delete all", id="delete_all"),
                Label("#HELLO", id="digits"),
                id="button-column"
            ),
            id="centered-container"
        )

    def on_mount(self) -> None:
        """Bind buttons to event handlers."""
        self.app.bind("q", "quit")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "btn_quit":
            self.app.exit()
        elif event.button.id == "show_words":
            self.app.push_screen(WordScene(self.handle_feedback_1))
        elif event.button.id == "add_category":
            self.app.push_screen(AddCategory(self.handle_feedback_2))
        elif event.button.id == "delete_all":
            res = remove_all()
            self.notify(f"result {res}", title="Feedback", severity="information")
        elif event.button.id == "add_word":
            self.app.push_screen(AddWords(self.handle_feedback_3))

    def handle_feedback_1(self, value: str) -> None:
        """Handle feedback from the popup."""
        self.mount(ShowWords(value))

    def handle_feedback_2(self,value:str) -> None:
        """Handle """
        self.notify(f"category {value} added" , title="Feedback" , severity="information")

    def handle_feedback_3(self,value:str) -> None:
        self.notify(f"word {value} added" , title="Feedback" , severity="information")


class PassageScene(ModalScreen[str]):
    def __init__(self,passage):
        super().__init__()

class MyApp(App):
    CSS = """
        #centered-container {
            align: center middle;
        }

        #button-column {
            align: center middle;
        }

        #popup-content{
            align: center middle;
        }
        
        #popup-container{
            align: center middle;
        }

        #dropdown {
            width: 100%;
            align-horizontal: center;
        }

        Button {
            width: 30%;
            margin: 1;
        }
    """

    def on_mount(self) -> None:
        """Register the main scene."""
        self.push_screen(MainScene())  # Start with the main scene


if __name__ == "__main__":
    db.create_table_if_not_exists()
    app = MyApp()
    app.run()
