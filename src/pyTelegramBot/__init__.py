"""
pyTelegramBot - Custom Telegram Bot API wrapper for Python made for personal use cases
====================================================================================================

Although there are many wrappers available on pypi.org which are more better than this custom one, I still
made this because those had many features and functions which were not required for many of my projects,
especially the small ones, so, in this custom wrapper, I added only those things which were required.
If you still need anything more or want to use some other API endpoints provided by Telegram, feel free to
add those.

Also, the performance of this wrapper can probably be improved using a diffrent logic or approach to do
certain things. I've tried to make the code as clean and performance efficient as possible but there can
still be some improvements.

--------------------
Author: @Sid72020123 on Github
"""

from pyTelegramBot.pyTelegramBot import (
    TelegramBot,
    InlineKeyboardInput,
    InlineKeyboardButton,
)
import pyTelegramBot.Exceptions
