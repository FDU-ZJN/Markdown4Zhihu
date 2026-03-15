---
title: Versatile Behavior Diffusion代码详解
date: 2025-11-29 15:25:24
categories: 计算机
tags:
  - 自动驾驶
  - python
cover: /img/cover_27.jpg
abbrlink: 6733346653
description: Versatile Behavior Diffusion数据代码阅读详解
---

## 数据提取

```python
MAX_NUM_OBJECTS = 64#车辆数目
MAX_POLYLINES = 256#多段线数目
MAX_TRAFFIC_LIGHTS = 16#交通灯数目
CURRENT_INDEX = 10
NUM_POINTS_POLYLINE = 30#线的点数目
```

```python
 tf_dataset = dataloader.tf_examples_dataset(
        path=data_dir,
        data_format=DataFormat.TFRECORD,
        preprocess_fn=tf_preprocess,
        repeat=1,
        # num_shards=16,
        deterministic=True,
    )
```

tf_preprocess用于 TensorFlow 数据集的预处理,tf_postprocess用于后处理，在data_utils.py定义

```python

def tf_preprocess(serialized: bytes) -> dict[str, tf.Tensor]:
    """
    Preprocesses the serialized data.

    Args:
        serialized (bytes): The serialized data.

    Returns:
        dict[str, tf.Tensor]: The preprocessed data.
    """
    womd_features = dataloader.womd_utils.get_features_description(
        include_sdc_paths=False,
        max_num_rg_points=30000,
        num_paths=None,
        num_points_per_path=None,
    )
    womd_features['scenario/id'] = tf.io.FixedLenFeature([1], tf.string)

    deserialized = tf.io.parse_example(serialized, womd_features)
    parsed_id = deserialized.pop('scenario/id')
    deserialized['scenario/id'] = tf.io.decode_raw(parsed_id, tf.uint8)
    return dataloader.preprocess_womd_example(
        deserialized,
        aggregate_timesteps=True,
        max_num_objects=None,
    )

```

将原始的序列化数据集样本转换为模型可用的格式化张量字典，为后续的轨迹预测或运动分析模型准备输入数据

```python
def tf_postprocess(example: dict[str, tf.Tensor]):
    """
    Postprocesses the example.

    Args:
        example (dict[str, tf.Tensor]): The example to be postprocessed.

    Returns:
        tuple: A tuple containing the scenario ID and the postprocessed scenario.
    """
    scenario = dataloader.simulator_state_from_womd_dict(example)
    scenario_id = example['scenario/id']
    return scenario_id, scenario

```

后处理分离出场景 ID 和 原始场景数据

```python
for example in tf_dataset_iter:
        
        scenario_id_binary, scenario = tf_postprocess(example)
        scenario_id = scenario_id_binary.tobytes().decode('utf-8')
        
        scenario_filename = os.path.join(save_dir, 'scenario_'+scenario_id+'.pkl')
        
        # check if file exists
        if os.path.exists(scenario_filename):
            continue
        
        if only_raw:
            data_dict = {'scenario_raw': scenario}
        else:
            data_dict = data_process_scenario(
                scenario,
                max_num_objects=MAX_NUM_OBJECTS,
                max_polylines=MAX_POLYLINES,
                current_index=CURRENT_INDEX,
                num_points_polyline=NUM_POINTS_POLYLINE,
            )
            if save_raw:
                data_dict['scenario_raw'] = scenario
            
        data_dict['scenario_id'] = scenario_id

        with open(scenario_filename, 'wb') as f:
            pickle.dump(data_dict, f)
```

### data_process_scenario——核心场景处理函数

#### 智能体

```c++
(agents_history, agents_future, agents_interested, agents_type, agents_id) = data_process_agent(
        scenario,
        max_num_objects = max_num_objects,
        current_index = current_index,
        use_log = use_log,
        selected_agents = selected_agents,
        remove_history=remove_history,
    )
```

```python
agents_history[i] = np.column_stack([
                log_trajectory.xy[a][:current_index+1, 0],
                log_trajectory.xy[a][:current_index+1, 1],
                log_trajectory.yaw[a][:current_index+1],
                log_trajectory.vel_x[a][:current_index+1],
                log_trajectory.vel_y[a][:current_index+1],
                log_trajectory.length[a][:current_index+1],
                log_trajectory.width[a][:current_index+1],
                log_trajectory.height[a][:current_index+1],
            ])
agents_history[i][~log_trajectory.valid[a, :current_index+1]] = 0
```

历史轨迹(max_objects, history_length, 8)的8个特征：x, y, yaw, vel_x, vel_y, length, width, height

```python
        agents_future[i] = np.column_stack([
                log_trajectory.xy[a][current_index:, 0],
                log_trajectory.xy[a][current_index:, 1],
                log_trajectory.yaw[a][current_index:],
                log_trajectory.vel_x[a][current_index:],
                log_trajectory.vel_y[a][current_index:]
            ])
```

**未来轨迹**(max_objects, future_length, 5)的5个特征x, y, yaw, vel_x, vel_y

-  `agents_interested`: 智能体关注度（模型化对象=10，其他=1，无效=0）
-  `agents_type`: 智能体类型（车辆、行人等）
-  `agent_ids`: 实际处理的智能体ID列表

-  **有效性掩码**: 使用`valid`标志过滤无效时间步的数据
-  **零填充**: 对无效位置用0填充
-  **历史清除**: `remove_history`参数可清除除当前时刻外的所有历史

最后返回

```python
return (agents_history, agents_future, agents_interested, agents_type, agent_ids)
```

```python
# 假设场景中有23个有效智能体，current_index=10，总时间步=91
agents_history.shape    # (64, 11, 8)   - 前23行有数据，后41行全0
agents_future.shape     # (64, 81, 5)   - 同上
agents_interested.shape # (64,)         - [10,1,1,10,0,0,...] 
agents_type.shape       # (64,)         - [1,1,2,1,0,0,...]
agent_ids              # [23, 45, 12, 67, ...] - 长度23的实际ID列表
```

