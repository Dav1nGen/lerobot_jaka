from lerobot.robots.jakaS12.jaka_lib_2_2_7 import jkrc

robot = jkrc.RC("192.168.1.3")
robot.login()
robot.power_on()
robot.enable_robot()

a = robot.get_robot_status()
print(a[1][18])