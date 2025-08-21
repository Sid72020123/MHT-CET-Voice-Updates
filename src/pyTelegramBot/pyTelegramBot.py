"""
pyTelegramBot - Main File
====================================================================================================

This file contains the main code of the wrapper. There are some limited functions but you can
add more.

--------------------
Author: @Sid72020123 on Github
"""

from json import dumps
from requests import Session
from requests.exceptions import ConnectionError
from traceback import print_exc

from pyTelegramBot.Exceptions import InsufficientDataException

# Official Telegram Bot API Documentation: https://core.telegram.org/bots/api
TELEGRAM_API_URL = "https://api.telegram.org/bot"


class User:
    def __init__(self, user_dict, bot_object):
        """
        Telegram user class used internally by the program
        :param user_dict: The dictionary of the user data received from the Telegram API
        :param bot_object: Object of the TelegramBot class
        """
        self.user_dict = user_dict
        self.bot_object = bot_object

        self.id = user_dict["id"]
        self.is_bot = user_dict.get("is_bot", None)
        self.first_name = user_dict.get("first_name", "")
        self.last_name = user_dict.get("last_name", "")
        self.username = user_dict.get("username", None)

    def send_message(
        self, message: str, parse_mode: str = "HTML", disable_wpp: bool = True
    ):
        """
        Send a message to the user
        :param message: The message to send
        :param parse_mode: The way the message should be parsed by the Telegram API
        :param disable_wpp: Change the behavior of "disable_web_page_preview" provided by the Telegram API
        """
        return self.bot_object.send_message(
            chat_id=self.id,
            message=message,
            parse_mode=parse_mode,
            disable_wpp=disable_wpp,
        )


class Message:
    def __init__(self, message_dict, bot_object):
        """
        Telegram message class used internally by the program
        :param message_dict: The dictionary of the message data received from the Telegram API
        :param bot_object: Object of the TelegramBot class
        """
        self.message_dict = message_dict
        self.bot_object = bot_object

        self._update(message_dict)

    def _update(self, message_dict):
        """
        Internal function to update the class attributes. Don't use.
        """
        self.id = message_dict["message_id"]
        self.date = message_dict["date"]
        self.text = message_dict["text"]
        self.entities = message_dict.get("entities", None)
        self.from_user = User(message_dict["from"], self.bot_object)
        self.chat = message_dict["chat"]
        self.chat_id = self.chat["id"]

    def edit(
        self,
        message: str,
        parse_mode: str = "HTML",
        disable_wpp: bool = True,
    ):
        """
        Edit the Telegram message
        :param message: The new text of the message to be edited
        :param parse_mode: The way the message should be parsed by the Telegram API
        :param disable_wpp: Change the behavior of "disable_web_page_preview" provided by the Telegram API
        """
        response = self.bot_object.edit_message(
            chat_id=self.chat_id,
            message_id=self.id,
            message=message,
            parse_mode=parse_mode,
            disable_wpp=disable_wpp,
        )
        if response["ok"]:
            self._update(response["result"])
            return True
        return False


class InlineKeyboardButton:
    def __init__(self, text: str, callback_data: str):
        """
        Class to make the adding of buttons to the inline keyboard input feature of Telegram more easier.
        Use this to add buttons to the inline keyboard input
        :param text: The text to be displayed on the button
        :param callback_data: The string with which the user can identify the exact button which is pressed from a group of buttons
        """
        self.text = text
        self.callback_data = callback_data


class InlineKeyboardInput:
    def __init__(self, name):
        """
        Parent class to add the inline keyboard input to a Telegram message
        :param name: Unique name of the "input" with which the program can detect exactly which set of buttons are pressed and from which message
        """
        self.name = name
        self.buttons = []
        self.action_function = (
            None  # The function that will be called each time the user presses a button
        )

    def set_action_function(self, func):
        """
        Set the action function (as explained above)
        :param func: The function. Make sure that it accepts a parameter
        """
        self.action_function = func

    def add_buttons(self, buttons: list[InlineKeyboardButton]):
        """
        Add buttons to the inline keyboard input.
        See the official Telegram Bot API documentation for more options to group many buttons together
        :param buttons: A list of buttons, each element being an instance of the InlineKeyboardButton class
        """
        processed = []
        for button in buttons:
            processed.append(
                {
                    "text": button.text,
                    "callback_data": f"{self.name}_{button.callback_data}",  # This is what makes it easier to detect which buttons are pressed
                }
            )
        self.buttons.append(processed)


