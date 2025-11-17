#!/usr/bin/env python3

"""
Example script for using Jaka S12 as a teleoperator with a follower robot.

This script demonstrates how to:
1. Set up a Jaka S12 leader robot as a teleoperator
2. Connect to both leader and follower robots
3. Transfer movements from leader to follower in real-time
"""

import time
import logging
from typing import Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import LeRobot modules
try:
    from lerobot.teleoperators.jakaS12_leader import JakaS12Leader
    from lerobot.teleoperators.jakaS12_leader.config_jakaS12_leader import JakaS12LeaderConfig
    from lerobot.robots.jakaS12 import Jaka
    from lerobot.robots.jakaS12.config_jakaS12 import JakaS12Config
    LEROBOT_AVAILABLE = True
except ImportError as e:
    logger.error(f"LeRobot modules not available: {e}")
    LEROBOT_AVAILABLE = False


def create_leader_teleoperator() -> JakaS12Leader:
    """Create and configure the Jaka S12 leader teleoperator."""
    # Create configuration for the leader robot
    leader_config = JakaS12LeaderConfig(
        port="192.168.1.100",  # IP of the leader robot
        id="jaka_leader_1"
    )
    
    # Create the leader teleoperator
    leader = JakaS12Leader(leader_config)
    
    return leader


def create_follower_robot() -> Jaka:
    """Create and configure the Jaka S12 follower robot."""
    # Create configuration for the follower robot
    follower_config = JakaS12Config(
        port="192.168.1.101",  # IP of the follower robot
        id="jaka_follower_1"
    )
    
    # Create the follower robot
    follower = Jaka(follower_config)
    
    return follower


def teleoperate_robot(leader: JakaS12Leader, follower: Jaka) -> None:
    """Main teleoperation loop."""
    logger.info("Starting teleoperation...")
    
    try:
        # Connect to both robots
        logger.info("Connecting to leader robot...")
        leader.connect()
        
        logger.info("Connecting to follower robot...")
        follower.connect()
        
        # Configure robots
        leader.configure()
        follower.configure()
        
        logger.info("Robots connected and configured. Starting teleoperation loop...")
        logger.info("Press Ctrl+C to stop")
        
        # Teleoperation loop
        while True:
            # Get current state from leader
            action = leader.get_action()
            
            # Send action to follower
            # For Jaka robots, we typically send joint positions
            follower_action = {
                "joint_position": [
                    action["joint_1"],
                    action["joint_2"],
                    action["joint_3"],
                    action["joint_4"],
                    action["joint_5"],
                    action["joint_6"]
                ]
            }
            
            # Send the action to the follower robot
            follower.send_action(follower_action)
            
            # Small delay to control loop frequency
            time.sleep(0.01)  # 100Hz loop
            
    except KeyboardInterrupt:
        logger.info("Teleoperation stopped by user")
    except Exception as e:
        logger.error(f"Error during teleoperation: {e}")
    finally:
        # Disconnect from both robots
        try:
            leader.disconnect()
            logger.info("Leader robot disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting leader robot: {e}")
            
        try:
            follower.disconnect()
            logger.info("Follower robot disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting follower robot: {e}")


def main():
    """Main function."""
    if not LEROBOT_AVAILABLE:
        logger.error("LeRobot modules not available. Please install lerobot.")
        return
    
    try:
        # Create leader teleoperator and follower robot
        leader = create_leader_teleoperator()
        follower = create_follower_robot()
        
        # Run teleoperation
        teleoperate_robot(leader, follower)
        
    except Exception as e:
        logger.error(f"Failed to run teleoperation: {e}")


if __name__ == "__main__":
    main()