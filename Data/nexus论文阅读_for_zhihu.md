---
title: nexus论文阅读
date: 2025-11-29 08:48:08
categories: 计算机
tags:
  - 自动驾驶
  - 论文
cover: /img/cover_28.jpg
abbrlink: 6732346653
description: Decoupled Diffusion Sparks Adaptive Scene Generation 论文阅读
---

![image-20251214092354467](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu@master/Data/nexus论文阅读/image-20251214092354467_1.png)

## 模型结构

![image-20251214095443531](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu@master/Data/nexus论文阅读/image-20251214095443531_1.png)

模型从 **真实驾驶日志** 和 **安全关键数据** 中学习，分别对 **智能体（Agent）** 和 **地图（Map）** 进行编码，然后输入到一个 **Diffusion Transformer**中。

 智能体 token 用时间和去噪步骤进行编码，然后通过注意力机制与地图和动力学进行交互。

具有不同噪声的 token 在一个块内进行调度，以便及时做出反应。每个去噪步骤都会更新并弹出零噪声 token，用下一帧 token 替换它们，从而迭代生成场景。

## 测评指标分析

从2秒历史预测8秒未来。

<img src="https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu@master/Data/nexus论文阅读/image-20260111111351147_1.png" alt="image-20260111111351147" style="zoom:50%;" />

通过一个**滑动窗口** 进行采样 。利用**流水线调度策略**，在每个去噪步骤中，会有已经完成去噪的令牌（代表当前时刻的状态）被“弹出 (Pop)”，同时新的高噪声令牌（代表未来的时刻）会被加入窗口中进行去噪 。

>  也就是始终维持一个 8 秒的逻辑窗口，但每一步只确定当前这一帧的动作，同时保留对未来 8 秒修改的权利，边跑边改。
>
>  那么表一得到这个结果的流程推测就是：
>
>  **输入**：给定 2 秒的历史轨迹作为初始条件。
>
>  **启动**：在 Chunk 中填充未来 8 秒的噪声令牌。
>
>  **循环迭代**：
>
>  ​	执行一次去噪步骤。
>
>  ​	**弹出**：将最左侧（当前时刻  <img src="https://www.zhihu.com/equation?tex=t" alt="t" class="ee_img tr_noresize" eeimg="1"> ）噪声降为 0 的令牌作为该时刻的生成结果。
>
>  ​	**压入**：从右侧（未来时刻）补充一个新的高噪声令牌进入窗口。
>
>  ​	**更新环境**：如果是在闭环场景下，模型会接收其他智能体的新位置，并作为 Context 影响窗口内剩下的高噪声令牌。（准开环？表1在顶层看就是给了最开始2s，吐出来后面的8s，但模型内部会看窗口内的来生成（但本质上还是他的生成结果，应该算是开环吧））
>
>  **结果**：直到这种“弹出”动作持续了 80 个步长，从而凑齐完整的 8 秒轨迹。

<img src="https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu@master/Data/nexus论文阅读/image-20260111112723522_1.png" alt="image-20260111112723522" style="zoom: 50%;" />

它 在 **nuPlan**、**Waymo** 以及自建的 **Nexus-Data** 上测试

<img src="https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu@master/Data/nexus论文阅读/image-20260111112932116_1.png" alt="image-20260111112932116" style="zoom:50%;" />

在指标对比时分别随机提供一个目标点，和自由地生成一个 8 秒的未来，都使用前两秒作为上下文。

### 开环评估

以nuPlan驾驶日志中的所有车辆状态和车道中心线过去2秒的数据为条件，以0.5秒的时间间隔自由生成一个8秒的未来场景。在生成过程中，每个token的噪声水平由调度策略决定。在相应的时间步长中，无效车辆将被忽略。

表1指标，split:**nuPlan Val** 

<img src="https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu@master/Data/nexus论文阅读/image-20260111110132037_1.png" alt="image-20260111110132037" style="zoom: 50%;" />

### Waymo评估

Waymo评估要求基于1秒的历史观测数据生成32个未来场景预测，包括车辆、行人以及骑行者。评估以10Hz的频率进行，将2Hz的模型插值以匹配所需的场景频率。

