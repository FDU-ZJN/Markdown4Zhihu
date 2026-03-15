---
title: Neural_MP论文阅读
date: 2025-10-20 08:35:17
categories: 具身智能
tags:
  - 运动规划
  - IROS
  - 论文
cover: /img/cover_12.jpg
highlight_shrink: true
abbrlink: 3740239699
description: Neural_MP通过大规模数据驱动的学习，构建一个通用、快速运动规划器，能泛化到未见过的真实世界场景。
---

![image-20251020091859752](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Neural_MP论文阅读/image-20251020091859752_1.png)

## 论文概述

通过大规模数据驱动的学习，构建一个**通用、快速运动规划器**，能泛化到**未见过的真实世界场景**。

## 成果

提出了一种简单、可扩展的方法来训练和部署快速、通用的神经运动规划器：1) 在逼真的配置中生成具有多样化环境的大规模程序化场景，2) 用于拟合基于采样的运动规划数据的多模态序列建模，以及 3) 轻量级的测试时优化，以确保在现实世界中快速、安全和可靠的部署。

在四个不同的环境中评估了我们的方法在 64 个现实世界运动规划任务中的表现，结果表明，与基于采样的方法相比，运动规划成功率提高了 23%，与基于优化的方法相比提高了 17%，与神经运动规划方法相比提高了 79%。

<div style="position:relative; padding-bottom:75%; width:100%; height:0">
    <iframe src="//player.bilibili.com/player.html?bvid=BV1Cam8YJEog&page=1" scrolling="no" border="0" frameborder="no" framespacing="0" allowfullscreen="true" style="position:absolute; height: 100%; width: 100%;"></iframe>
</div>
## 生成大规模训练数据

### 生成大量复杂场景

-  **程序生成物体**：使用一组六个参数可变的类别——架子、小隔间、微波炉、洗碗机、开放式盒子和橱柜。这些类别代表了日常场景中机器人遇到并必须避免碰撞的大量物体。每个类别实例都是使用原始长方体对象的组合构建的，并通过定义资产的类别特定参数进行参数化。

-  **Objaverse日常物品资产**：程序化生成可以使用定义的类别创建大量场景，但机器人可能遇到的大量日常物品并不在此分布范围内，从最近提出的大规模3D对象数据集Objaverse [37]中采样的对象来扩充我们的数据集。

-  使用从场景中现有资产计算出的有效碰撞法向量来调整其位置，从而迭代地将资产添加到场景中

![image-20251020093435752](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Neural_MP论文阅读/image-20251020093435752_1.png)

### 运动规划专家提供运动数据

为了确保规划器需要避开障碍物，会从**特定位置**（例如，柜子或微波炉内部）采样末端执行器姿态。然后，通过逆运动学来推导出相应的关节姿态，作为机器人的起始或目标配置。

使用自适应信息树[10] (AIT*)，通过自适应启发式算法实现快速逼近最优路径规划。（BB:查了下自适应启发式算法感觉有点像遗传算法,不怼，就是属于他们的，还有蚁群算法）

单纯地模仿规划器的输出效果不佳，AIT* 生成的规划通常会导致航路点相距甚远，从而产生较大的动作跳跃和稀疏数据覆盖，使得网络难以拟合数据（平滑对于学习性能至关重要)。为了解决这个问题，使用三次样条插值执行平滑处理，同时强制执行速度和加速度限制。

## 泛化神经网络策略

### 适用于sim2real迁移的观测空间

在观测中包含本体感受和目标信息，包括当前的关节角度qt，目标关节角度g，以及点云PCD。

**点云** 作为场景表示的自然选择。点云是是基于机器人基坐标系的3D点，因此与视角无关，并且在模拟和真实之间基本一致。，这对于Sim2Real迁移至关重要。

### 网络架构

