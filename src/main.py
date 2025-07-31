import os
from time import sleep, strftime
from datetime import datetime
from json import loads, dumps, decoder as json_decoder
from pprint import pprint

try:
    from bs4 import BeautifulSoup
    from requests import get

    from gtts import gTTS
except ModuleNotFoundError:
    print("[*] Some necessary package requirements were not found! Installing them...")
    os.system("pip install -r requirements.txt")
    print(
        "[*] All necessary package requirements were installed! Please re-run the program..."
    )
    exit()

USER_NAME = "Siddhesh"
WAIT = 180

DEBUG = True
if DEBUG:
    WAIT = 5


def simple_log(message):
    current_time = strftime("%d/%m/%Y %H:%M:%S")
    print(f"[*] [{current_time}]: {message}")


def set_last_checked(update, content):
    try:
        HISTORY = loads(open("last_checked.json", "r").read())
    except (FileNotFoundError, json_decoder.JSONDecodeError):
        HISTORY = {"News": [], "Notifications": [], "Downloads": []}
    HISTORY[update].append(content)
    with open("last_checked.json", "w") as file:
        file.write(dumps(HISTORY, indent=4))


def get_last_checked(update):
    try:
        HISTORY = loads(open("last_checked.json", "r").read())
        result = HISTORY[update]
    except (FileNotFoundError, json_decoder.JSONDecodeError, KeyError):
        HISTORY = {
            "News": [],
            "Notifications": [],
            "Downloads": [],
            "Important": [],
            "Buttons": [],
        }
        result = HISTORY[update]
    return result


def get_updates_from_website():
    try:
        content = get("https://fe2025.mahacet.org/StaticPages/HomePage").content
        soup = BeautifulSoup(content, "html.parser")

        cards = soup.find_all("div", class_="card-body")

        UPDATES = []
        for card in cards:
            parts = []
            paragraphs = card.find_all("p")
            for paragraph in paragraphs:
                text_content = str(paragraph.get_text()).replace("\xa0", " ")
                text_content = text_content.strip()
                parts.append(text_content)
            UPDATES.append(parts)

        raw_important_messages_container = soup.find("div", class_="important-text")
        raw_important_messages = raw_important_messages_container.find_all("lang")

        important_messages = []
        for message in raw_important_messages:
            important_messages.append(
                str(message.get_text()).replace("\xa0", " ").strip()
            )
        UPDATES.append(important_messages)

        raw_button_messages_container = soup.find("div", id="LeftMenu")
        raw_button_link_boxes_containers = raw_button_messages_container.find_all(
            "div", class_="LinkBox"
        )

        raw_button_names = []
        for container in raw_button_link_boxes_containers:
            for contents in container:
                raw_button_names.extend(contents.find_all("a"))

        button_names = []
        for button_name in raw_button_names:
            button_names.append(str(button_name.get_text()).strip())
        UPDATES.append(button_names)

        NEWS, NOTIFICATIONS, DOWNLOADS, IMPORTANT, BUTTONS = UPDATES
        result = {
            "News": NEWS,
            "Notifications": NOTIFICATIONS,
            "Downloads": DOWNLOADS,
            "Important": IMPORTANT,
            "Buttons": BUTTONS,
        }
        with open("updates.json", "w") as file:
            file.write(dumps(result, indent=4))
        return result

    except Exception as E:
        simple_log(f"Error while parsing the updates: {E}")
        return loads(open("updates.json", "r").read())


def create_txt_to_speech_message(update_name, message):
    text = f"Hello {USER_NAME}, there is a new '{update_name}' message from CET Cell, stating that {message}. Please visit the official website for more information."
    tts = gTTS(text=text, lang="en")
    tts.save("output.mp3")


def play_voice_message():
    while not DEBUG:
        try:
            info = os.popen("termux-media-player info").read()
            status = loads(info).get("status")
            if status == "stopped":
                break
            sleep(0.1)
        except Exception as E:
            simple_log(f"Termux API Sound playing error: {E}")
            break
    (
        os.system("mpg123 notification-sound.mp3")
        if DEBUG
        else os.system("termux-media-player play notification-sound.mp3")
    )
    sleep(2)
    (
        os.system("mpg123 output.mp3")
        if DEBUG
        else os.system("termux-media-player play output.mp3")
    )
    if not DEBUG:
        sleep(15)


def main():
    simple_log("Main Loop Started!")
    while True:
        try:
            simple_log("Checking for updates...")
            UPDATES = get_updates_from_website()
            for update_name, update_messages in UPDATES.items():
                history = get_last_checked(update_name)
                for message in update_messages:
                    if message not in history:
                        simple_log(f"New Update found - {update_name}: {message}")
                        now = datetime.now()
                        current_hour = int(now.hour)
                        if (current_hour > 8) and (current_hour < 23):
                            create_txt_to_speech_message(update_name, message)
                            play_voice_message()
                        set_last_checked(update_name, message)
                        sleep(3)
            sleep(WAIT)
        except KeyboardInterrupt:
            simple_log("Stopping Main Loop...")
            simple_log("Exiting Program...")
            break
        except Exception as E:
            simple_log(f"Main Loop Error: {E}")
            sleep(WAIT + 30)


if __name__ == "__main__":
    # simple_log("Starting Main Loop...")
    # main()
    # simple_log("Main Loop stopped! Program stopped!")
    print(get_updates_from_website())
