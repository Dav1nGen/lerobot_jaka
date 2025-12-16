import logging
import os
import sys
import time
from queue import Queue
from typing import Any

from pynput import keyboard
from pynput.keyboard import Key, Listener

class KeyboardTrigger:
    def __init__(self, key: str, callback: Any):
        self.key = key
        self.callback = callback
        self.listener = Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key: Key):
        if key == self.key:
            self.callback()

    def stop(self):
        self.listener.stop()