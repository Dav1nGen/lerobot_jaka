# !/usr/bin/env python.

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import hw_to_dataset_features
from lerobot.processor import make_default_processors
from lerobot.robots.jakaS12 import JakaS12, JakaS12Config
from lerobot.scripts.lerobot_record import record_loop
from lerobot.teleoperators.keyboard import KeyboardSuckerTeleop, KeyboardSuckerTeleopConfig
from lerobot.teleoperators.jakaS12_leader import JakaS12Leader, JakaS12LeaderConfig
from lerobot.teleoperators.utils import TeleopEvents
from lerobot.utils.constants import ACTION, OBS_STR
from lerobot.utils.utils import log_say
from loguru import logger 

NUM_EPISODES = 2
FPS = 30
EPISODE_TIME_SEC = 30
RESET_TIME_SEC = 10
TASK_DESCRIPTION = "FPC insert"
HF_REPO_ID = "Dav1nGen/data_1"

# Create the robot and teleoperator configurations
robot_config = JakaS12Config(arm_ip="192.168.1.5",
                             sucker_ip="192.168.1.8",
                             id="JakaS12")
leader_arm_config = JakaS12LeaderConfig(arm_ip="192.168.1.3",
                                        id="JakaS12_leader_arm")
keyboard_config = KeyboardSuckerTeleopConfig(sucker_ip="192.168.1.8",
                                             sucker_port=502)

# Initialize the robot and teleoperator
robot = JakaS12(robot_config)
leader_arm = JakaS12Leader(leader_arm_config)
keyboard = KeyboardSuckerTeleop(keyboard_config)

teleop_action_processor, robot_action_processor, robot_observation_processor = make_default_processors(
)

# Configure the dataset features
action_features = hw_to_dataset_features(robot.action_features, ACTION)
obs_features = hw_to_dataset_features(robot.observation_features, OBS_STR)
dataset_features = {**action_features, **obs_features}

# Create the dataset
dataset = LeRobotDataset.create(
    repo_id=HF_REPO_ID,
    fps=FPS,
    features=dataset_features,
    robot_type=robot.name,
    use_videos=True,
    image_writer_threads=4,
)

robot.connect()
leader_arm.connect()
keyboard.connect()

events = {
    "stop_recording": False,
    "rerecord_episode": False,
    "exit_early": False
}

if not robot.is_connected or not leader_arm.is_connected or not keyboard.is_connected:
    raise ValueError("Robot or teleop is not connected!")

print("Starting record loop...")
recorded_episodes = 0
while recorded_episodes < NUM_EPISODES and not events["stop_recording"]:
    log_say(f"Recording episode {recorded_episodes}")

    # Main record loop
    record_loop(
        robot=robot,
        events=events,
        fps=FPS,
        dataset=dataset,
        teleop=[leader_arm, keyboard],
        control_time_s=EPISODE_TIME_SEC,
        single_task=TASK_DESCRIPTION,
        display_data=True,
        teleop_action_processor=teleop_action_processor,
        robot_action_processor=robot_action_processor,
        robot_observation_processor=robot_observation_processor,
    )

    teleop_events = keyboard.get_teleop_events()
    logger.info(f"get_teleop_events !")
    if teleop_events[TeleopEvents.TERMINATE_EPISODE]:
        events["stop_recording"] = True

    # Reset the environment if not stopping or re-recording
    if not events["stop_recording"] and ((recorded_episodes < NUM_EPISODES - 1)
                                         or events["rerecord_episode"]):
        log_say("Reset the environment")
        record_loop(
            robot=robot,
            events=events,
            fps=FPS,
            teleop=[leader_arm, keyboard],
            control_time_s=RESET_TIME_SEC,
            single_task=TASK_DESCRIPTION,
            display_data=True,
            teleop_action_processor=teleop_action_processor,
            robot_action_processor=robot_action_processor,
            robot_observation_processor=robot_observation_processor,
        )

    if events["rerecord_episode"]:
        log_say("Re-record episode")
        events["rerecord_episode"] = False
        events["exit_early"] = False
        dataset.clear_episode_buffer()
        continue

    # Save episode
    dataset.save_episode()
    recorded_episodes += 1

# Clean up
log_say("Stop recording")
robot.disconnect()
leader_arm.disconnect()
keyboard.disconnect()

dataset.finalize()
# dataset.push_to_hub()
