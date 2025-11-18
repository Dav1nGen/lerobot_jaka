from ..robot_bus import RobotBusBase
from typing import Any
from numpy import float64
from ..robot import Robot


class JakaS12Bus(RobotBusBase):

    def __init__(self, jaka_robot):
        self._robot = jaka_robot
        self.motors: dict[str, float64] = {
            "joint1": float64,
            "joint2": float64,
            "joint3": float64,
            "joint4": float64,
            "joint5": float64,
            "joint6": float64
        }
        joint_positions = self._robot.get_joint_position()[1]
        self.motors = dict(zip(self.motors.keys(), joint_positions))

    def sync_read(self, dict_name: str) -> dict[str, float64]:
        self.motors = self._robot.get_joint_position()[1]
        joint_position = self._robot.get_joint_position()[1]
        return {
            key: pos
            for key, pos in zip(self.motors.keys(), joint_position)
        }

    def sync_write(self, dict_name: str, joint_position: dict[str, float64]):
        self._robot.servo_j(tuple(joint_position))
