import abc
import builtins
from pathlib import Path
from typing import Any


class RobotBusBase(abc.ABC):
    """
    Abstract bus interface required by GymManipulator.
    The interface that must be implemented:
    - get_joint_positions
    - get_joint_velocities
    - set_joint_positions
    """

    def __init__(self):
        # List of joint *names* used by the environment
        # Example: ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6"]
        self._motors = []

    @abc.abstractmethod
    def sync_read(self, dict_name: str):
        """
        Essential function
        Returns current joint positions (list or np.array).
        Example output: [0.1, -0.5, 1.2, ...]
        """
        pass

    @abc.abstractmethod
    def sync_write(self, dict_name: str, positions: dict):
        """
        Essential function
        Send position command to robot.
        'positions' is a list of joint targets.
        """
        pass
