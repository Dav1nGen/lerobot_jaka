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
modbus.write(8,0)

# robot = jkrc.RC("192.168.1.5")
# robot.login()
# robot.power_on()
# robot.enable_robot()
# robot.servo_move_enable(1)
# robot.edg_init_extend(en=True,
#                       edg_stat_ip="192.168.1.5",
#                       edg_port=10010,
#                       edg_mode=0)
# target_position_tuple = [
#     -1.427469, 1.290287, -2.063432, 2.366073, 1.521647, 0.063826
# ]

# robot.joint_move(joint_pos=target_position_tuple,
#                  move_mode=0,
#                  is_block=True,
#                  speed=1)
