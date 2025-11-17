#!/usr/bin/env python3

"""
Example configuration for Jaka S12 teleoperation.

This file shows how to configure the leader and follower robots for teleoperation.
"""

from lerobot.teleoperators.jakaS12_leader.config_jakaS12_leader import JakaS12LeaderConfig
from lerobot.robots.jakaS12.config_jakaS12 import JakaS12Config


# Leader robot configuration (the one being teleoperated)
leader_config = JakaS12LeaderConfig(
    port="192.168.1.100",  # IP address of the leader robot
    id="jaka_leader_1",
    drag_friction_compensation_gain=(80, 80, 80, 80, 80, 80),
    is_block=False,
    joint_speed=3.0,
    joint_acc=3.0
)

# Follower robot configuration (the one following the leader)
follower_config = JakaS12Config(
    port="192.168.1.101",  # IP address of the follower robot
    id="jaka_follower_1",
    is_block=False,
    joint_speed=3.0,
    joint_acc=3.0
)