>  插值。。。。有点绷不住

### 闭环评估

智能体基于2秒的历史观测数据预测一个8秒的轨迹，并采取0.1秒的动作。环境根据智能体的动作更新场景，以10Hz的频率运行。在使用生成模型作为世界生成器的实验中，替换了原始的nuPlan环境。从一个2秒的历史场景开始，它根据智能体的动作生成并更新下一个场景（提前0.1秒）。

![image-20260112103312679](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu@master/Data/nexus论文阅读/image-20260112103312679_1.png)

>  闭环评估用的是另外三个指标
>
>  这怎么还有Waymo啊，感觉论文给的信息有限，去翻翻代码找找吧

### 指标汇总

| **指标名称** | **定义**                                                     |

| ------------ | ------------------------------------------------------------ |

| ADE          | **平均位移误差**：衡量生成轨迹与真实轨迹之间的平均偏差（不计终点及无效点）。 |

|  <img src="https://www.zhihu.com/equation?tex=R_{road}" alt="R_{road}" class="ee_img tr_noresize" eeimg="1">    | **脱靶率/离路率**：车辆中心偏离指定车道中心线的频率，用于衡量生成的道路合规性。 |

|  <img src="https://www.zhihu.com/equation?tex=R_{col}" alt="R_{col}" class="ee_img tr_noresize" eeimg="1">     | **碰撞率**：通过检测智能体边界框是否存在重叠，计算发生碰撞的车辆占比。 |

|  <img src="https://www.zhihu.com/equation?tex=M_k" alt="M_k" class="ee_img tr_noresize" eeimg="1">         | **运动学稳定性**：通过切向/法向加速度及其加加速度（Jerk）的均值来评估轨迹的平顺性与舒适度。 |

| Composite    | **综合指标**：对比生成场景分布（32次采样）与真实分布在速度、距离、碰撞等维度的似然度。（给WOD用的） |

| Score        | **规划得分**：nuPlan闭环评估主指标。综合考虑舒适度、碰撞、路权、变道及里程完成度（1为成功，0为失败）。 |

|  <img src="https://www.zhihu.com/equation?tex=S_{col}" alt="S_{col}" class="ee_img tr_noresize" eeimg="1">     | **规划碰撞率**：Score的子指标，专门衡量规划轨迹中的碰撞情况。 |

|  <img src="https://www.zhihu.com/equation?tex=S_p" alt="S_p" class="ee_img tr_noresize" eeimg="1">         | **距离完成率**：Score的子指标，衡量规划轨迹完成预设里程的比例。 |


### 基础指标

ADE,   <img src="https://www.zhihu.com/equation?tex=R_{col}" alt="R_{col}" class="ee_img tr_noresize" eeimg="1"> ,  <img src="https://www.zhihu.com/equation?tex=R_{road}" alt="R_{road}" class="ee_img tr_noresize" eeimg="1"> ,  <img src="https://www.zhihu.com/equation?tex=M_k" alt="M_k" class="ee_img tr_noresize" eeimg="1"> 

```bash
sh ./scripts/testing/test_nexus_metrics.sh
```

>  真难读啊，比vbd难读好多，一层层的封装，到最后也没能搞懂整个流程，封装的特别神奇，Pytorch Lighting封装了一个test函数，但查整个项目也找不到test_step函数，一大堆指标计算函数是hydra包含的yaml指定的，不过虽然流程没搞懂，翻项目和参考论文把计算对应代码找到了

