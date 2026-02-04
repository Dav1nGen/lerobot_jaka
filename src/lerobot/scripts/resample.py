import torch
from tqdm import tqdm
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from pathlib import Path
import os


def resample_dataset_frames(repo_id: str,
                            new_repo_id: str,
                            target_fps: int,
                            root: str = None):
    # 1. 加载源数据集
    old_dataset = LeRobotDataset(repo_id, root=root)
    old_fps = old_dataset.fps
    stride = max(1, round(old_fps / target_fps))

    print(f"🚀 源数据集路径: {old_dataset.root}")
    print(f"🚀 采样步长: {stride} (每 {stride} 帧取 1 帧)")

    # 2. 创建新数据集
    new_dataset = LeRobotDataset.create(repo_id=new_repo_id,
                                        fps=target_fps,
                                        features=old_dataset.features,
                                        robot_type=getattr(
                                            old_dataset.meta, "robot_type",
                                            "unknown"),
                                        root=root)
    print(f"📂 新数据集将保存至: {new_dataset.root}")

    total_frames_added = 0

    # 3. 遍历 Episode
    for ep_idx in range(old_dataset.num_episodes):
        # --- 强力索引获取逻辑 ---
        # 优先使用 LeRobot 内部映射
        if hasattr(old_dataset, "episode_data_index"):
            indices = range(old_dataset.episode_data_index[ep_idx],
                            old_dataset.episode_data_index[ep_idx + 1])
        elif hasattr(old_dataset.meta, "episode_data_index"):
            indices = range(old_dataset.meta.episode_data_index[ep_idx],
                            old_dataset.meta.episode_data_index[ep_idx + 1])
        else:
            # 回退方案：通过直接比较获取索引
            ep_indices = torch.where(
                torch.tensor(old_dataset.hf_dataset["episode_index"]) ==
                ep_idx)[0]
            indices = range(ep_indices[0].item(), ep_indices[-1].item() + 1)

        frames_in_episode = 0

        # 4. 抽样并写入
        for frame_idx in tqdm(indices[::stride], desc=f"Episode {ep_idx}"):
            frame_data = old_dataset[frame_idx]

            # 清理键值
            for k in [
                    "index", "task_index", "frame_index", "episode_index",
                    "frame_id", "timestamp"
            ]:
                frame_data.pop(k, None)

            # 修复图像格式 (CHW -> HWC)
            for key in frame_data:
                if "image" in key and isinstance(frame_data[key],
                                                 torch.Tensor):
                    if frame_data[key].ndim == 3 and frame_data[key].shape[
                            0] <= 4:
                        frame_data[key] = frame_data[key].permute(1, 2, 0)

                # 修复标量维度 () -> (1,)
                if key.startswith("next.") or key in [
                        "reward", "done", "success"
                ]:
                    if torch.is_tensor(
                            frame_data[key]) and frame_data[key].ndim == 0:
                        frame_data[key] = frame_data[key].unsqueeze(0)

            new_dataset.add_frame(frame_data)
            frames_in_episode += 1
            total_frames_added += 1

        # 5. 保存 Episode (关键：产生 .parquet 文件)
        if frames_in_episode > 0:
            new_dataset.save_episode()
            print(f"✅ Episode {ep_idx} 已保存, 包含 {frames_in_episode} 帧")
        else:
            print(f"⚠️ Episode {ep_idx} 没有抽取到任何帧，请检查 stride！")

    print(f"\n✨ 全部完成！总计写入 {total_frames_added} 帧")
    print(f"请检查该目录是否有 data 文件夹: {new_dataset.root}")


if __name__ == "__main__":
    resample_dataset_frames(
        repo_id="/home/joysonrobot/lerobot_dataset/imitation_data_2026_01_26_data1",
        new_repo_id="/home/joysonrobot/lerobot_dataset/imitation_data_2026_01_26_data1_resample_10FPS",
        target_fps=10)