class CallbackQuery:
    def __init__(self, query_dict, bot_object):
        """
        Telegram callback query update class used internally by the program
        :param query_dict: The dictionary of the query data received from the Telegram API
        :param bot_object: Object of the TelegramBot class
        """
        self.query_dict = query_dict
        self.bot_object = bot_object

        self.id = query_dict["id"]
        self.from_user = User(query_dict["from"], bot_object)
        self.message = Message(query_dict["message"], bot_object)
        self.data = str(query_dict["data"])

        self.input_name = self.data.split("_")[0]  # The name of the input
        self.input_data = self.data[
            self.data.index("_") + 1 :
        ]  # The name of the data (or the ID of button pressed) of that particular input

    def answer_callback(self):
        """
        Just answer the query, i.e., let the client/user know that the bot/program has received the input and is still processing further tasks
        """
        return self.bot_object.answer_callback_query(self.id)

    def edit_inline_keyboard_input(self, iki: InlineKeyboardInput):
        """
        Edit the "reply_markup" of the Telegram message by editing the buttons/content of the inline keyboard input
        :param iki: The object of InlineKeyboardInput class
        """
        return self.bot_object.edit_inline_keyboard_input(
            chat_id=self.from_user.id, message_id=self.message.id, iki=iki
        )


class TelegramBot:
    def __init__(self, token):
        """
        The main class to manage your Telegram Bot
        :param token: The bot token of your bot
        """
        self.session = Session()
        self.bot_token = token
        self.api_url = f"{TELEGRAM_API_URL}{token}"

        self.commands = {}  # Used to store the command functions
        self.commands_help_text = {}  # Used to store the command help texts
        self.command_history = (
            {}
        )  # Used to store the most recent command used by a particular user
        self.accept_text_input = (
            {}
        )  # Used to store exactly which commands can accept a text input after being used
        self.inline_keyboard_inputs = (
            {}
        )  # Used to store the objects created while using the inline keyboard input in a message

        self.events = {
            "start": None,  # the bot starts
            "new_message": None,  # a message is received, i.e., a new update
            "new_text_message": None,  # a text message is received or basically the text message received other than a text input a specific command is awaiting
            "new_command": None,  # a command is received
            "stop": None,  # the bot stops
            "incorrect_command": None,  # the command which doesn't exist is being used
        }  # Used by "events" feature

        self.update_offset = 0
        self.get_updates(first_offset=True)  # Required for storing the first offset

    def get_updates(
        self,
        offset=None,
        timeout: int = 3,
        limit: int = 10,
        first_offset: bool = False,
    ):
        """
        Get the updates the bot receives from the Telegram Bot API
        :param offset: The offset of the update
        :param timeout: The timeout
        :param limit: The limit of the updates
        :param first_offset: Set it to True if you want to get the offset of the most recent update
        """
        request_offset = offset
        if offset is None:
            request_offset = self.update_offset
            if first_offset:
                request_offset = -1  # Get the most recent update

        response = self.session.get(
            f"{self.api_url}/getUpdates",
            params={"limit": limit, "offset": request_offset, "timeout": timeout},
        )
        response_json = response.json()
        if first_offset or (offset is None):
            if response_json["ok"] and len(response_json["result"]) > 0:
                self.update_offset = (
                    response_json["result"][0]["update_id"] + 1
                )  # Increase the offset by 1 to check for the next update
        results = response_json["result"]
        updates = []
        for result in results:
            if "message" in result:
                updates.append(Message(result["message"], self))
            elif "callback_query" in result:
                updates.append(CallbackQuery(result["callback_query"], self))
            else:
                updates.append(
                    result
                )  # Only the two types of updates ("message" and "callback_query") are processed here. The rest are returned. This can also be changed.
        return updates

    def get_user_info(self, id: int):
        """
        Returns the information about a Telegram user
        :param id: The ID of the chat
        """
        response = self.session.get(f"{self.api_url}/getChat?chat_id={id}").json()
        if response["ok"]:
            return User(response["result"], self)
        return response

    def send_message(
        self, chat_id, message: str, parse_mode: str = "HTML", disable_wpp: bool = True
    ):
        """
        Sends the message to a chat ID
        :param chat_id: The ID of the chat
        :param message: The message to be sent
        :param parse_mode: The way the message should be parsed by the Telegram API
        :param disable_wpp: Change the behavior of "disable_web_page_preview" provided by the Telegram API
        """
        response = self.session.get(
            f"{self.api_url}/sendMessage",
            params={
                "chat_id": chat_id,
                "parse_mode": parse_mode,
                "text": message,
                "disable_web_page_preview": disable_wpp,
            },
        ).json()
        if response["ok"]:
            return Message(response["result"], self)
        else:
            return response

    def send_inline_keyboard_input(
        self,
        chat_id,
        message: str,
        iki: InlineKeyboardInput,
        parse_mode: str = "HTML",
        disable_wpp: bool = True,
    ):
        """
        Send the inline keyboard input as reply markup along with the message
        :param chat_id: The ID of the chat
        :param message: The message to be sent alongside the input keyboard
        :param iki: An object of the InlineKeyboardInput class
        :param parse_mode: The way the message should be parsed by the Telegram API
        :param disable_wpp: Change the behavior of "disable_web_page_preview" provided by the Telegram API
        """
        payload = {
            "chat_id": chat_id,
            "parse_mode": parse_mode,
            "text": message,
            "disable_web_page_preview": disable_wpp,
            "reply_markup": dumps({"inline_keyboard": iki.buttons}),
        }
        self.inline_keyboard_inputs[iki.name] = iki
        response = self.session.get(
            f"{self.api_url}/sendMessage", params=payload
        ).json()
        if response["ok"]:
            return Message(response["result"], self)
        else:
            return response

    def edit_inline_keyboard_input(self, chat_id, message_id, iki: InlineKeyboardInput):
        """
        Edit the input of the inline keyboard
        :param chat_id: The ID of the chat
        :param message_id: The message ID which has a reply markup of inline keyboard
        :param iki: An object of the InlineKeyboardInput class
        """
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": dumps({"inline_keyboard": iki.buttons}),
        }
        if len(iki.buttons) == 0:
            payload["reply_markup"] = {}  # Remove all the buttons if its empty
        self.inline_keyboard_inputs[iki.name] = iki
        response = self.session.get(
            f"{self.api_url}/editMessageReplyMarkup", params=payload
        ).json()
        if response["ok"]:
            return Message(response["result"], self)
        else:
            return response

    def answer_callback_query(self, query_id: int):
        """
        Just answer the query, i.e., let the client/user know that the bot/program has received the input and is still processing further tasks
        :param query_id: The ID of the query
        """
        data = {"callback_query_id": query_id}
        return self.session.get(
            f"{self.api_url}/answerCallbackQuery", data=data
        ).json()["result"]

    def send_photo(
        self,
        chat_id,
        from_url=None,
        from_file=None,
        caption: str = "",
        parse_mode: str = "HTML",
        show_caption_above: bool = False,
        has_spoiler: bool = False,
    ):
        """
        Sends a photo message to a chat ID. Make sure to provide at least one of the "from_url" and "from_file" parameters
        :param chat_id: The ID of the chat
        :param from_url: Send the image from an URL (more priority over 'from_file')
        :param from_file: Send the image from a file path
        :param caption: The caption to be sent alongside the image
        :param parse_mode: The way the message/caption should be parsed by the Telegram API
        :param show_caption_above: Set it to True if you want the image caption to be displayed above the image
        :param has_spoiler: Set it to True if you want the image to be sent as a "spoiler" message
        """
        payload = {
            "chat_id": chat_id,
            "caption": caption,
            "parse_mode": parse_mode,
            "show_caption_above_media": show_caption_above,
            "has_spoiler": has_spoiler,
        }
        response = {}
        if from_url is not None:
            payload["photo"] = from_url
            response = self.session.post(
                f"{self.api_url}/sendPhoto", data=payload
            ).json()
        elif from_file is not None:
            with open(from_file, "rb") as file:
                response = self.session.post(
                    f"{self.api_url}/sendPhoto", data=payload, files={"photo": file}
                ).json()
        else:
            raise InsufficientDataException(
                "One of the 'from_url' or 'from_file' variables should be provided!"
            )
        return response

    def edit_message(
        self,
        chat_id,
        message_id,
        message: str,
        parse_mode: str = "HTML",
        disable_wpp: bool = True,
    ):
        """
        Edit the Telegram message
        :param chat_id: The ID of the chat
        :param message_id: The ID of the message to be edited
        :param message: The new text of the message to be edited
        :param parse_mode: The way the message should be parsed by the Telegram API
        :param disable_wpp: Change the behavior of "disable_web_page_preview" provided by the Telegram API
        """
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "parse_mode": parse_mode,
            "text": message,
            "disable_web_page_preview": disable_wpp,
        }
        return self.session.get(
            f"{self.api_url}/editMessageText", params=payload
        ).json()  # Directly parsed JSON is returned here...

    def on_command(
        self,
        command_names: list[str],
        accept_text_input=None,
        help_text: list[str] = [],
    ):
        """
        Function for the decorator of commands
        :param command_names: List of commands which will trigger the function given below once they are called
        :param accept_text_input: Set a function to this parameter and it will be called when the user enters a text message
        :param help_text: List containing the help text of bot commands
        """

        def func(f):
            count = 0
            for command_name in command_names:
                self.commands[command_name.strip()] = f
                if len(help_text) > 0:
                    final_help_text = ""
                    try:
                        final_help_text = help_text[count]
                    except IndexError:
                        final_help_text = help_text[0]
                    self.commands_help_text[command_name.strip()] = final_help_text
                if accept_text_input is not None:
                    self.accept_text_input[command_name.strip()] = accept_text_input
                count += 1

        return func

    def set_bot_commands_info(self, command_info: list[dict] = []):
        """
        Function to set the command instructions of the bot
        :param commands_info: Optional list of command help data in a dictionary containing the keys "command" and "description"
        """
        payload = {}
        if command_info:
            payload["commands"] = dumps(command_info)
        else:
            info = []
            for command_name, command_description in self.commands_help_text.items():
                info.append(
                    {
                        "command": command_name.lower(),
                        "description": command_description.strip(),
                    }
                )
            payload["commands"] = dumps(info)
        return self.session.get(f"{self.api_url}/setMyCommands", params=payload).json()

    def delete_bot_commands_info(self):
        """
        Function to clear all the command instructions of the bot
        """
        return self.session.get(f"{self.api_url}/deleteMyCommands").json()

    def _emit_event(self, e_name, data=None):
        """
        Internal function used to "emit" the events (or call the functions associated with specific events). Don't use this
        """
        if self.events[e_name]:
            if data:
                self.events[e_name](data)
            else:
                self.events[e_name]()

    def on_event(self, event_name):
        """
        Function for the decorator of events
        :param event_name: The event name
        """
        if event_name not in list(self.events.keys()):
            raise ValueError(
                f"Invalid event name, please choose one from the list: {list(self.events.keys())}"
            )

        def func(f):
            self.events[event_name] = f

        return func

    def cancel_text_input(self, chat_id):
        """
        Cancel accepting text inputs from the user after using a specific command
        :param chat_id: The chat ID
        """
        try:
            command_used = str(self.command_history[str(chat_id)])
            if command_used in self.accept_text_input:
                del self.command_history[str(chat_id)]
                return [True, command_used]
            return [False, False]
        except KeyError:
            return [False, False]
        except Exception as E:
            return [False, E]

    def start_polling(self):
        """
        Start the infinite polling wherein the bot/program will check for new updates and proceed accordingly
        """
        self._emit_event("start")  # Emit the start event as the bot is starting
        while True:
            try:
                update = self.get_updates()
                if len(update) == 0:
                    continue
                latest_update = update[0]
                if type(latest_update) not in (
                    Message,
                    CallbackQuery,
                ):  # Only two types of updates are checked here according to the use case but you may add more...
                    continue
                message = latest_update
                self._emit_event("new_message", message)
                if (type(latest_update) is Message) and (message.entities is not None):
                    entity_type = message.entities[0]["type"]
                    if (
                        entity_type == "bot_command"
                    ):  # Confirm if the update received is a bot command or not
                        text = str(message.text).strip()
                        command = text[1:]
                        if command in self.commands:
                            self._emit_event("new_command", message)
                            can_proceed = True
                            if (
                                "<any>" in self.commands
                            ):  # A special feature to do a certain action before the main command action
                                can_proceed = self.commands["<any>"](
                                    message
                                )  # Remember: The function provided must return a boolean value
                            if not can_proceed:
                                continue
                            self.commands[command](message)  # Call the command function
                            self.command_history[str(message.from_user.id)] = (
                                command  # Save the command for the specific chat ID
                            )
                        else:
                            self._emit_event("incorrect_command", message)
                elif type(latest_update) is CallbackQuery:  # The callback query
                    callback_query = latest_update
                    if self.inline_keyboard_inputs[
                        callback_query.input_name
                    ].action_function:
                        self.inline_keyboard_inputs[
                            callback_query.input_name
                        ].action_function(
                            callback_query
                        )  # Call the function for that specific callback query
                    else:
                        self.answer_callback_query(
                            callback_query.id
                        )  # Automatically answer the callback query as the function was empty
                else:  # Normal messages other than bot commands and callback query
                    user_id = str(message.from_user.id)
                    if user_id in self.command_history:
                        command_used = self.command_history[user_id]
                        if (
                            command_used in self.accept_text_input
                        ):  # Call the text input function if the text input is enabled for a specific command
                            self.accept_text_input[command_used](message.text, message)
                        else:
                            self._emit_event("new_text_message", message)
                    else:
                        self._emit_event("new_text_message", message)
            except ConnectionError as CE:
                print(f"pyTelegramBot > Connection Error: {CE}")
            except KeyboardInterrupt:
                self._emit_event("stop")
                break
            except Exception as E:
                print(f"pyTelegramBot > Polling Loop Exception: {E}")
                print_exc()