```yaml
aggregated_metric:
  agent_behavior_prediction:
    _target_: nuplan_extent.planning.training.modeling.aggregated_metrics.behavior_prediction.BehaviorPredictionMetric
    _convert_: all
    name: agent_bp
    prediction_output_key: behavior_pred
    exclude_ego: true
    use_only_ego: false
  intent_condtioned_agent_behavior_prediction:
    _target_: nuplan_extent.planning.training.modeling.aggregated_metrics.behavior_prediction.BehaviorPredictionMetric
    _convert_: all
    name: intent_conditioned_agent_bp
    prediction_output_key: intent_conditioned_behavior_pred
    exclude_ego: true
    use_only_ego: false
  collision_rate_bp:
    _target_: nuplan_extent.planning.training.modeling.aggregated_metrics.collision_rate.CollisionMetric
    _convert_: all
    name: collision_rate_bp
    prediction_output_key: behavior_pred
    exclude_ego: false
    use_only_ego: false
  collision_rate_gp:
    _target_: nuplan_extent.planning.training.modeling.aggregated_metrics.collision_rate.CollisionMetric
    _convert_: all
    name: collision_rate_gp
    prediction_output_key: intent_conditioned_behavior_pred
    exclude_ego: false
    use_only_ego: false
  traj_metric_gp:
    _target_: nuplan_extent.planning.training.modeling.aggregated_metrics.traj_metric.TrajMetric
    _convert_: all
    name: traj_metric_gp
    prediction_output_key: intent_conditioned_behavior_pred
    exclude_ego: false
    use_only_ego: false
  traj_metric_bp:
    _target_: nuplan_extent.planning.training.modeling.aggregated_metrics.traj_metric.TrajMetric
    _convert_: all
    name: traj_metric_bp
    prediction_output_key: behavior_pred
    exclude_ego: false
    use_only_ego: false
  time:
    _target_: nuplan_extent.planning.training.modeling.aggregated_metrics.time.TimeMetric
    _convert_: all
    name: time
    prediction_output_key: time_consume
```

### 模型前向推理得到评估计算所需数据

代码位置nuplan_extent/planning/training/modeling/models/nexus.py

```python

    def forward_validation(self, input_features: FeaturesType) -> Dict:
        # Encode image
        # global_context = self.image_encoder(input_features)  # B, L, C
        input_features['scene_tensor'].tensor = input_features['scene_tensor'].tensor[...,:8] # to exclude agents id from scene_tensor
        scene_tensor_features: SceneTensor = input_features["scene_tensor"]
        global_context = self.global_encoder(scene_tensor_features)

        n_past_timesteps = 4 + 1  # 1 current timestep + 4 past timesteps
        present_mask = scene_tensor_features.validity[:, :, :n_past_timesteps].any(
            dim=-1
        )
        for batch_idx in range(scene_tensor_features.tensor.shape[0]):
    scene_tensor_features.validity[batch_idx, ~present_mask[batch_idx], :] = 0
```

定义前 5 个时间步为“历史”（4个2HZ过去帧和现在帧，与论文一致的2s)。如果一个智能体在这 5 帧内一次都没有出现过（`any(dim=-1)` 为 False），则认为该智能体在当前场景中无效。

将那些在历史记录中完全不存在的智能体的 `validity` 全部置 0，防止模型去预测这些不存在的对象。

```python
        task_mask_bp = torch.zeros_like(scene_tensor_features.tensor)
        task_mask_bp[:, :, :n_past_timesteps] = 1

        time_consume = 0
        time_start = time.time()
        xpred, _ = self.diffuser.sample(
            scene_tensor=scene_tensor_features.tensor,
            valid_mask=scene_tensor_features.validity,
            global_context=global_context,
            z_t=None,
            keep_mask=task_mask_bp,
            raw_map=self.extract_raw_map(scene_tensor_features)
            # use_guidance_fn=True,
        )
        time_end = time.time()
        time_consume += time_end - time_start
```

将历史帧掩码设为1，然后扔进扩散模型采样。