如果智能体比较少，agents_history，agents_future会形成很大的稀疏矩阵

#### 交通灯

```c++
(traffic_light_points, traffic_lane_ids, traffic_light_states) = data_process_traffic_light(
        scenario,
        current_index = current_index,
    )
```

```python
def data_process_traffic_light(
    scenario,
    current_index = 10,
):
    """
    Process traffic light data from the given scenario.

    Args:
        scenario (datatypes.SimulatorState): The simulator state containing traffic light information.

    Returns:
        tuple: A tuple containing the processed traffic light points, lane IDs, and states.
    """
    traffic_lights = scenario.log_traffic_light
        
    ############# Get Traffic Lights #############
    traffic_lane_ids = np.asarray(traffic_lights.lane_ids)[:, current_index]
    traffic_light_states = np.asarray(traffic_lights.state)[:, current_index]
    traffic_stop_points = np.asarray(traffic_lights.xy)[:, current_index]
    traffic_light_valid = np.asarray(traffic_lights.valid)[:, current_index]
        
    traffic_light_points = np.concatenate([traffic_stop_points, traffic_light_states[:, None]], axis=1)    
    traffic_light_points = np.float32(traffic_light_points)
    traffic_light_points = np.where(
        traffic_light_valid[:, None],
        traffic_light_points,
        0.0
    )
        
    return traffic_light_points, traffic_lane_ids, traffic_light_states
```

输出x,y坐标，航道id，交通灯状态

#### 航点

```python
roadgraph_points = scenario.roadgraph_points
```

不作处理

#### 道路图

从完整的 Waymo 道路图中，只提取与当前场景中**活跃智能体相关**的局部地图。

```python
    for a in range(agents_history.shape[0]):
        if not current_valid[a]:
            continue
        
        agent_position = agents_history[a, -1, :2]
        nearby_roadgraph_points = filter_topk_roadgraph_points(roadgraph_points, agent_position, 3000)
        map_ids.append(nearby_roadgraph_points.ids.tolist())
```

只为有效的智能体筛选附近的路网点,找到**距离智能体最近的  <img src="https://www.zhihu.com/equation?tex=K" alt="K" class="ee_img tr_noresize" eeimg="1">  个道路图点**（这里  <img src="https://www.zhihu.com/equation?tex=K=3000" alt="K=3000" class="ee_img tr_noresize" eeimg="1"> ),收集所有这些点所属的**地图元素 ID**（即车道、人行横道等的 ID）

```python
    sorted_map_ids = []
    for i in range(nearby_roadgraph_points.shape[0]):
        for j in range(len(map_ids)):
            if map_ids[j][i] != -1 and map_ids[j][i] not in sorted_map_ids:
                sorted_map_ids.append(map_ids[j][i])
```

去重

```python
    for id in sorted_map_ids:
        # get polyline
        p_x = roadgraph_points_x[roadgraph_points.ids == id]
        p_y = roadgraph_points_y[roadgraph_points.ids == id]
        dir_x = roadgraph_points_dir_x[roadgraph_points.ids == id]
        dir_y = roadgraph_points_dir_y[roadgraph_points.ids == id]
        heading = np.arctan2(dir_y, dir_x)
        lane_type = roadgraph_points_types[roadgraph_points.ids == id]
        traffic_light_state = traffic_light_states[traffic_lane_ids == id] if id in traffic_lane_ids else 0
        traffic_light_state = np.repeat(traffic_light_state, len(p_x))
        polyline = np.stack([p_x, p_y, heading, traffic_light_state, lane_type], axis=1)
        
        # sample points and fill into fixed-size array
        polyline_len = polyline.shape[0]
        sampled_points = np.linspace(0, polyline_len-1, num_points_polyline, dtype=np.int32)
        cur_polyline = np.take(polyline, sampled_points, axis=0)
        polylines.append(cur_polyline)
```

每条多段线由 5 个特征组成：**(x, y) 坐标、航向角 (heading)、交通灯状态、车道类型**，由于地图元素的实际点数不固定，使用 `np.linspace` 和 `np.take` 对其进行均匀采样，以保证每条多段线最终包含固定的 `num_points_polyline`（例如 30）个点。

```python
    if len(polylines) > 0:
        polylines = np.stack(polylines, axis=0)
        polylines_valid = np.ones((polylines.shape[0],), dtype=np.int32)
    else:
        polylines = np.zeros((1, num_points_polyline, 5), dtype=np.float32)
        polylines_valid = np.zeros((1,), dtype=np.int32)
    
    if polylines.shape[0] >= max_polylines:
        polylines = polylines[:max_polylines]
        polylines_valid = polylines_valid[:max_polylines]
    else:
        polylines = np.pad(polylines, ((0, max_polylines-polylines.shape[0]), (0, 0), (0, 0)))
        polylines_valid = np.pad(polylines_valid, (0, max_polylines-polylines_valid.shape[0]))
```

截断和填充，将polylines固定在[max_polylines, num_points_polyline, 5]

#### 相对关系

```python
relations = calculate_relations(agents_history, polylines, traffic_light_points)
    relations = np.asarray(relations)
```


<img src="https://www.zhihu.com/equation?tex=N = n_{\text{agents}}(64) + n_{\text{polylines}}（256） + n_{\text{traffic_lights}}" alt="N = n_{\text{agents}}(64) + n_{\text{polylines}}（256） + n_{\text{traffic_lights}}" class="ee_img tr_noresize" eeimg="1">

**Agents:** 取最后一个时间步 `[:, -1, :3]`，  <img src="https://www.zhihu.com/equation?tex=(x, y, \text{yaw})" alt="(x, y, \text{yaw})" class="ee_img tr_noresize" eeimg="1"> 。