1. **选择LSTM而非Transformer**：
   -  使用LSTM序列模型是因为它在保持与Transformer相当性能的同时，推理速度更快
   
   -  LSTM能处理历史信息，这对学习专家行为很有帮助
   
   -  ![image-20251020182036557](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Neural_MP论文阅读/image-20251020182036557_1.png)
   
      消融实验结果
2. **输入处理**：
   
   -  **点云数据(PCDt)**：先把点云分割成机器人、障碍物、目标机器人三部分，再交给PointNet++处理，输出 1024 维的向量——原始点云经过多层抽象和信息聚合后的紧凑表示。它包含了场景中物体（机器人、障碍物、目标）的形状、相对位置以及其他几何和语义特征（沿用MπNets）
   -  **关节状态(qt)和目标(g/gt)**：用简单的MLP网络处理
   -  把所有处理后的信息拼接成一个向量，输入给LSTM
3. **输出设计**：
   
   -  因为基于采样的运动规划器（如AIT*）具有多模态特性——同一场景可能产生完全不同的规划路径，所以使用**高斯混合模型(GMM)**来输出一个多模态的概率分布
   -  网络预测的是关节角度的变化量(Δqt+1)，实际执行时用 qt+1 = qt + Δqt+1 计算下一个目标位置

| **组件**             | **参数规模** | **输入维度**                         | **输出维度**                   | **功能描述**                            |

| :------------------- | :----------- | :----------------------------------- | :----------------------------- | :-------------------------------------- |

| **整体神经网络**     | 20M参数      | -                                    | -                              | 在100万条轨迹数据集上训练               |

| **PointNet++编码器** | 4M参数       | -                                    | 1024                           | 输出1024维嵌入向量                      |

| **LSTM解码器**       | 16M参数      | PointNet++嵌入 +  <img src="https://www.zhihu.com/equation?tex=q_t" alt="q_t" class="ee_img tr_noresize" eeimg="1"> 编码 +  <img src="https://www.zhihu.com/equation?tex=g" alt="g" class="ee_img tr_noresize" eeimg="1"> 编码 | 5个GMM模式的权重、均值、标准差 | 接收编码后的状态和目标向量              |

| **输出层**           | -            | LSTM隐藏状态                         | 15个值（5模式×3参数）          | 输出5个高斯混合模式的权重、均值、标准差 |


使用负对数似然损失训练模型，进行450万次梯度下降，在配备批量大小为16的4090 GPU上需要2天时间。

![image-20251020181400380](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Neural_MP论文阅读/image-20251020181400380_1.png)

### 三层 PointNet++ Set Abstraction (SA) 模块：

**第一层 SA 模块**

```
PointnetSAModule(
    npoint=128,      # 采样128个中心点
    radius=0.05,     # 搜索半径0.05米
    nsample=64,      # 每个区域采样64个点
    mlp=[1, 64, 64, 64],  # 通道数: 1→64→64→64
)
```

-  **作用**：局部特征提取，处理细粒度几何结构

**第二层 SA 模块**

```
PointnetSAModule(
    npoint=64,       # 采样64个中心点  
    radius=0.3,      # 扩大搜索半径
    nsample=64,      # 每个区域采样64个点
    mlp=[64, 128, 128, 256],  # 通道数: 64→128→128→256
)
```

-  **作用**：提取更大范围的局部特征

**第三层 SA 模块**

```
PointnetSAModule(
    nsample=64,      # 全局采样64个点
    mlp=[256, 512, 512],  # 通道数: 256→512→512
)
```

-  **作用**：全局特征提取，不进行下采样

**MLP 特征映射**

```
MLP(
    Linear(512, 2048),      # 512维 → 2048维
    GroupNorm(16, 2048),    # 分组归一化，16组
    LeakyReLU,              # 激活函数
    Linear(2048, 1024),     # 2048维 → 1024维  
    GroupNorm(16, 1024),    # 分组归一化
    LeakyReLU,
    Linear(1024, 1024)      # 输出1024维特征向量
)
```

 **LSTM 解码器**