```python
 valid_mask = scene_tensor_features.validity
        intent_conditioned_task_mask_bp = torch.zeros_like(scene_tensor_features.tensor)
        intent_conditioned_task_mask_bp[:, :, :n_past_timesteps] = 1
        last_valid_indices = torch.max(
            (valid_mask == 1).float()
            * torch.arange(valid_mask.shape[-1], device=valid_mask.device).float(),
            dim=-1,
        )[1]
        batch_indices = torch.arange(valid_mask.shape[0], device=valid_mask.device)[
            :, None
        ].expand(-1, valid_mask.shape[1])
        agent_indices = torch.arange(valid_mask.shape[1], device=valid_mask.device)[
            None, :
        ].expand(valid_mask.shape[0], -1)
        intent_conditioned_task_mask_bp[
            batch_indices, agent_indices, last_valid_indices
        ] = 1.0
        time_start = time.time()
        intent_conditioned_xpred, _ = self.diffuser.sample(
            scene_tensor=scene_tensor_features.tensor,
            valid_mask=scene_tensor_features.validity,
            global_context=global_context,
            z_t=None,
            keep_mask=intent_conditioned_task_mask_bp,
            raw_map=self.extract_raw_map(scene_tensor_features)
            # use_guidance_fn=True,
        )
        time_end = time.time()
        time_consume += time_end - time_start
        time_consume /= 2
```

这个采样与前面的相比是终点采样设为1，生成从起点到终点的意图路径，而前一个是自由路径

```python
        return dict(
            behavior_prediction_out={
                "behavior_pred": xpred,
                "intent_conditioned_behavior_pred": intent_conditioned_xpred,
                "scene_tensor_gt": scene_tensor_features.tensor,
                "valid_mask": scene_tensor_features.validity,
                "task_mask": task_mask_bp,
                "time_consume": time_consume,
                "road_graph": scene_tensor_features.road_graph,
                "road_graph_validity": scene_tensor_features.road_graph_validity,
            }
        )
```

| **键名 (Key)**                         | **数据内容**                     |

| -------------------------------------- | -------------------------------- |

| **`behavior_pred`**                    | 自由预测轨迹                     |

| **`intent_conditioned_behavior_pred`** | 意图约束轨迹                     |

| **`scene_tensor_gt`**                  | 真实轨迹张量(估计算ADE，FDE用的) |

| **`valid_mask`**                       | 有效性掩码（有效的智能体为1）    |

| **`task_mask`**                        | 任务约束掩码（只有前5帧为1那个） |

| **`time_consume`**                     | 采样平均耗时                     |

| **`road_graph`**                       | 道路图数据                       |

| **`road_graph_validity`**              | 地图有效性掩码                   |


### 指标计算

代码位置在代码位置nuplan_extent/planning/training/modeling/aggregated_metrics

#### ADE(behavior_prediction)

```python
    def update(self, predictions: TargetsType, targets: TargetsType) -> None:
        if "behavior_prediction_out" not in predictions:
            return

        if self._key not in predictions["behavior_prediction_out"]:
            return

        valid = predictions["behavior_prediction_out"]["valid_mask"][
            :, :, -self._nt :
        ]  # B, NA, NT
        gt = predictions["behavior_prediction_out"]["scene_tensor_gt"][
            :, :, -self._nt :
        ]
        pred = predictions["behavior_prediction_out"][self._key][:, :, -self._nt :]

        gt = decode_scene_tensor(gt)
        pred = decode_scene_tensor(pred)

        if self._use_only_ego:
            valid = valid[:, self._ego_idx : self._ego_idx + 1]
            gt = gt[:, self._ego_idx : self._ego_idx + 1]
            pred = pred[:, self._ego_idx : self._ego_idx + 1]

        if self._exclude_ego:
            valid[:, self._ego_idx] = 0

        self.entries_at_t += valid.sum(axis=(0, 1))  # NT

        errors = torch.norm(gt[..., :2] - pred[..., :2], dim=-1)  # B, NA, NT

        errors *= valid
        self.displacement_at_t += errors.sum(axis=(0, 1))
```


<img src="https://www.zhihu.com/equation?tex=\text{Distance} = \sqrt{(\Delta x)^2 + (\Delta y)^2}" alt="\text{Distance} = \sqrt{(\Delta x)^2 + (\Delta y)^2}" class="ee_img tr_noresize" eeimg="1">

#### collided_aggregated_metrics

```python
    def update(self, predictions: TargetsType, targets: TargetsType) -> torch.Tensor:
        """
        Computes the metric given the ground truth targets and the model's predictions.

        :param predictions: model's predictions
        :param targets: ground truth targets from the dataset
        :return: metric scalar tensor
        """
        predicted_tokenized_arrays = predictions['predicted_tokenized_arrays']
        for i in range(predicted_tokenized_arrays.shape[0]):
            collision_rate = gutils.calculate_collision_rate_batch(
                predicted_tokenized_arrays[i], 
                ego_only=self._is_ego)
            self.batch += 1
            self.collision_rate += collision_rate
```