**Polylines:** 取路段的起始点 `[:, 0, :3]`。

**Traffic Lights:** 取位置  <img src="https://www.zhihu.com/equation?tex=(x, y)" alt="(x, y)" class="ee_img tr_noresize" eeimg="1"> ，并将角度  <img src="https://www.zhihu.com/equation?tex=\theta" alt="\theta" class="ee_img tr_noresize" eeimg="1">  强制设为 0

**几何变换**：计算**元素  <img src="https://www.zhihu.com/equation?tex=j" alt="j" class="ee_img tr_noresize" eeimg="1">  相对于元素  <img src="https://www.zhihu.com/equation?tex=i" alt="i" class="ee_img tr_noresize" eeimg="1">  的位置关系**，并将这个向量投影到元素  <img src="https://www.zhihu.com/equation?tex=i" alt="i" class="ee_img tr_noresize" eeimg="1">  的自身坐标系


<img src="https://www.zhihu.com/equation?tex=\begin{bmatrix} x_{ij}^{local} \\ y_{ij}^{local} \end{bmatrix} = \begin{bmatrix} \cos \theta_i & \sin \theta_i \\ -\sin \theta_i & \cos \theta_i \end{bmatrix} \begin{bmatrix} x_i - x_j \\ y_i - y_j \end{bmatrix}" alt="\begin{bmatrix} x_{ij}^{local} \\ y_{ij}^{local} \end{bmatrix} = \begin{bmatrix} \cos \theta_i & \sin \theta_i \\ -\sin \theta_i & \cos \theta_i \end{bmatrix} \begin{bmatrix} x_i - x_j \\ y_i - y_j \end{bmatrix}" class="ee_img tr_noresize" eeimg="1">

相对角度计算两者的朝向差，并规范化到  <img src="https://www.zhihu.com/equation?tex=(-\pi, \pi]" alt="(-\pi, \pi]" class="ee_img tr_noresize" eeimg="1">  区间。


<img src="https://www.zhihu.com/equation?tex=\text{if } i = j: \quad (x_{ij}^{local}, y_{ij}^{local}, \Delta \theta_{ij}) \leftarrow (\epsilon, \epsilon, \epsilon)" alt="\text{if } i = j: \quad (x_{ij}^{local}, y_{ij}^{local}, \Delta \theta_{ij}) \leftarrow (\epsilon, \epsilon, \epsilon)" class="ee_img tr_noresize" eeimg="1">

输出的  <img src="https://www.zhihu.com/equation?tex=[N, N, 3]" alt="[N, N, 3]" class="ee_img tr_noresize" eeimg="1">  关系特征数组，编码了节点  <img src="https://www.zhihu.com/equation?tex=j" alt="j" class="ee_img tr_noresize" eeimg="1">  相对于节点  <img src="https://www.zhihu.com/equation?tex=i" alt="i" class="ee_img tr_noresize" eeimg="1">  的**局部几何位置**：

1. **`local_pos_x` ( <img src="https://www.zhihu.com/equation?tex=\Delta x'" alt="\Delta x'" class="ee_img tr_noresize" eeimg="1"> ):** 元素  <img src="https://www.zhihu.com/equation?tex=j" alt="j" class="ee_img tr_noresize" eeimg="1">  在元素  <img src="https://www.zhihu.com/equation?tex=i" alt="i" class="ee_img tr_noresize" eeimg="1">  视野中的**前后距离**。
2. **`local_pos_y` ( <img src="https://www.zhihu.com/equation?tex=\Delta y'" alt="\Delta y'" class="ee_img tr_noresize" eeimg="1"> ):** 元素  <img src="https://www.zhihu.com/equation?tex=j" alt="j" class="ee_img tr_noresize" eeimg="1">  在元素  <img src="https://www.zhihu.com/equation?tex=i" alt="i" class="ee_img tr_noresize" eeimg="1">  视野中的**左右距离**。
3. **`theta_diff` ( <img src="https://www.zhihu.com/equation?tex=\Delta \theta" alt="\Delta \theta" class="ee_img tr_noresize" eeimg="1"> ):** 元素  <img src="https://www.zhihu.com/equation?tex=i" alt="i" class="ee_img tr_noresize" eeimg="1">  相对于元素  <img src="https://www.zhihu.com/equation?tex=j" alt="j" class="ee_img tr_noresize" eeimg="1">  的**相对航向角**。

>  感觉可以根据对称压缩一半，还有智能体只与附近的地图元素有关，这会是个比较大的稀疏矩阵吧

最终输出的数据结构

```python
data_dict = {
    'agents_history':        (64, 11, 8)     # 智能体历史轨迹
    'agents_interested':     (64,)           # 智能体关注度
    'agents_type':           (64,)           # 智能体类型
    'agents_future':         (64, 81, 5)     # 智能体未来轨迹（标签）
    'traffic_light_points':  (n_traffic_lights, 3)          # 交通灯信息
    'polylines':             (256, 30, 5)    # 道路折线
    'polylines_valid':       (256,)          # 折线有效性掩码
    'relations':             (N,N,3)            # 空间关系
    'agents_id':             (64,)           # 智能体原始ID
}
```

>  感觉压缩空间还是蛮大的

```python
            data_dict = data_process_scenario(
                scenario,
                max_num_objects=MAX_NUM_OBJECTS,
                max_polylines=MAX_POLYLINES,
                current_index=CURRENT_INDEX,
                num_points_polyline=NUM_POINTS_POLYLINE,
            )
            if save_raw:
                data_dict['scenario_raw'] = scenario
            
        data_dict['scenario_id'] = scenario_id

        with open(scenario_filename, 'wb') as f:
            pickle.dump(data_dict, f)
```

最后加上id，存入pkl文件

## 模型--顶层VBD

