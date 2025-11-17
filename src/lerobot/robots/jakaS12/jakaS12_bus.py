import robot_bus
from typing import Any
from numpy import float64
from ..robot import Robot


class JakaS12Bus(robot_bus):

    def __init__(self, jaka_robot):
        self._robot = jaka_robot
        self._motors = {
            "joint1": float64,
            "joint2": float64,
            "joint3": float64,
            "joint4": float64,
            "joint5": float64,
            "joint6": float64
        }
        self._motors = self._robot.get_joint_position()[1]

    def sync_read(self, dict_name: str) -> dict[str, float64]:
        self._motors = self._robot.get_joint_position()[1]
        return self._motors

    def sync_write(self, dict_name: str, joint_position: dict[str, float64]):
        self._robot.servo_j(joint_position)
