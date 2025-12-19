from loguru import logger
import sys
from typing import Any
import time
import threading
from .jaka_lib_2_3_0 import jkrc
from ..robot import Robot
from .modbus_tcp import ModbusTCP
from .config_jakaS12 import JakaS12Config
from .jakaS12_bus import JakaS12Bus
from lerobot.cameras.utils import make_cameras_from_configs
from lerobot.Dav1nGen_utils.fps_monitor import FPSMonitor


class JakaS12(Robot):

    config_class = JakaS12Config
    name: str = "jakaS12"
    id: str = "jakaS12"

    def __init__(self, config: JakaS12Config) -> None:
        # Config
        self._config: JakaS12Config = config

        # Arm
        self._arm_ip: str = self._config.arm_ip
        self._is_connected: bool = False
        self._joint_position: tuple = (0, 0, 0, 0, 0, 0)
        self._cart_position: tuple = (0, 0, 0, 0, 0, 0)
        self._EE_torque: tuple = (0, 0, 0, 0, 0, 0)
        self._cartesian_space_position_diff: dict[str, float] = {}
        self._robot = jkrc.RC(self._arm_ip)
        self.bus = None

        # Sucker
        self._sucker_ip: str = self._config.sucker_ip
        self._sucker_port: int = self._config.sucker_port
        self._coils_address: int = self._config.coils_address
        self._sucker: ModbusTCP = ModbusTCP(ip=self._sucker_ip,
                                            port=self._sucker_port)
        self._sucker_state: bool = False

        # Debug monitor
        # self._monitor = FPSMonitor()

    def connect(self) -> None:

        # Connect to arm
        try:
            logger.info(f"Logging in to robot at {self._arm_ip}")
            self._robot.login()
        except Exception as e:
            logger.error(f"Failed to login to robot at {self._arm_ip}: {e}")
            sys.exit(1)

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

        # Init EDG extend
        self._robot.edg_init_extend(en=True,
                                    edg_stat_ip=self._arm_ip,
                                    edg_port=10010,
                                    edg_mode=0)

        # Set servo move filter
        # self._robot.servo_move_enable(0)
        # self._robot.servo_speed_foresight(200, 0.4)
        # self._robot.servo_move_use_joint_LPF(0.5)

        # Enable servo mode
        self._robot.servo_move_enable(1)

        logger.info(f"Successfully connected to robot at {self._arm_ip}")

        # Connect to sucker
        self._sucker.connect()

        logger.info(
            f"Successfully connected to sucker at {self._sucker_ip}:{self._sucker_port}"
        )

        # Connect to cameras
        self._cameras = make_cameras_from_configs(self._config.cameras)
        self._cameras["wrist"].connect()
        self._cameras["head"].connect()
        logger.info(f"Successfully connected to _cameras")

        # Arm bus connenct
        self.bus = JakaS12Bus(self._robot)

        self._is_connected = True

    def disconnect(self) -> None:
        if not self._is_connected:
            return

        if self._robot:
            try:
                self._robot.logout()
            except Exception as e:
                logger.warning(f"Error during robot logout: {e}")

        self._is_connected = False
        logger.info(f"Disconnected from robot at {self._arm_ip}")

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    @property
    def _joint_feature(self) -> dict[str, float]:
        joint_position = self._robot.get_joint_position()[1]
        self._joint_position = joint_position

        feature = {}
        for i in range(6):
            name = f"joint{i+1}"

            # The gym_manipulator retrieves data from obs_dict[name._joint_position]
            feature[f"{name}._joint_position"] = self._joint_position[i]

            # When generating a raw dict, the gym_manipulator needs to use name.pos as the key
            feature[f"{name}.pos"] = self._joint_position[i]

        return feature

    @property
    def _cart_position_feature(self) -> dict[str, float]:
        cart_position_feature = {}
        self._cart_positon = self._robot.get_tcp_position()[1]
        cart_position_feature = {
            "x": self._cart_positon[0],
            "y": self._cart_positon[1],
            "z": self._cart_positon[2],
            "rx": self._cart_positon[3],
            "ry": self._cart_positon[4],
            "rz": self._cart_positon[5],
        }

        return cart_position_feature

    # TODO(Dav1nGen): The low-frequency issue needs to be fixed.
    # @property
    # def _EE_torque_feature(self) -> dict[str, float]:
    #     EE_torque_feature = {}
    #     self._EE_torque = self._robot.get_robot_status()[1][21]
    #     # TODO(Dav1nGen): self._EE_torque = self._robot.get_robot_status()[1][21][6]??
    #     EE_torque_feature = {
    #         "x": self._EE_torque[0],
    #         "y": self._EE_torque[1],
    #         "z": self._EE_torque[2],
    #         "rx": self._EE_torque[3],
    #         "ry": self._EE_torque[4],
    #         "rz": self._EE_torque[5],
    #     }

    #     return EE_torque_feature

    @property
    def _cameras_feature(self) -> dict[str, dict]:
        camera_features = {}
        for cam_key, cam in self._cameras.items():
            camera_features[cam_key] = {
                "shape": (cam.height, cam.width),
                "names": ["height", "width"],
                "info": None,
            }
        return camera_features

    @property
    def _sucker_feature(self) -> dict[str, bool]:
        self._sucker_state = self._sucker.read(self._coils_address)
        return {"sucker_state": self._sucker_state}

    @property
    def observation_features(self) -> dict[str, Any]:
        features = {
            **self._joint_feature,
            **self._cart_position_feature,
            # **self._EE_torque_feature,
            **self._sucker_feature,
            **self._cameras_feature
        }
        return features

    def get_observation(self) -> dict[str, Any]:

        # Joint feature
        joint_feature: dict[str, float] = self._joint_feature

        # Cartesian space position feature
        cartesian_space_position_feature: dict[
            str, float] = self._cart_position_feature

        # EE torque feature
        # EE_torque_feature: dict[str, float] = self._EE_torque_feature

        # Sucker feature
        sucker_feature: dict[str, bool] = self._sucker_feature

        # Camera feature
        camera_feature: dict[str, Any] = {}

        # Capture images from _cameras
        for cam_key, cam in self._cameras.items():
            camera_feature[cam_key] = cam.async_read()

        observation_dict = {
            **joint_feature,
            **cartesian_space_position_feature,
            # **EE_torque_feature,
            **sucker_feature,
            **camera_feature
        }

        return observation_dict

    @property
    def action_features(self) -> dict[str, Any]:
        return self._cartesian_space_position_diff

    # Send action to robot
    # Struct same as action_features
    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:

        # Adapt the hardcoded values in the step() function of the gym_manipulator.py file
        if 'cart_pos_diff_dict' in action:
            cart_pos_diff_dict = action['cart_pos_diff_dict']
        elif 'arm_cart_pos_diff_dict' in action:
            cart_pos_diff_dict = action['arm_cart_pos_diff_dict']
        else:
            raise KeyError(
                "Could not find 'cart_pos_diff_dict' or 'arm_cart_pos_diff_dict' in the action."
            )

        self._cartesian_space_position_diff: dict[str,
                                                  float] = cart_pos_diff_dict
        pos_diff = tuple(self._cartesian_space_position_diff.values())

        # logger.debug(f"Sending action to robot: {pos_diff}")

        self._robot.edg_servo_p(end_pos=pos_diff,
                                move_mode=1,
                                step_num=1,
                                robot_index=0)

        return self._cartesian_space_position_diff

    # Processes an action from the keyboard teleoperator and applies it to the robot.
    # This handles components controlled by the keyboard, like the sucker.
    def _from_keyboard_to_base_action(
            self, keyboard_action: dict[str, Any]) -> dict[str, Any]:

        base_action = {}
        if "sucker_state" in keyboard_action:
            desired_sucker_state = keyboard_action["sucker_state"]
            # Only send a command if the state needs to change
            if desired_sucker_state != self._sucker_state:
                self._sucker.write(self._coils_address, desired_sucker_state)
                self._sucker_state = desired_sucker_state
                logger.info(f"Sucker state set to: {self._sucker_state}")
            # The action to be logged is the state itself.
            base_action["sucker_state"] = self._sucker_state
        return base_action

    def is_calibrated(self) -> bool:
        pass

    def calibrate(self) -> None:
        pass

    def configure(self) -> None:
        pass