```python
        self.encoder = Encoder(self._encoder_layers,version=self._encoder_version)     	   self.denoiser = Denoiser(
            future_len=self._future_len,
            action_len=self._action_len,
            agents_len=self._agents_len,
            steps=self._diffusion_steps,
            input_dim = self._embeding_dim,
        )
        if self._with_predictor:
            self.predictor = GoalPredictor(
                future_len=self._future_len,
                agents_len=self._agents_len,
                action_len=self._action_len,
            )
        else:
            self.predictor = None
            self._train_predictor = False

        self.noise_scheduler = DDPM_Sampler(
            steps=self._diffusion_steps,
            schedule=self._schedule_type,
            s = cfg.get('schedule_s', 0.0),
            e = cfg.get('schedule_e', 1.0),
            tau = cfg.get('schedule_tau', 1.0),
            scale = cfg.get('schedule_scale', 1.0),
        )
```

编码器，去噪器，目标预测器，噪声调度器实例化

`configure_optimizers`定义模型训练时的优化器和学习率调度器的配置函数

`forward`调用去噪器和预测器forward，再通过output_dict.update()合并返回。

### forward_denoiser

先将输入的规范化加噪动作转换回原始数值范围，再使用去噪器进行预测

```python
denoised_actions_normalized = self.noise_scheduler.q_x0(
            denoiser_output, 
            diffusion_step, 
            noised_actions_normalized,
            prediction_type=self._prediction_type
        )
```

使用Noise Scheduler反推干净动作序列

q_x0在utils.py定义

```python
    def q_x0(
        self,
        model_output: torch.FloatTensor,
        timesteps: Union[int, torch.IntTensor],
        sample: torch.FloatTensor,
        prediction_type: str = "sample",
    ):
        """
        Predict the denoised x0 from the previous timestep by reversing the SDE. This function propagates the diffusion
        process from the learned model outputs (most often the predicted noise).

        Args:
            model_output (`torch.FloatTensor`):
                The direct output from learned diffusion model.
            timestep (`float`):
                The current discrete timestep in the diffusion chain.
            sample (`torch.FloatTensor`):
                A current instance of a sample created by the diffusion process.
        """
        

        # 2. Compute predicted original sample from predicted noise also called "predicted x_0"
        if prediction_type == "sample" or prediction_type == "mean":
            pred_original_sample = model_output
        elif prediction_type == "error":
            alpha_prod_t = self.alphas_cumprod[timesteps]
            for _ in range(len(sample.shape)-len(alpha_prod_t.shape)):
                alpha_prod_t = alpha_prod_t[..., None]
            beta_prod_t = 1 - alpha_prod_t
            
            pred_original_sample = (sample - beta_prod_t ** (0.5) * model_output) / alpha_prod_t ** (0.5)
        # elif prediction_type == "v":
        #     pred_original_sample = (alpha_prod_t**0.5) * sample - (beta_prod_t**0.5) * model_output
        else:
            raise NotImplementedError

        return pred_original_sample
```

使用去噪器的输出

前向加噪： <img src="https://www.zhihu.com/equation?tex=x_t = \sqrt{\bar{\alpha}_t} x_0 + \sqrt{1 - \bar{\alpha}_t} \epsilon" alt="x_t = \sqrt{\bar{\alpha}_t} x_0 + \sqrt{1 - \bar{\alpha}_t} \epsilon" class="ee_img tr_noresize" eeimg="1"> 

那么反向执行是 <img src="https://www.zhihu.com/equation?tex=\hat{x}_0 = \frac{1}{\sqrt{\bar{\alpha}_t}} \left( x_t - \sqrt{1 - \bar{\alpha}_t} \cdot \epsilon_\theta(x_t, t) \right)" alt="\hat{x}_0 = \frac{1}{\sqrt{\bar{\alpha}_t}} \left( x_t - \sqrt{1 - \bar{\alpha}_t} \cdot \epsilon_\theta(x_t, t) \right)" class="ee_img tr_noresize" eeimg="1"> ，得到最终的干净动作序列

>  "error"时去噪器输出的是预测噪声，以前我一直以为是干净序列呢，所以不知道为什么加q_x0，看了看q_x0明白了

```python
        current_states = encoder_outputs['agents'][:, :self._agents_len, -1]
        assert encoder_outputs['agents'].shape[1] >= self._agents_len, 'Too many agents to consider'
        # Roll out
        denoised_actions = self.unnormalize_actions(denoised_actions_normalized) 
        denoised_trajs = roll_out(current_states, denoised_actions,
                    action_len=self.denoiser._action_len, global_frame=True)
```

获取初始状态，再将干净动作反归一化，再根据这两个生成完整的轨迹

```python
        return {
            'denoiser_output': denoiser_output,
            'denoised_actions_normalized': denoised_actions_normalized,
            'denoised_actions': denoised_actions,
            'denoised_trajs': denoised_trajs,
        }
```



### forward_predictor

与forward_denoiser差不多，预测器预测动作（归一化）后，获取初始状态，再将干净动作反归一化，再根据这两个生成完整的轨迹。

```python
return {
            'goal_actions_normalized': goal_actions_normalized,
            'goal_actions': goal_actions,
            'goal_scores': goal_scores,
            'goal_trajs': goal_trajs,
        }
```

最后输出概率，轨迹，动作。

### forward_and_get_loss

完整的前向传播和损失计算过程。

```python
gt_actions, gt_actions_valid = inverse_kinematics(
            agents_future,
            agents_future_valid,
            dt=0.1,
            action_len=self._action_len,
        )
gt_actions_normalized = self.normalize_actions(gt_actions)
```

地面轨迹转化为动作后归一化

```python
noise = torch.randn(B, A, T, D).type_as(agents_future)
            
            # noise the input
            noised_action_normalized = self.noise_scheduler.add_noise(
                gt_actions_normalized, #.reshape(B*A, T, D),
                noise,
                diffusion_steps#, .reshape(B*A),
            )
```

获得加入噪声的动作

