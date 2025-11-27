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

robot = jkrc.RC("192.168.1.5")
robot.login()
robot.power_on()
robot.enable_robot()
robot.edg_init_extend(en=True,
                      edg_stat_ip="192.168.1.5",
                      edg_port=10010,
                      edg_mode=0)
robot.servo_move_enable(1)
        
while(1):
    pos=[0,0,0,0,0,0]
    print(pos)
    robot.edg_servo_p(end_pos=pos,
                    move_mode=1,
                    step_num=1,
                    robot_index=0)
    time.sleep(0.008)