发生碰撞的场景占比

####  <img src="https://www.zhihu.com/equation?tex=R_{col}" alt="R_{col}" class="ee_img tr_noresize" eeimg="1"> （collision_rate）

```python
    def update(self, predictions: TargetsType, targets: TargetsType) -> None:
        if "behavior_prediction_out" not in predictions:
            return

        if self._key not in predictions["behavior_prediction_out"]:
            return

        valid = predictions["behavior_prediction_out"]["valid_mask"][
            :, :, -self._nt :
        ]  # B, NA, NT
        gt = predictions["behavior_prediction_out"]["scene_tensor_gt"][
            :, :, -self._nt :
        ]
        pred = predictions["behavior_prediction_out"][self._key][:, :, -self._nt :]

        gt = decode_scene_tensor(gt)
        pred = decode_scene_tensor(pred)

        self.entries_at_t += valid.sum(axis=(0, 1))  # NT

        collied_agents = self.calculate_collision_rate_batch(pred.cpu().numpy(), valid.cpu().numpy(), self._use_only_ego)
        collied_agents = torch.tensor(collied_agents).to(self.collision_at_t.device)
        self.collision_at_t += collied_agents
```

发生碰撞的车占总数的比例

#### WOD（sim_agents_metrics）

waymo官方要求，和上一篇看的vbd差不多

#### time

统计推理耗时

####  <img src="https://www.zhihu.com/equation?tex=R_{road}" alt="R_{road}" class="ee_img tr_noresize" eeimg="1"> ,  <img src="https://www.zhihu.com/equation?tex=M_k" alt="M_k" class="ee_img tr_noresize" eeimg="1"> （TrajMetric）

 <img src="https://www.zhihu.com/equation?tex=M_k" alt="M_k" class="ee_img tr_noresize" eeimg="1"> 

```python
def mertic_comfort(pred_traj: torch.tensor, delta_t=0.5):
    """
    \text{LonAcc}=\frac{1}{T} \sum_{t=1}^{T}\left|a_{\mathrm{lon}}^{t}\right|

    \text{LonJerk}=\frac{1}{T} \sum_{t=1}^{T}\left|\frac{d a_{\mathrm{lon}}^{t}}{d t}\right|

    \text{LatAcc}=\frac{1}{T} \sum_{t=1}^{T}\left|a_{\text {lat }}^{t}\right|

    \text{LatJerk}=\frac{1}{T} \sum_{t=1}^{T}\left|\frac{d a_{\mathrm{lat}}^{t}}{d t}\right|

    """
    delta = pred_traj[..., 1:, :2] - pred_traj[..., :-1, :2]
    delta = (delta[...,0]**2 + delta[...,1]**2)**0.5
    velocities = delta / delta_t
    delta_v = velocities[..., 1:] - velocities[..., :-1]
    acceleration = delta_v / delta_t
    delta_a = acceleration[..., 1:] - acceleration[..., :-1]
    jerk = delta_a / delta_t

    traj_angles = torch.atan2(pred_traj[..., 3], pred_traj[..., 2])
    angle_delta = torch.abs(traj_angles[..., 1:] - traj_angles[..., :-1])
    angle_delta = (angle_delta + math.pi) % (2 * math.pi) - math.pi
    angle_velocities = angle_delta / delta_t
    angle_delta_v = angle_velocities[..., 1:] - angle_velocities[..., :-1]
    angle_acceleration = angle_delta_v / delta_t
    angle_delta_a = angle_acceleration[..., 1:] - angle_acceleration[..., :-1]
    angle_jerk = angle_delta_a / delta_t


    # lon acc
    acceleration_lon = acceleration # x
    # max_acc_lon = torch.max(acceleration_lon, dim=1)[0]
    max_acc_lon = acceleration_lon
    mean_acc_lon = torch.abs(max_acc_lon).mean()

    # lon jerk
    jerk_lon = jerk # x
    # max_jerk_lon = torch.max(jerk_lon, dim=1)[0]
    max_jerk_lon = jerk_lon
    mean_jerk_lon = torch.abs(max_jerk_lon).mean()

    # lat acc
    acceleration_lat = angle_acceleration # y
    # max_acc_lat = torch.max(acceleration_lat, dim=1)[0]
    max_acc_lat = acceleration_lat
    mean_acc_lat = torch.abs(max_acc_lat).mean()*180/math.pi

    # lat jerk
    jerk_lat = angle_jerk # x
    # max_jerk_lat = torch.max(jerk_lat, dim=1)[0]
    max_jerk_lat = jerk_lat
    mean_jerk_lat = torch.abs(max_jerk_lat).mean()*180/math.pi

    return mean_acc_lon, mean_jerk_lon, mean_acc_lat, mean_jerk_lat
```