```
LSTM(
    hidden_dim=1024,    # 隐藏层维度1024
    num_layers=2        # 2层LSTM
)
```

-  **输入**：PointNet++输出(1024维) + 关节角度编码 + 目标编码
-  **输出**：15个值 = 5个GMM模式 × (权重 + 均值 + 标准差)



## 部署神经网络规划器

### 测试优化

依赖于一个简单的模型，该模型假设障碍物不移动，并且控制器可以准确地到达目标航路点，使用初始场景点云从策略中采样 N 条轨迹，以提供障碍物表示，并使用线性前向模型估计与机器人相交的场景点数量。然后，使用机器人与场景相交最少的路径。

<img src="https://www.zhihu.com/equation?tex=\min_{\tau \sim \rho_{\pi_{\theta}}} \sum_{t=1}^{T} \sum_{k=1}^{K} \mathbf{1}\{SDF_{q_t}(\text{PCD}_O^k) < \epsilon\}
" alt="\min_{\tau \sim \rho_{\pi_{\theta}}} \sum_{t=1}^{T} \sum_{k=1}^{K} \mathbf{1}\{SDF_{q_t}(\text{PCD}_O^k) < \epsilon\}
" class="ee_img tr_noresize" eeimg="1">

*    <img src="https://www.zhihu.com/equation?tex=\min_{\tau \sim \rho_{\pi_{\theta}}}" alt="\min_{\tau \sim \rho_{\pi_{\theta}}}" class="ee_img tr_noresize" eeimg="1"> ：表示在**策略  <img src="https://www.zhihu.com/equation?tex=\pi_{\theta}" alt="\pi_{\theta}" class="ee_img tr_noresize" eeimg="1">  生成的轨迹分布  <img src="https://www.zhihu.com/equation?tex=\rho_{\pi_{\theta}}" alt="\rho_{\pi_{\theta}}" class="ee_img tr_noresize" eeimg="1">  中**，寻找使目标函数值最小的轨迹  <img src="https://www.zhihu.com/equation?tex=\tau" alt="\tau" class="ee_img tr_noresize" eeimg="1"> 。这里的  <img src="https://www.zhihu.com/equation?tex=\pi_{\theta}" alt="\pi_{\theta}" class="ee_img tr_noresize" eeimg="1">  是通过线性模型描述的轨迹分布策略。

*    <img src="https://www.zhihu.com/equation?tex=\sum_{t=1}^{T}" alt="\sum_{t=1}^{T}" class="ee_img tr_noresize" eeimg="1"> ：表示对轨迹中的所有时间步 (timestep) 进行求和，从  <img src="https://www.zhihu.com/equation?tex=t=1" alt="t=1" class="ee_img tr_noresize" eeimg="1">  到  <img src="https://www.zhihu.com/equation?tex=T" alt="T" class="ee_img tr_noresize" eeimg="1"> 。 <img src="https://www.zhihu.com/equation?tex=T" alt="T" class="ee_img tr_noresize" eeimg="1">  是轨迹的总时间步长。

*    <img src="https://www.zhihu.com/equation?tex=\sum_{k=1}^{K}" alt="\sum_{k=1}^{K}" class="ee_img tr_noresize" eeimg="1"> ：表示对障碍物点云中的所有点进行求和，从  <img src="https://www.zhihu.com/equation?tex=k=1" alt="k=1" class="ee_img tr_noresize" eeimg="1">  到  <img src="https://www.zhihu.com/equation?tex=K" alt="K" class="ee_img tr_noresize" eeimg="1"> 。 <img src="https://www.zhihu.com/equation?tex=K" alt="K" class="ee_img tr_noresize" eeimg="1">  是障碍物点云的最大点数，这里设定为  <img src="https://www.zhihu.com/equation?tex=4096" alt="4096" class="ee_img tr_noresize" eeimg="1"> 。

