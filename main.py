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

# modbus = ModbusTCP()

# modbus.connect()
# modbus.write(8,0)

# Test
robot = jkrc.RC("192.168.1.3")
robot.login()
robot.power_on()
robot.enable_robot()
robot.servo_move_enable(1)
robot.edg_init_extend(en=True,
                      edg_stat_ip="192.168.1.3",
                      edg_port=10010,
                      edg_mode=0)
time.sleep(1)
# joint_position = (0, 0, 0, 0, 0, 0)
joint_position = (0, 0, -0.0523598, 0, 0, 0)
# result = robot.joint_move(position, 0, True, 1)
# result = robot.joint_move(joint_position, 0, True, 1)

# logger.info(f"move result: {result}")

result = robot.edg_servo_j(joint_pos=joint_position,
                           move_mode=0,
                           step_num=1000000,
                           robot_index=0)

logger.info(f"{result}")