纵向和横向的加速度和加速度的变化率（想到高中物理题了，加速度的变化率是舒适度）

 <img src="https://www.zhihu.com/equation?tex=R_{road}" alt="R_{road}" class="ee_img tr_noresize" eeimg="1"> 

```python
def metric_offroad_rate(scene_tensor, valid_mask, map_tensor, map_valid, lane_threshold=2.75, obs_frames=5):
    """
    Computes the off-road rate for vehicles based on their distances to lane lines.

    A vehicle is considered "in-lane" if at least one valid frame in the first obs_frames is within lane_threshold.
    If any valid frame after obs_frames has a distance greater than lane_threshold, the vehicle is marked as off-road.

    The off-road rate is computed as:
        off-road rate = (# vehicles that went off-road) / (# vehicles that were initially in-lane)

    Parameters:
        scene_tensor (torch.Tensor): [B, NA, NT, D] vehicle tensor (first two dims of D are x, y)
        valid_mask (torch.Tensor): [B, NA, NT] boolean tensor indicating valid vehicle frames
        map_tensor (torch.Tensor): [B, L, N, D] lane tensor (first two dims of D are x, y)
        map_valid (torch.Tensor): [B, L, N, D] boolean tensor indicating valid lane points
        lane_threshold (float): distance threshold for being "in-lane"
        obs_frames (int): number of initial frames for observing in-lane behavior

    Returns:
        offroad_rate (float): Ratio of vehicles that went off-road among those initially in-lane.
    """
    B, NA, NT, _ = scene_tensor.shape

    # Compute the minimum distance from each vehicle position to any lane point
    min_dist = compute_min_distance_torch(scene_tensor, map_tensor, map_valid)  # [B, NA, NT]

    in_lane = torch.zeros(B, NA, dtype=torch.bool, device=scene_tensor.device)
    offroad = torch.zeros(B, NA, dtype=torch.bool, device=scene_tensor.device)

    for b in range(B):
        for i in range(NA):
            # Get valid mask for vehicle i in batch b (shape [NT])
            valid_frames = valid_mask[b, i, :]  # Bool tensor
            if not torch.any(valid_frames[:obs_frames]):
                continue  # Skip if no valid observation in first obs_frames
            # Check if any valid frame in the observation period is within lane threshold
            if torch.any((min_dist[b, i, :obs_frames] <= lane_threshold) & valid_frames[:obs_frames].bool()):
                in_lane[b, i] = True
                # Check subsequent valid frames for off-road condition
                if torch.any((min_dist[b, i, obs_frames:] > lane_threshold) & valid_frames[obs_frames:].bool()):
                    offroad[b, i] = True

    num_in_lane = in_lane.sum().item()
    num_offroad = offroad.sum().item()
    num_valid = torch.any(valid_mask == 1, dim=-1).bool().sum().item()
    offroad_rate = num_offroad / num_valid if num_valid > 0 else 0.0
    count = 1. if num_valid > 0 else 0.0
    return offroad_rate, count
```

计算脱离车道的比例

### 训练数据处理

nuplan_extent/planning/training/caching

预处理是cache_data的处理，主要分析这个函数