```python
if self._replay_buffer:
                with torch.no_grad():
                    # Forward for one step
                    denoise_outputs = self.forward_denoiser(encoder_outputs, gt_actions_normalized, diffusion_steps.view(B,A))
                    x_0 = denoise_outputs['denoised_actions_normalized']
                    # Step to sample from P(x_t-1 | x_t, x_0)
                    x_t_prev = self.noise_scheduler.step(
                        model_output = x_0,
                        timesteps = diffusion_steps,
                        sample = noised_action_normalized,
                        prediction_type=self._prediction_type if hasattr(self, '_prediction_type') else 'sample',
                    )
                    noised_action_normalized = x_t_prev.detach()
```

（可选）

模型先预测一次  <img src="https://www.zhihu.com/equation?tex=x_0" alt="x_0" class="ee_img tr_noresize" eeimg="1">  (`denoise_outputs`)。

利用预测的  <img src="https://www.zhihu.com/equation?tex=\hat{x}_0" alt="\hat{x}_0" class="ee_img tr_noresize" eeimg="1">  和当前的加噪样本  <img src="https://www.zhihu.com/equation?tex=x_t" alt="x_t" class="ee_img tr_noresize" eeimg="1"> ，通过 **逆向过程**（`self.noise_scheduler.step`）计算出**前一个时间步的样本  <img src="https://www.zhihu.com/equation?tex=x_{t-1}" alt="x_{t-1}" class="ee_img tr_noresize" eeimg="1"> ** (`x_t_prev`)。

用  <img src="https://www.zhihu.com/equation?tex=x_{t-1}" alt="x_{t-1}" class="ee_img tr_noresize" eeimg="1">  替换  <img src="https://www.zhihu.com/equation?tex=x_t" alt="x_t" class="ee_img tr_noresize" eeimg="1">  作为加噪输入数据。


<img src="https://www.zhihu.com/equation?tex=x_{t-1} = \underbrace{\sqrt{\bar{\alpha}_{t-1}} \cdot \hat{x}_0}_{\text{1. 对 }\hat{x}_0\text{ 的缩放}} + \underbrace{\sqrt{1 - \bar{\alpha}_{t-1} - \sigma_t^2} \cdot \epsilon_\theta(x_t, t)}_{\text{2. 指向 }x_t\text{ 的方向}} + \underbrace{\sigma_t \cdot \epsilon}_{\text{3. 随机噪声项}}" alt="x_{t-1} = \underbrace{\sqrt{\bar{\alpha}_{t-1}} \cdot \hat{x}_0}_{\text{1. 对 }\hat{x}_0\text{ 的缩放}} + \underbrace{\sqrt{1 - \bar{\alpha}_{t-1} - \sigma_t^2} \cdot \epsilon_\theta(x_t, t)}_{\text{2. 指向 }x_t\text{ 的方向}} + \underbrace{\sigma_t \cdot \epsilon}_{\text{3. 随机噪声项}}" class="ee_img tr_noresize" eeimg="1">

**去噪器损失计算**

sample

```python
state_loss_mean, yaw_loss_mean = self.denoise_loss(denoised_trajs, agents_future, ...)
denoise_loss = state_loss_mean + yaw_loss_mean 
total_loss += denoise_loss
```

比较模型展开的轨迹 (`denoised_trajs`) 与真实轨迹 (`agents_future`) 的状态（位置/速度和偏航角（Yaw）误差。

error

```python
denoise_loss = torch.nn.functional.mse_loss(
                    denoiser_output, noise, reduction='mean'
                )
                total_loss += denoise_loss
                log_dict.update({
                    prefix+'diffusion_loss': denoise_loss.item(),
                })
```

计算**模型预测的噪声**（ <img src="https://www.zhihu.com/equation?tex=\epsilon_\theta" alt="\epsilon_\theta" class="ee_img tr_noresize" eeimg="1"> ）与**采样的真实噪声**（ <img src="https://www.zhihu.com/equation?tex=\epsilon" alt="\epsilon" class="ee_img tr_noresize" eeimg="1"> ）之间的 **均方误差（MSE Loss）**

mean

计算模型预测的  <img src="https://www.zhihu.com/equation?tex=\hat{x}_0" alt="\hat{x}_0" class="ee_img tr_noresize" eeimg="1"> 与真实  <img src="https://www.zhihu.com/equation?tex=x_0" alt="x_0" class="ee_img tr_noresize" eeimg="1"> 之间的动作损失 (`self.action_loss`)。

```python
denoise_ade, denoise_fde = self.calculate_metrics_denoise(
                denoised_trajs, agents_future, agents_future_valid, agents_interested, 8
            )
            
            log_dict.update({
                prefix+'denoise_ADE': denoise_ade,
                prefix+'denoise_FDE': denoise_fde,
            })
```

**行为预测器损失**

```python
goal_loss_mean, score_loss_mean = self.goal_loss(
                goal_trajs, goal_scores, agents_future,
                agents_future_valid, anchors,
                agents_interested,
            )

            pred_loss = goal_loss_mean + 0.05 * score_loss_mean
```

包括轨迹损失和概率损失

```python
    def training_step(self, batch, batch_idx):
        """
        Training step of the model.

        Args:
            batch: Input batch.
            batch_idx: Batch index.

        Returns:
            loss: Loss value.
        """        
        loss, log_dict = self.forward_and_get_loss(batch, prefix='train/')
        self.log_dict(
            log_dict, 
            on_step=True, on_epoch=False, sync_dist=True,
            prog_bar=True
        )
        
        return loss
    
```

交给训练的显示签名

>  把数据提取和VBD模型的顶层看完了，但只看到前向推理获得损失的函数，找不到更新模型的函数，训练的python文件也只能看到模型绑定到了lightning.pytorch没有看到他显式地更新，是这个lightning.pytorch会自动处理反向传播的过程吗，也就是我只要算出前向损失就能无脑扔给他了是吗，真神奇

