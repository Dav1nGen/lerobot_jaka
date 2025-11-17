from lerobot.robots.jakaS12.jaka_lib_2_3_0 import jkrc

robot = jkrc.RC("192.168.1.3")
robot.login()
robot.power_on()
robot.enable_robot()
robot.drag_mode_enable(False)