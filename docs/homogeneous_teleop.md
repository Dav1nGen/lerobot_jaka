# Using Homogeneous Robot Arms as Teleoperators

This document explains how to use homogeneous robot arms (specifically Jaka S12) as teleoperation controllers in the LeRobot framework.

## Overview

The LeRobot framework supports using one robot arm as a teleoperator to control another robot arm of the same type. This is particularly useful for:
- Training robots through demonstration
- Remote control of robots in hazardous environments
- Collaborative robotics applications

## Implementation Details

### 1. Teleoperator Class Implementation

The `JakaS12Leader` class in `src/lerobot/teleoperators/jakaS12_leader/` implements the teleoperator interface for Jaka S12 robots. Key features include:

- Connection management to the leader robot
- Action retrieval from the leader robot's joint positions
- Feedback handling (for force feedback or other sensory information)
- Calibration and configuration methods

### 2. Robot Class Implementation

The `Jaka` class in `src/lerobot/robots/jakaS12/` implements the robot interface for Jaka S12 robots. It can act as either a leader or follower in teleoperation scenarios.

### 3. Configuration

Both leader and follower robots are configured using dataclasses:
- `JakaS12LeaderConfig` for the teleoperator
- `JakaS12Config` for the robot

## Usage Example

See the example in `examples/jakaS12_teleop/` for a complete implementation of teleoperation between two Jaka S12 robots.

### Basic Usage Pattern

```python
# Create leader teleoperator
leader_config = JakaS12LeaderConfig(port="192.168.1.100")
leader = JakaS12Leader(leader_config)

# Create follower robot
follower_config = JakaS12Config(port="192.168.1.101")
follower = Jaka(follower_config)

# Connect to both robots
leader.connect()
follower.connect()

# Teleoperation loop
while True:
    # Get action from leader
    action = leader.get_action()
    
    # Send action to follower
    follower.send_action(action)
```

## Key Considerations

1. **Network Configuration**: Both robots must be accessible over the network with proper IP addresses.

2. **Calibration**: Proper calibration of both robots is essential for accurate teleoperation.

3. **Safety**: Implement appropriate safety measures, including emergency stops and position limits.

4. **Latency**: Network latency can affect teleoperation performance. Consider using wired connections for better performance.

5. **Coordinate Systems**: Ensure that both robots use compatible coordinate systems for joint positions.