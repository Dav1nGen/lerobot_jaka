from lerobot.robots.jakaS12.jaka_lib_2_3_0 import jkrc
from pynput import keyboard
import sys
import os
import time
import ctypes

import threading
import time
import math
from datetime import datetime
from loguru import logger
from lerobot.robots.jakaS12.modbus_tcp import ModbusTCP

modbus = ModbusTCP()

modbus.connect()
modbus.write(8,1)