```python
assert cfg.cache.cache_path is not None, ...
scenario_builder = build_scenario_builder(cfg)
scenarios = build_scenarios_from_config(cfg, scenario_builder, worker)
```

筛选出符合条件的场景加载进来（脚本默认的是all)

```python
if cfg.get('cache_adv',False):
    # 动态导入对抗生成器
    from third_party.CAT.advgen.adv_generator_nuplan import AdvGenerator
    scenarios = generate_adv_scenarios(cfg, scenarios)
    data_points = [{"scenario": scenario, "cfg": cfg, "adv_info": scenario.adv_info} for scenario in scenarios]
else:
    data_points = [{"scenario": scenario, "cfg": cfg} for scenario in scenarios]
```

默认常规，即仅保留原始场景信息，有对抗模式，尝试修改他车行为来影响自车，若成功制造碰撞，则保存该对抗信息（adv_info），应该是为了增强数据吧。

```python
logger.info("Starting dataset caching of %s files...", str(len(data_points)))
cache_results = worker_map(worker, cache_scenarios, data_points)
```

#### cache_scenarios核心场景处理函数

```python
model = build_torch_module_wrapper(cfg.model)
feature_builders = model.get_list_of_required_feature()
target_builders = model.get_list_of_computed_target()
del model
```

获取模型需要的输入输出后就可以直接删掉了

```python
        preprocessor = feature_preprocessor(
            cache_path=cfg.cache.cache_path,
            force_feature_computation=cfg.cache.force_feature_computation,
            feature_builders=feature_builders,
            target_builders=target_builders,
        )
```

nuplan自己的特征处理函数

```python
from nuplan.planning.training.preprocessing.feature_preprocessor import FeaturePreprocessor
```

>  服务器上vscode全局搜索特别慢，真奇怪

```python
features, targets, file_cache_metadata = preprocessor.compute_features(scenario)
```

将原始地图和车辆轨迹转为 Tensor，写入磁盘

```python
scenario_num_failures = sum(
    0 if feature.is_valid else 1 for feature in itertools.chain(features.values(), targets.values())
)
scenario_num_successes = len(features.values()) + len(targets.values()) - scenario_num_failures
```

检查valid

#### nuplan数据集官方feature_preprocessor

```python
def compute_features(
        self, scenario: AbstractScenario, iteration: int=0
    ) -> Tuple[FeaturesType, TargetsType, List[CacheMetadataEntry]]:
        """
        Compute features for a scenario, in case cache_path is set, features will be stored in cache,
        otherwise just recomputed
        * perform try/except when not versatile_cache
        :param scenario for which features and targets should be computed
        :return: model features and targets and cache metadata
        """
        all_features: FeaturesType
        all_feature_cache_metadata: List[CacheMetadataEntry]
        all_targets: TargetsType
        all_targets_cache_metadata: List[CacheMetadataEntry]

        all_features, all_feature_cache_metadata = self._compute_all_features(scenario, self._feature_builders, iteration)
        all_targets, all_targets_cache_metadata = self._compute_all_features(scenario, self._target_builders, iteration)

        all_cache_metadata = all_feature_cache_metadata + all_targets_cache_metadata
        return all_features, all_targets, all_cache_metadata
```

算一遍输入特征，和一遍目标特征