*    <img src="https://www.zhihu.com/equation?tex=\mathbf{1}\{ \cdot \}" alt="\mathbf{1}\{ \cdot \}" class="ee_img tr_noresize" eeimg="1"> ：表示**指示函数 (indicator function)**。当括号内的条件为真时，函数值为  <img src="https://www.zhihu.com/equation?tex=1" alt="1" class="ee_img tr_noresize" eeimg="1"> ；当条件为假时，函数值为  <img src="https://www.zhihu.com/equation?tex=0" alt="0" class="ee_img tr_noresize" eeimg="1"> 。

*    <img src="https://www.zhihu.com/equation?tex=SDF_{q_t}(\text{PCD}_O^k)" alt="SDF_{q_t}(\text{PCD}_O^k)" class="ee_img tr_noresize" eeimg="1"> ：表示**符号距离函数的值。计算在时间步  <img src="https://www.zhihu.com/equation?tex=t" alt="t" class="ee_img tr_noresize" eeimg="1">  时，机器人处于关节角度  <img src="https://www.zhihu.com/equation?tex=q_t" alt="q_t" class="ee_img tr_noresize" eeimg="1">  状态下，机器人表面到**障碍物点云中的第  <img src="https://www.zhihu.com/equation?tex=k" alt="k" class="ee_img tr_noresize" eeimg="1">  个点  <img src="https://www.zhihu.com/equation?tex=\text{PCD}_O^k" alt="\text{PCD}_O^k" class="ee_img tr_noresize" eeimg="1"> 的最短距离。
    *   ** <img src="https://www.zhihu.com/equation?tex=\text{PCD}_O^k" alt="\text{PCD}_O^k" class="ee_img tr_noresize" eeimg="1"> **：表示障碍物点云 (obstacle point-cloud) 中的第  <img src="https://www.zhihu.com/equation?tex=k" alt="k" class="ee_img tr_noresize" eeimg="1">  个点。
    *   ** <img src="https://www.zhihu.com/equation?tex=SDF_{q_t}" alt="SDF_{q_t}" class="ee_img tr_noresize" eeimg="1"> **：表示在机器人当前关节角度  <img src="https://www.zhihu.com/equation?tex=q_t" alt="q_t" class="ee_img tr_noresize" eeimg="1">  下，机器人自身的符号距离函数。
    
*    <img src="https://www.zhihu.com/equation?tex=\epsilon" alt="\epsilon" class="ee_img tr_noresize" eeimg="1"> ：一个小的正阈值。当  <img src="https://www.zhihu.com/equation?tex=SDF_{q_t}(\text{PCD}_O^k) < \epsilon" alt="SDF_{q_t}(\text{PCD}_O^k) < \epsilon" class="ee_img tr_noresize" eeimg="1">  时，表示障碍物点  <img src="https://www.zhihu.com/equation?tex=\text{PCD}_O^k" alt="\text{PCD}_O^k" class="ee_img tr_noresize" eeimg="1">  距离机器人表面非常近，甚至发生碰撞。

    ![image-20251020095534346](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Neural_MP论文阅读/image-20251020095534346_1.png)

    左：使用专家规划器在模拟中生成大规模数据；中：训练深度网络模型以执行快速反应式运动规划；右：在推理时进行测试时优化以提高性能。

    ![image-20251020180900384](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Neural_MP论文阅读/image-20251020180900384_1.png)

    开环执行

### sim2real

使用4个相机计算场景的点云，并使用基于网格的机器人表示分割出部分机器人云，以排除点。然后，使用基于网格的机器人表示上的正向运动学生成当前的机器人和目标机器人点云，并将它们放置到场景中。对于基于视觉的真实世界碰撞检测，我们计算点云和机器人的球形表示之间的SDF，从而实现快速SDF计算（每次查询0.01-0.02秒）。

感觉物理调试sim2real的细节要占了一半的篇幅，涉及到物理，调试就很麻烦了看来。

