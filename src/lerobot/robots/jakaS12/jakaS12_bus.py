from typing import Any
from numpy import float64
from loguru import logger
import time

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
        position = tuple(joint_position.values())

        logger.debug(f"reset joint position to {position}")
        # self._robot.edg_servo_j(tuple(position),
        #                         move_mode=1,
        #                         step_num=100,
        #                         robot_index=0)
        
        self._robot.edg_servo_j(joint_pos=position,
                  move_mode=1,
                  step_num=100000,
                  robot_index=0)
        # result = self._robot.joint_move(position, 0, True, 1)
        
        