## 内部模块

### Encoder

```python
    def __init__(self, layers=6, version='v1'):
        super().__init__()
        self._version = version
        if self._version == 'v1':
            self.agent_encoder = AgentEncoder()
        else:
            self.agent_encoder = AgentEncoderV2()
        self.map_encoder = MapEncoder()
        self.traffic_light_encoder = TrafficLightEncoder()
        self.relation_encoder = FourierEmbedding(input_dim=3)
        self.transformer_encoder = TransformerEncoder(layers=layers)
```

智能体编码器，地图编码器，交通信号灯编码器，关系编码器，Transformer 编码器

```python
        agents = inputs['agents_history']
        agents_type = inputs['agents_type']
        agents_interested = inputs['agents_interested']
        agents_local = batch_transform_trajs_to_local_frame(agents)

        B, A, T, D = agents_local.shape
        agents_local = agents_local.reshape(B*A, T, D)
        agents_type = agents_type.reshape(B*A)
        encoded_agents = self.agent_encoder(agents_local, agents_type)
        encoded_agents = encoded_agents.reshape(B, A, -1)
        agents_mask = torch.eq(agents_interested, 0)

        # map and traffic light encoding
        map_polylines = inputs['polylines']
        map_polylines_local = batch_transform_polylines_to_local_frame(map_polylines)
        encoded_map_lanes = self.map_encoder(map_polylines_local)
        maps_mask = inputs['polylines_valid'].logical_not()

        traffic_lights = inputs['traffic_light_points']
        encoded_traffic_lights = self.traffic_light_encoder(traffic_lights)
        traffic_lights_mask = torch.eq(traffic_lights.sum(-1), 0)

        # relation encoding
        relations = inputs['relations']
        relations = self.relation_encoder(relations)
                encodings = self.transformer_encoder(relations, encoded_agents, encoded_map_lanes, encoded_traffic_lights,
                                             agents_mask, maps_mask, traffic_lights_mask)
```

智能体和地图都要转化为局部坐标系，最后一起扔给transformer_encoder

**智能体局部坐标系**

```python
def batch_transform_trajs_to_local_frame(trajs, ref_idx=-1):
    """
    Batch transform trajectories to the local frame of reference.

    Args:
        trajs (torch.Tensor): Trajectories tensor of shape [B, N, T, x].
        ref_idx (int): Reference index for the local frame. Default is -1.

    Returns:
        torch.Tensor: Transformed trajectories in the local frame.

    """
    x = trajs[..., 0]
    y = trajs[..., 1]
    theta = trajs[..., 2]
    v_x = trajs[..., 3]
    v_y = trajs[..., 4]
    
    local_x = (x - x[:, :, ref_idx, None]) * torch.cos(theta[:, :, ref_idx, None]) + \
        (y - y[:, :, ref_idx, None]) * torch.sin(theta[:, :, ref_idx, None])
    local_y = -(x - x[:, :, ref_idx, None]) * torch.sin(theta[:, :, ref_idx, None]) + \
        (y - y[:, :, ref_idx, None]) * torch.cos(theta[:, :, ref_idx, None])
    
    local_theta = theta - theta[:, :, ref_idx, None]
    local_theta = wrap_angle(local_theta)

    local_v_x = v_x * torch.cos(theta[:, :, ref_idx, None]) + v_y * torch.sin(theta[:, :, ref_idx, None])
    local_v_y = -v_x * torch.sin(theta[:, :, ref_idx, None]) + v_y * torch.cos(theta[:, :, ref_idx, None])

    local_trajs = torch.stack([local_x, local_y, local_theta, local_v_x, local_v_y], dim=-1)
    local_trajs[trajs[..., :5] == 0] = 0

    if trajs.shape[-1] > 5:
        trajs = torch.cat([local_trajs, trajs[..., 5:]], dim=-1)
    else:
        trajs = local_trajs

    return trajs
```

以第一个点的坐标朝向为参考点，还是前面那个旋转矩阵。

**地图局部坐标系**

```python
def batch_transform_polylines_to_local_frame(polylines):
    """
    Batch transform polylines to the local frame of reference.
    Args:
        polylines (torch.Tensor): Polylines tensor of shape [B, M, W, 5].
    Returns:
        torch.Tensor: Transformed polylines in the local frame.
    """
    x = polylines[..., 0]
    y = polylines[..., 1]
    theta = polylines[..., 2]
    local_x = (x - x[:, :, 0, None]) * torch.cos(theta[:, :, 0, None]) + \
        (y - y[:, :, 0, None]) * torch.sin(theta[:, :, 0, None])
    local_y = -(x - x[:, :, 0, None]) * torch.sin(theta[:, :, 0, None]) + \
        (y - y[:, :, 0, None]) * torch.cos(theta[:, :, 0, None])
    local_theta = theta - theta[:, :, 0, None]
    local_theta = wrap_angle(local_theta)
    local_polylines = torch.stack([local_x, local_y, local_theta], dim=-1)
    local_polylines[polylines[..., :3] == 0] = 0
    polylines = torch.cat([local_polylines, polylines[..., 3:]], dim=-1)
    return polylines
```

变换逻辑相同

```python
def batch_transform_trajs_to_global_frame(trajs, current_states):
    """
    Batch transform trajectories to the global frame of reference.

    Args:
        trajs (torch.Tensor): Trajectories tensor of shape [B, N, x, 2 or 3].
        current_states (torch.Tensor): Current states tensor of shape [B, N, 5].

    Returns:
        torch.Tensor: Transformed trajectories in the global frame. [B, N, x, 3]

    """
    x, y, theta = current_states[:, :, 0], current_states[:, :, 1], current_states[:, :, 2]
    g_x = trajs[..., 0] * torch.cos(theta[:, :, None]) - trajs[..., 1] * torch.sin(theta[:, :,  None])
    g_y = trajs[..., 0] * torch.sin(theta[:, :, None]) + trajs[..., 1] * torch.cos(theta[:, :,  None])
    x = g_x + x[:, :, None]
    y = g_y + y[:, :, None]
        
    if trajs.shape[-1] == 2:
        trajs = torch.stack([x, y], dim=-1)
    else:
        theta = trajs[..., 2] + theta[:, :, None]
        theta = wrap_angle(theta)
        trajs = torch.stack([x, y, theta], dim=-1)

    return trajs
```

