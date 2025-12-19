from typing import Any
from numpy import float64

from ..robot_bus import RobotBusBase
from ..robot import Robot


class JakaS12Bus(RobotBusBase):

    def __init__(self, jaka_robot):
        self._robot = jaka_robot
        self.motors = {
            "joint1": 0.0,
            "joint2": 0.0,
            "joint3": 0.0,
            "joint4": 0.0,
            "joint5": 0.0,
            "joint6": 0.0,
        }

        joint_positions = self._robot.get_joint_position()[1]
        for i, key in enumerate(self.motors.keys()):
            self.motors[key] = float(joint_positions[i])

    def sync_read(self, dict_name: str) -> dict[str, float64]:
        joint_positions = self._robot.get_joint_position()[1]

        for i, key in enumerate(self.motors.keys()):
            self.motors[key] = float(joint_positions[i])

        return self.motors

    def sync_write(self, dict_name: str, joint_position: dict[str, float64]):
        positions = [joint_position[key] for key in self.motors.keys()]
        self._robot.servo_j(tuple(positions), 1)
