from dataclasses import dataclass
from ..config import TeleoperatorConfig


@TeleoperatorConfig.register_subclass("jakaS12_leader")
@dataclass
class JakaS12LeaderConfig(TeleoperatorConfig):
    
    # Arm parameters
    arm_ip: str = "192.168.1.3"
    drag_friction_compensation_gain: tuple = (80, 80, 80, 80, 80, 80)
    use_gripper: bool = False

    # Other parameters
    is_block: bool = False
    joint_speed: float = 3.0
    joint_acc: float = 3.0