局部到全局，取旋转矩阵M( <img src="https://www.zhihu.com/equation?tex=θ" alt="θ" class="ee_img tr_noresize" eeimg="1"> )变为其逆矩阵M( <img src="https://www.zhihu.com/equation?tex=-θ" alt="-θ" class="ee_img tr_noresize" eeimg="1"> )，在加上当前x坐标就变换过去了

交通灯使用全局坐标系

```python
class SelfTransformer(nn.Module):
    def __init__(self):
        super().__init__()
        heads, dim, dropout = 8, 256, 0.1
        self.qc_attention = QCMHA(dim, heads, dropout)
        self.norm_1 = nn.LayerNorm(dim)
        self.norm_2 = nn.LayerNorm(dim)
        self.ffn = nn.Sequential(nn.Linear(dim, dim*4), nn.GELU(), nn.Dropout(dropout), 
                                 nn.Linear(dim*4, dim), nn.Dropout(dropout))

    def forward(self, inputs, relations, mask=None):
        attention_output = self.qc_attention(inputs, relations, mask)
        attention_output = self.norm_1(attention_output + inputs)
        output = self.norm_2(self.ffn(attention_output) + attention_output)

        return output
```

多头自注意力，relations是边属性，与论文一致

### 行为预测器

```python
class GoalPredictor(nn.Module):
    def __init__(self, future_len=80, action_len=5, agents_len=32):
        super().__init__()
        self._agents_len = agents_len
        self._future_len = future_len
        self._action_len = action_len
        
        self.attention_layers = nn.ModuleList([CrossTransformer() for _ in range(4)])
        self.anchor_encoder = nn.Sequential(nn.Linear(2, 128), nn.ReLU(), nn.Linear(128, 256))
        self.act_decoder = nn.Sequential(nn.Linear(256, 256), nn.ELU(), nn.Dropout(0.1),
                                         nn.Linear(256, (self._future_len//self._action_len)*2))
        self.score_decoder = nn.Sequential(nn.Linear(256, 128), nn.ELU(), nn.Dropout(0.1),
                                           nn.Linear(128, 1))
        
    def forward(self, inputs):
        anchors_points = inputs['anchors'][:, :self._agents_len]
        anchors = self.anchor_encoder(anchors_points) 
        encodings = inputs['encodings']
        query = encodings[:, :self._agents_len, None] + anchors

        num_batch, num_agents, num_queries, _ = query.shape
        
        mask = torch.cat([inputs['agents_mask'], inputs['maps_mask'], 
                          inputs['traffic_lights_mask']], dim=-1)
        relations = inputs['relation_encodings']
                
        actions = []
        scores = []
        for i in range(self._agents_len):
            query_content = self.attention_layers[0](query[:, i], encodings, relations[:, i], key_mask=mask)
            query_content = self.attention_layers[1](query_content, encodings, relations[:, i], key_mask=mask)
            query_content = query_content + query[:, i]
            query_content = self.attention_layers[2](query_content, encodings, relations[:, i], key_mask=mask)
            query_content = self.attention_layers[3](query_content, encodings, relations[:, i], key_mask=mask)
            actions.append(self.act_decoder(query_content).reshape(
                num_batch, num_queries, self._future_len//self._action_len, 2
            ))
            scores.append(self.score_decoder(query_content).squeeze(-1))

        actions = torch.stack(actions, dim=1)
        scores = torch.stack(scores, dim=1)

        return actions, scores
    
    def reset_agent_length(self, agents_len):
        self._agents_len = agents_len
```

交叉注意力，查询由**智能体的场景编码** 和**锚点编码**相加

**anchors**在datasets.py直接从`./vbd/data/cluster_64_center_dict.pkl`获取

```python
class CrossTransformer(nn.Module):
    def __init__(self):
        super().__init__()
        heads, dim, dropout = 8, 256, 0.1
        self.cross_attention = nn.MultiheadAttention(dim, heads, dropout, batch_first=True)
        self.norm_1 = nn.LayerNorm(dim)
        self.norm_2 = nn.LayerNorm(dim)
        self.ffn = nn.Sequential(nn.Linear(dim, dim*4), nn.GELU(), nn.Dropout(dropout), 
                                 nn.Linear(dim*4, dim), nn.Dropout(dropout))

    def forward(self, query, key, relations, attn_mask=None, key_mask=None):
        # add relations to key and value
        key = key + relations
        value = key

        if key_mask is not None:
            attention_output, _ = self.cross_attention(query, key, value, key_padding_mask=key_mask)
        elif attn_mask is not None:
            attention_output, _ = self.cross_attention(query, key, value, attn_mask=attn_mask)
        else:
            attention_output, _ = self.cross_attention(query, key, value)

        attention_output = self.norm_1(attention_output)
        output = self.norm_2(self.ffn(attention_output) + attention_output)

        return output
```

交叉注意力，K,V是场景输入+相对关系

### 去噪器

