from ..config import RobotConfig
from dataclasses import dataclass, field
from lerobot.cameras import CameraConfig
from lerobot.cameras.opencv import OpenCVCameraConfig
from lerobot.cameras.realsense import RealSenseCameraConfig


@RobotConfig.register_subclass("jakaS12")
@dataclass
class JakaS12Config(RobotConfig):

    # Arm
    arm_ip: str = "192.168.1.5"

    # Sucker parameter
    sucker_ip: str = "192.168.1.8"
    sucker_port: int = 502
    coils_address: int = 8

    # Cameras
    cameras: dict[str, CameraConfig] = field(
        default_factory=lambda: {
            "head":
            RealSenseCameraConfig(
                # D435I
                serial_number_or_name="243422072128",
                width=640,
                height=480,
                fps=30,
                color_mode="rgb"
            ),
            "wrist":
            RealSenseCameraConfig(
                # D435
                serial_number_or_name="346522072291",
                width=640,
                height=480,
                fps=30,
                color_mode="rgb"
            ),
        })
