from loguru import logger
from typing import Any
import numpy as np
import time
import threading
import sys

from .jaka_lib_2_3_0 import jkrc
# import jkrc
from ..teleoperator import Teleoperator
from .config_jakaS12_leader import JakaS12LeaderConfig


class JakaS12Leader(Teleoperator):

    config_class = JakaS12LeaderConfig
    name = "jakaS12_leader"

    # Constructor
    def __init__(self, config: JakaS12LeaderConfig):
        # Config
        self._config: JakaS12LeaderConfig = config

        # Arm
        self._arm_ip: str = self._config.arm_ip
        self._drag_friction_compensation_gain: tuple = self._config.drag_friction_compensation_gain
        self._cart_space_position: tuple = (0, 0, 0, 0, 0, 0)
        self._last_cart_space_position: tuple = (0, 0, 0, 0, 0, 0)
        self._cart_space_position_diff: tuple = (0, 0, 0, 0, 0, 0)
        self._robot = jkrc.RC(self._arm_ip)

        # States
        self._is_connected: bool = False
        self._is_running: bool = False

        # Connect and init robot
        self.connect()

        # Thread for getting joint position diff
        self._lock = threading.Lock()
        self._joint_position_diff_thread = threading.Thread(
            target=self._get_cartesian_space_position_diff, daemon=True)
        self._joint_position_diff_thread.start()

    #################################
    ########Lerobot interface########
    #################################

    # Connect to robot
    def connect(self, calibrate: bool = True) -> None:

        # Login to robot
        try:
            logger.info(f"Logging in to robot at {self._arm_ip}")
            self._robot.login()
        except Exception as e:
            logger.error(f"Failed to login to robot at {self._arm_ip}: {e}")
            sys.exit(1)

        # Power on robot
        try:
            logger.info(f"Powering on robot at {self._arm_ip}")
            self._robot.power_on()
        except Exception as e:
            logger.error(f"Failed to power on robot at {self._arm_ip}: {e}")
            sys.exit(1)

        # Enable robot
        try:
            logger.info(f"Enable robot at {self._arm_ip}")
            self._robot.enable_robot()
        except Exception as e:
            logger.error(f"Failed to enable robot at {self._arm_ip}: {e}")

        # Init drag mode parameter
        self._robot.enable_admittance_ctrl(0)
        self._robot.set_torque_sensor_mode(0)
        self._robot.set_torsenosr_brand(2)
        self._robot.set_torque_sensor_mode(1)
        logger.info(f"Torque senser open!")
        self._robot.set_compliant_type(1, 1)
        logger.info(f"Inint sensor comple")
        logger.info(f"Ready to run")
        self._robot.zero_end_sensor()
        time.sleep(1)

        # Set admittance control parameters
        self._robot.set_admit_ctrl_config(0, 1, 10, 5, 0, 0)
        self._robot.set_admit_ctrl_config(1, 1, 10, 5, 0, 0)
        self._robot.set_admit_ctrl_config(2, 1, 10, 5, 0, 0)
        self._robot.set_admit_ctrl_config(3, 1, 10, 0, 0, 0)
        self._robot.set_admit_ctrl_config(4, 1, 10, 0, 0, 0)
        self._robot.set_admit_ctrl_config(5, 1, 10, 0, 0, 0)

        # Enable admittance control
        self._robot.enable_admittance_ctrl(1)
        logger.info(f"Enable_admittance_ctrl open!")

        # Init parameters
        self._init_parameters()

        self._is_connected = True
        self._is_running = True
        logger.info(f"Successfully connected to robot at {self._arm_ip}")

    # Disconnect to robot
    def disconnect(self) -> None:
        if not self._is_connected:
            return

        if self._robot:
            try:
                self._robot.logout()
            except Exception as e:
                logger.warning(f"Error during robot logout: {e}")

        self._is_connected = False
        self._is_running = False
        logger.info(f"Disconnected from robot at {self._arm_ip}")

    # Get connection status
    @property
    def is_connected(self) -> bool:
        return self._is_connected

    # Robot action features(sucker and cartesian position)
    @property
    def action_features(self) -> dict:
        """Return a description of the action features."""
        return {
            "shape": (6,),
            "dtype": "float32",
            "names": ["x", "y", "z", "rx", "ry", "rz"],
        }

    # Get the cartesian position difference of the remote control arm in each cycle
    def get_action(self) -> dict[str, Any]:
        with self._lock:
            # self._cart_space_position_diff is a tuple
            action_np = np.array(self._cart_space_position_diff, dtype=np.float32)

        action_names = self.action_features["names"]
        cart_pos_diff_dict = {name: action_np[i] for i, name in enumerate(action_names)}
        return {"cart_pos_diff_dict": cart_pos_diff_dict}

    @property
    def feedback_features(self) -> dict[str, type]:
        pass

    def send_feedback(self, feedback: dict[str, Any]) -> None:
        pass

    @property
    def is_calibrated(self) -> bool:
        pass

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass

    def get_teleop_events(self) -> dict[str, bool]:
        with self._lock:
            # A simple heuristic for intervention: if the arm has moved.
            # Using only translation part for simplicity.
            pos_diff = np.array(self._cart_space_position_diff[:3])
            is_intervention = np.linalg.norm(pos_diff) > 1e-5  # Threshold for movement

        return {
            "grip": True,
            "ungrip": False,
            "finish_episode": False,
            "rerecord_episode": False,
            "is_intervention": is_intervention,
        }

    #############################
    ########Custom method########
    #############################

    # Initialize robot parameters
    def _init_parameters(self) -> None:
        self._cart_space_position = self._robot.get_tcp_position()[1]
        self._last_cart_space_position = self._robot.get_tcp_position()[1]
        logger.info(f"Initialize robot parameters {self._arm_ip} successfully")

    # Update cartesian space position diff in each cycle
    def _get_cartesian_space_position_diff(self) -> None:
        while self._is_running:
            self._last_cart_space_position = self._cart_space_position
            
            # logger.debug(f"Cartesian space position diff before: {self._cart_space_position}")
            time.sleep(0.05)
            self._cart_space_position = self._robot.get_tcp_position()[1]
            
            # logger.debug(f"Cartesian space position diff later: {self._cart_space_position}")

            # Calculate cart space diff
            cart_space_position_diff = list(
                np.array(self._cart_space_position) -
                np.array(self._last_cart_space_position))

            for i in range(3, 6):
                cart_space_position_diff[i] = -cart_space_position_diff[i]
                
            # logger.debug(f"Cartesian space position diff: {cart_space_position_diff}")

            with self._lock:
                self._cart_space_position_diff = tuple(
                    cart_space_position_diff)