```python
    def _compute_all_features(
        self, scenario: AbstractScenario, builders: List[Union[AbstractFeatureBuilder, AbstractTargetBuilder]], iteration: int
    ) -> Tuple[Union[FeaturesType, TargetsType], List[Optional[CacheMetadataEntry]]]:
        """
        Compute all features/targets from builders for scenario
        * perform try/except when versatile_cache
        :param scenario: for which features should be computed
        :param builders: to use for feature computation
        :return: computed features/targets and the metadata entries for the computed features/targets
        """
        # Features to be computed
        all_features: FeaturesType = {}
        all_features_metadata_entries: List[CacheMetadataEntry] = []

        for builder in builders:
            if self._versatile_cache:
                # try:
                feature, feature_metadata_entry = compute_or_load_feature(
                    scenario, self._cache_path, builder, self._storing_mechanism, self._force_feature_computation, iteration, self._versatile_cache,)
                all_features[builder.get_feature_unique_name()] = feature
                all_features_metadata_entries.append(feature_metadata_entry)
                # except Exception as error:
                #     msg = (
                #         f"Failed to compute {builder.get_feature_unique_name()} for scenario token {scenario.token} in log {scenario.log_name}\n"
                #         f"Error: {error}"
                #     )
                #     logger.error(msg)
                #     all_features[builder.get_feature_unique_name()] = None
                #     all_features_metadata_entries.append(None)
            else:
                feature, feature_metadata_entry = compute_or_load_feature(
                    scenario, self._cache_path, builder, self._storing_mechanism, self._force_feature_computation, iteration, self._versatile_cache,)
                all_features[builder.get_feature_unique_name()] = feature
                all_features_metadata_entries.append(feature_metadata_entry)

        return all_features, all_features_metadata_entries
```

遍历需要的builders进行计算

```python
def compute_or_load_feature(
    scenario: AbstractScenario,
    cache_path: Optional[pathlib.Path],
    builder: Union[AbstractFeatureBuilder, AbstractTargetBuilder],
    storing_mechanism: FeatureCache,
    force_feature_computation: bool,
    iteration: int = 0,
    versatile_cache: bool = False,
) -> Tuple[AbstractModelFeature, Optional[CacheMetadataEntry]]:
    """
    Compute features if non existent in cache, otherwise load them from cache
    :param scenario: for which features should be computed
    :param cache_path: location of cached features
    :param builder: which builder should compute the features
    :param storing_mechanism: a way to store features
    :param force_feature_computation: if true, even if cache exists, it will be overwritten
    :return features computed with builder and the metadata entry for the computed feature if feature is valid.
    """
    cache_path_available = cache_path is not None
    # Filename of the cached features/targets
    file_name = (
        cache_path / scenario.log_name / scenario.scenario_type / scenario.token / builder.get_feature_unique_name()
        if cache_path_available
        else None
    )

    # If feature recomputation is desired or cached file doesnt exists, compute the feature
    need_to_compute_feature = (
        force_feature_computation or not cache_path_available or not storing_mechanism.exists_feature_cache(file_name)
    )
    feature_stored_sucessfully = False
    if need_to_compute_feature:
        logger.debug("Computing feature...")
        if isinstance(scenario, CachedScenario):
            raise ValueError(
                textwrap.dedent(
                    f"""
                Attempting to recompute scenario with CachedScenario.
                This should typically never happen, and usually means that the scenario is missing from the cache.
                Check the cache to ensure that the scenario is present.

                If it was intended to re-compute the feature on the fly, re-run with `cache.use_cache_without_dataset=False`.

                Debug information:
                Scenario type: {scenario.scenario_type}. Scenario log name: {scenario.log_name}. Scenario token: {scenario.token}.
                """
                )
            )
        if isinstance(builder, AbstractFeatureBuilder):
            feature = builder.get_features_from_scenario(scenario)
        elif isinstance(builder, AbstractTargetBuilder):
            feature = builder.get_targets(scenario)
        else:
            raise ValueError(f"Unknown builder type: {type(builder)}")

        # If caching is enabled, store the feature
        if feature.is_valid and cache_path_available:
            logger.debug(f"Saving feature: {file_name} to a file...")
            file_name.parent.mkdir(parents=True, exist_ok=True)
            feature_stored_sucessfully = storing_mechanism.store_computed_feature_to_folder(file_name, feature)
    else:
        # In case the feature exists in the cache, load it
        logger.debug(f"Loading feature: {file_name} from a file...")
        
        feature = storing_mechanism.load_computed_feature_from_folder(file_name, builder.get_feature_type())
        assert feature.is_valid, 'Invalid feature loaded from cache!'

    return (
        feature,
        CacheMetadataEntry(file_name=file_name) if (need_to_compute_feature and feature_stored_sucessfully) else None,
    )

```

缓存有的话直接加载，否则用get_features_from_scenario或get_targets直接从场景中获得

>  真是一层套一层