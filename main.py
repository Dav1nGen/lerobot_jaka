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
# modbus.write(8,1)

robot = jkrc.RC("192.168.1.5")
robot.login()
robot.power_on()
robot.enable_robot()
robot.servo_move_enable(1)
robot.edg_init_extend(en=True,
                      edg_stat_ip="192.168.1.5",
                      edg_port=10010,
                      edg_mode=0)
pos_diff1 = (-0.7, 0, 0, 0, 0, 0)
pos_diff2 = (0.1, 0, 0, 0, 0, 0)
while True:
    robot.edg_servo_p(end_pos=pos_diff1,
                      move_mode=1,
                      step_num=2,
                      robot_index=0)
    logger.debug(f"sent {pos_diff1}")
    time.sleep(0.017)

    robot.edg_servo_p(end_pos=pos_diff2,
                      move_mode=1,
                      step_num=2,
                      robot_index=0)
    logger.debug(f"sent {pos_diff2}")
    time.sleep(0.017)