```python
class Denoiser(nn.Module):
    def __init__(self, future_len=80, action_len=5, agents_len=32, steps=100, input_dim=5):
        super().__init__()
        self._agents_len = agents_len
        self._action_len = action_len
        self._input_dim = input_dim
        self.noise_level_embedding = nn.Embedding(steps, 256)
        self.decoder = TransformerDecoder(future_len, agents_len, self._action_len, input_dim=self._input_dim)

    def forward(self, encoder_inputs, noisy_actions, diffusion_step, rollout = True):
        '''
        Args:
            noisy_actions: [B, A, T_r, 2], [acc, yaw_rate] Unnormalized actions
            diffusion_step: [B, A]
        Output:
            denoised_states: [B, A, T, 3], [x, y, theta]
        '''
        noisy_actions = noisy_actions[:, :self._agents_len]
        
        if type(diffusion_step) == int:
            diffusion_step = torch.full(
                noisy_actions.shape[:-2], diffusion_step, 
                dtype=torch.long, device=noisy_actions.device
            )
        else:
            diffusion_step = diffusion_step[:, :self._agents_len]
        current_states = encoder_inputs['agents'][:, :self._agents_len, -1]
        encodings = encoder_inputs['encodings']
        relations = encoder_inputs['relation_encodings']
        agents_mask = encoder_inputs['agents_mask']
        maps_mask = encoder_inputs['maps_mask']
        traffic_lights_mask = encoder_inputs['traffic_lights_mask']
        mask = torch.cat([agents_mask, maps_mask, traffic_lights_mask], dim=-1)
        # denoise step
        noise_level = self.noise_level_embedding(diffusion_step)
        if rollout:
            embedding = roll_out(current_states, noisy_actions,
                                    action_len=self._action_len, global_frame=False)   
        else:
            embedding = noisy_actions
        decoder_output = self.decoder(
            embedding, noise_level, 
            encodings, relations, mask
        )       
        return decoder_output
    def reset_agent_length(self, agents_len):
        self._agents_len = agents_len
        self.decoder.reset_agent_length(agents_len)
```

`noise_level_embedding`离散整数转化为张量

```python
class TransformerDecoder(nn.Module):
    def __init__(self, future_len, agents_len, action_len, input_dim=5, ouptut_dim = 2,  causal = True):
        super().__init__()
        self._future_len = future_len
        self._action_len = action_len
        self._agents_len = agents_len
        self._future_len = future_len // action_len
        self._input_dim = input_dim
        self._output_dim = ouptut_dim

        self.time_embedding = nn.Embedding(self._future_len, 256)
        self.attention_layers = nn.ModuleList([CrossTransformer() for _ in range(4)])
        self.encoder = nn.Sequential(nn.Linear(self._input_dim, 128), nn.ReLU(), nn.Linear(128, 256))
        self.decoder = nn.Sequential(nn.Linear(256, 128), nn.ELU(), nn.Dropout(0.1), nn.Linear(128, self._output_dim))
        
        self.register_buffer('casual_mask', self.generate_casual_mask(causal))
        self.register_buffer('time', torch.arange(self._future_len).unsqueeze(0))

    def generate_casual_mask(self, causal=True):
        if not causal:
            return torch.zeros(self._agents_len, self._future_len, self._agents_len * self._future_len, dtype=bool)
        
        # Initialize a zero mask
        mask = torch.zeros(self._agents_len, self._future_len, self._agents_len * self._future_len)

        # An agent can attend to all of its own actions
        for i in range(self._agents_len):
            mask[i, :, i*self._future_len:(i+1)*self._future_len] = 1.0

        # An agent can attend to other agents from all previous timesteps but not future timesteps
        for i in range(self._agents_len):
            for j in range(self._agents_len):
                if i != j:
                    for t in range(self._future_len):
                        mask[i, t, j*self._future_len:j*self._future_len+t+1] = 1.0
        
        # Convert to boolean mask
        mask = mask.bool().logical_not()

        return mask

    def forward(self, noisy_trajectories, noise_level, encodings, relations, mask):
        '''
        noisy_trajectories: [B, Na, T_f, 5]
        '''
        # get query
        noisy_trajectories = torch.reshape(noisy_trajectories, (-1, self._agents_len, 
                                                                self._future_len, self._action_len, self._input_dim)) 
        future_states = self.encoder(noisy_trajectories)
        future_states = future_states.max(dim=3).values # [B, Na, T, 256]
        time_embedding = self.time_embedding(self.time) # [1, T, 256]
        query = future_states + time_embedding[:, None] # [B, Na, T, 256]
        query = query + noise_level[:, :, None, :] 

        # decode denoised actions
        query_content_list = []
        for i in range(self._agents_len):
            query_content = self.attention_layers[0](
                query[:, i], 
                query.reshape(-1, self._agents_len*self._future_len, 256), 
                relations[:, i, :self._agents_len].repeat_interleave(self._future_len, dim=1),
                attn_mask=self.casual_mask[i]) # [B, T, 256]
            query_content = self.attention_layers[1](query_content, encodings, relations[:, i], key_mask=mask) # [B, T, 256]
            query_content_list.append(query_content)

        query_content_stack = torch.stack(query_content_list, dim=1) # [B, Na, T, 256] 
        query_content_stack = query_content_stack + query
    
        query_content_list = []
        for i in range(self._agents_len):
            query_content = self.attention_layers[2](
                query_content_stack[:, i],
                query_content_stack.reshape(-1, self._agents_len*self._future_len, 256),
                relations[:, i, :self._agents_len].repeat_interleave(self._future_len, dim=1),
                attn_mask=self.casual_mask[i]) # [B, T, 256]
            query_content = self.attention_layers[3](query_content, encodings, relations[:, i], key_mask=mask) # [B, T, 256]
            query_content_list.append(query_content)
        
        query_content_stack = torch.stack(query_content_list, dim=1) # [B, Na, T, 256] 
        actions = self.decoder(query_content_stack) 

        return actions

    def reset_agent_length(self, agents_len):
        self._agents_len = agents_len
        new_mask = self.generate_casual_mask().type_as(self.casual_mask)
        self.casual_mask = new_mask
```

query包含**带噪的序列特征**、**时间/位置信息**和**噪声级别**

两个块，均是第一层为自注意力，第二层为场景交叉注意力

块一和块二残差连接`query_content_stack = query_content_stack + query`