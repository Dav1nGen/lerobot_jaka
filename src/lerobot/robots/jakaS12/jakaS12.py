from loguru import logger
import sys
from typing import Any
import time
from .jaka_lib_2_3_0 import jkrc
from ..robot import Robot
from .modbus_tcp import ModbusTCP
from .config_jakaS12 import JakaS12Config
from lerobot.cameras.utils import make_cameras_from_configs

# TODO: Dav1nGen: 1. Add robot end effector torque


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
        self._cartesian_space_position_diff: dict[str, float] = {}
        self._robot = jkrc.RC(self._arm_ip)

        # Sucker
        self._sucker_ip: str = self._config.sucker_ip
        self._sucker_port: int = self._config.sucker_port
        self._coils_address: int = self._config.coils_address
        self._sucker: ModbusTCP = ModbusTCP(ip=self._sucker_ip,
                                            port=self._sucker_port)
        self._sucker_state: bool = False

        # Connect to arm & sucker & cameras
        self.connect()

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
        logger.info(f"Successfully connected to cameras")

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
        return {
            "joint_1": self._joint_position[0],
            "joint_2": self._joint_position[1],
            "joint_3": self._joint_position[2],
            "joint_4": self._joint_position[3],
            "joint_5": self._joint_position[4],
            "joint_6": self._joint_position[5]
        }

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
            **self._sucker_feature,
            **self._cameras_feature
        }
        return features

    def get_observation(self) -> dict[str, Any]:

        # Joint feature
        joint_feature_dict: dict[str, float] = self._joint_feature

        # Sucker feature
        sucker_feature: dict[str, bool] = self._sucker_feature

        # Capture images from cameras
        for cam_key, cam in self._cameras.items():
            camera_feature: dict[str, Any] = {}
            start = time.perf_counter()
            camera_feature[cam_key] = cam.async_read()
            dt_ms = (time.perf_counter() - start) * 1e3
            # logger.debug(f"{self} read {cam_key}: {dt_ms:.1f}ms")

        observation_dict = {
            **joint_feature_dict,
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
        # pos_diff=(10,0,0,0,0,0)

        logger.debug(f"Sending action to robot: {pos_diff}")
        
        self._robot.edg_servo_p(end_pos=pos_diff,
                                move_mode=1,
                                step_num=50,
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
