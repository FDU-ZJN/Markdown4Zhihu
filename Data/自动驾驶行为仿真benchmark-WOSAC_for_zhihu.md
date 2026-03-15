---
title: 自动驾驶行为仿真benchmark-WOSAC
date: 2025-11-23 19:01:21
categories: 计算机
tags:
  - 自动驾驶
  - 论文
cover: /img/cover_22.jpg
highlight_shrink: true
abbrlink: 3513334553
description: 自动驾驶行为仿真现在最主流的benchmark
---

>  核心大概就是看基准测试的含义和评估方法

## 目标

通过定义一个数据驱动的评估框架，并使用公开可访问的数据来实例化它，从而鼓励交通模拟器的设计。

## 整体框架

将驾驶建模为一个隐马尔可夫模型

![image-20251123194036636](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶行为仿真benchmark-WOSAC/image-20251123194036636.png)

![image-20251124083143152](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶行为仿真benchmark-WOSAC/image-20251124083143152.png)

>  不知道为什么这个表格传到博客一直公式格式不对，放弃了，就用图片吧

每个时刻的观测值  <img src="https://www.zhihu.com/equation?tex=o_t" alt="o_t" class="ee_img tr_noresize" eeimg="1">  被分为两部分 ：

 <img src="https://www.zhihu.com/equation?tex=o_{t}^{AV}" alt="o_{t}^{AV}" class="ee_img tr_noresize" eeimg="1"> ：**自动驾驶车辆 (AV)** 的状态。

 <img src="https://www.zhihu.com/equation?tex=o_{t}^{env}" alt="o_{t}^{env}" class="ee_img tr_noresize" eeimg="1"> ：**环境 ** 的状态（虽然环境通常包含丰富特征，但在论文中， <img src="https://www.zhihu.com/equation?tex=o_{t}^{env}" alt="o_{t}^{env}" class="ee_img tr_noresize" eeimg="1">  仅包含非 AV 代理（如其他车辆、行人的位姿 ）。

## 任务

构建世界模型 <img src="https://www.zhihu.com/equation?tex=q_{world}(ot|oc<t)" alt="q_{world}(ot|oc<t)" class="ee_img tr_noresize" eeimg="1"> ,即根据历史观测信息 `oc<t`（包括静态地图、交通信号灯和历史轨迹）生成下一时刻的观测 `ot`

### 两个约束：

自回归性 : 模型必须以10Hz的频率自回归地运行T个步骤，重新观察更新后的场景并消耗它们之前的输出。（人话：闭环，使用自己前一步输出作为当前输入）

因子分解 : 世界模型 q_world 必须分解为自动驾驶汽车（AV）的策略  <img src="https://www.zhihu.com/equation?tex=π(o^{AV}_t|oc<t)" alt="π(o^{AV}_t|oc<t)" class="ee_img tr_noresize" eeimg="1"> 和环境动态模型  <img src="https://www.zhihu.com/equation?tex=q(o^{env}_t|oc<t)" alt="q(o^{env}_t|oc<t)" class="ee_img tr_noresize" eeimg="1">  的乘积。这意味着AV的行为模型和环境中其他智能体的行为模型是分离的。

![image-20251123194543638](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶行为仿真benchmark-WOSAC/image-20251123194543638.png)

>  也就是不允许开环生成的

### 挑战

真实世界的交通情况 `p_world` 具有**多模态不确定性**。在同一个历史场景  <img src="https://www.zhihu.com/equation?tex=s_{t-1}" alt="s_{t-1}" class="ee_img tr_noresize" eeimg="1">  下，未来可能有多种合理的发展方向。因此，一个优秀的模型（无论是AV策略 `π` 还是环境模型 `q`）必须能够捕捉并生成这种**多模态**的结果，而不是只给出一个最可能的预测。

通过比较模型生成的整个概率分布 `p_world` 与真实记录的数据集之间的匹配程度来评估性能。

## 评估

### 数据集

挑战赛使用Waymo开放运动数据集（WOMD）v1.2.0的测试集。每个场景包含1.1秒的历史数据和8秒的未来数据，频率为10Hz。参赛者需要仿真场景中所有在t=0时刻存在的智能体（车辆、骑行者、行人），最多128个。

### 评估方式

**逼真智能体 的定义：** 智能体（仿真模型）生成的场景分布必须**匹配**在真实世界驾驶中观察到的实际场景分布。

如果我们知道真实世界分布  <img src="https://www.zhihu.com/equation?tex=p^{world}" alt="p^{world}" class="ee_img tr_noresize" eeimg="1">  的解析形式，我们应该最小化**负对数似然**

![image-20251123200638939](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶行为仿真benchmark-WOSAC/image-20251123200638939.png)

#### 问题

真实世界的整个未来场景是一个**高维**数据点（对象，时间步，多种数据等等），难以直接计算其似然值。

许多生成模型只能**采样**，但无法进行**点似然估计**（即无法给出特定真实场景出现的精确概率）。挑战赛也只要求提交样本。

>  就是仿真模型可以生成 32 条合理的未来轨迹（采样）。但是，要让它精确计算“真实世界中，一辆车以 1.5m/s 的加速度、在十字路口右转”这个精确事件的概率无法实现。

#### 解决

不直接计算整个场景的似然，而是将场景分解为更少数量的**组件指标**，然后将这些组件的 NLL **聚合**成一个**综合 NLL** 指标。

对每个rollout，计算9个不同的组件指标。这些指标分为三类：

运动学指标: 线速度、线加速度、角速度、角加速度。

交互指标 : 到最近物体的距离、碰撞、碰撞时间（TTC）。

地图相关指标: 到路边的距离、偏离道路。


要求参赛者提交 **32 个样本 **。对这 32 个样本进行拟合，生成**直方图**，从而得到一个**分类分布 **。最终，基于这个分类分布来计算真实世界样本的近似 NLL。

最终的综合指标 `MK` 是所有9个组件指标NLL的加权平均值。为了强调安全性，**碰撞**和**偏离道路**这两个指标的权重是其他指标的2倍。

![image-20251123201509489](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶行为仿真benchmark-WOSAC/image-20251123201509489.png)

>让AI写了一个例子稍微改了改，感觉能帮助理解：
>
>对于一个特定的测试场景  <img src="https://www.zhihu.com/equation?tex=i" alt="i" class="ee_img tr_noresize" eeimg="1"> 
>
>1. 你的模型提交了 **32 个**样本轨迹。
>2. 评估系统计算这 32 个样本中，所有 **智能体** 在所有 **80 个时间步**上的所有**线加速度**值。
>

<img src="https://www.zhihu.com/equation?tex=\text{总数据量} = 32 \text{ (样本)} \times 80 \text{ (时间步)} \times N \text{ (智能体数量)}" alt="\text{总数据量} = 32 \text{ (样本)} \times 80 \text{ (时间步)} \times N \text{ (智能体数量)}" class="ee_img tr_noresize" eeimg="1">
>
>-  所有这些数千个瞬时加速度值被**合并成一个巨大的集合**。这个集合就是你的模型  <img src="https://www.zhihu.com/equation?tex=q^{world}" alt="q^{world}" class="ee_img tr_noresize" eeimg="1">  在该场景下、该指标上的**近似分布的基础**。
>-  然后，评估系统对这个巨大的集合拟合出**一个单一的直方图**。
>
>接下来，评估系统处理真实数据：
>
>1. 取出**真实世界**日志中，所有智能体在所有 80 个时间步上的**线加速度**值。
>2. 对 **每一个** 真实的瞬时加速度值，评估系统都去查询它落在**步骤 1 构建的直方图**的哪个区间  <img src="https://www.zhihu.com/equation?tex=j" alt="j" class="ee_img tr_noresize" eeimg="1"> 。
>3. 计算这个真实瞬时值的 NLL： <img src="https://www.zhihu.com/equation?tex=-\log(P_j)" alt="-\log(P_j)" class="ee_img tr_noresize" eeimg="1"> 。
>
>**指标 NLL：** 最终的  <img src="https://www.zhihu.com/equation?tex=\text{NLL}_{\text{accel}}" alt="\text{NLL}_{\text{accel}}" class="ee_img tr_noresize" eeimg="1">  是所有真实瞬时加速度值的 NLL 的**平均值**。

## 基础指标（基线）

### 基线模型:

Random Agent: 产生高斯随机轨迹。

Constant Velocity: 按最后时刻的速度和朝向进行匀速直线外推。

Wayformer (Identical/Diverse Samples): 使用Wayformer预测模型，以2Hz或10Hz的频率进行重规划，生成相同或多样化的样本。

Logged Oracle: 直接复制真实数据作为理想上限。

### 外部提交方案:

MVTA/MVTE: 挑战赛冠军。采用闭环训练，并结合了MTR和TrafficSim的思想，使用GMM头和可变长度历史。MVTE是MVTA的多模型集成版本，以增加多样性。

MTR+++: 一种混合开环/闭环方法，在MTR基础上改进，通过在无碰撞轨迹图中寻找最稠密子图来减少碰撞。

CAD: 一种开环方法，使用MTR进行预测，并通过拒绝采样来过滤掉会产生碰撞的未来。

### 指标

![image-20251124081617313](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶行为仿真benchmark-WOSAC/image-20251124081617313.png)

![image-20251124081637018](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶行为仿真benchmark-WOSAC/image-20251124081637018.png)

指标要和这些做比较了

### 结果分析

#### 主要趋势

**闭环训练的优势**：采用闭环训练方法的模型（如挑战赛冠军方案MVTA/MVTE）展现出显著优势。

**开环模型的重新规划频率**：对于基于开环预测模型（如Wayformer）的方法，一个反直觉的发现是，**较低的重规划频率（如2Hz）性能反而优于较高的频率（如10Hz）**。大概就是出现误差很难自己纠正，会一直累积下来，闭环能纠正，就好一些。

![image-20251124082126253](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶行为仿真benchmark-WOSAC/image-20251124082126253.png)

**主流技术路径**：绝大多数成功的提交方案都基于**Transformer架构**，并强烈依赖于先进的**运动预测模型**（特别是MTR）作为其核心组件。

#### 指标特性洞察

**似然度指标**：该指标奖励能够捕捉未来不确定性的模型。因此，能够生成多样化未来轨迹的 Wayformer在该指标上明显优于只输出单一最大似然轨迹的 Wayformer。

**综合排名相关性**：最终的综合性指标排名与 **minADE**（衡量最佳预测与真值之间的误差）显示出一定的正相关性。然而，它与 **ADE**（衡量所有预测的平均误差）没有明显关联，这表明评估体系更看重模型“至少能给出一个正确预测”的能力，而非所有预测的平均表现。

#### 组件指标深度分析

表现最佳的**MVTE**模型在大多数组件指标上都处于领先地位。然而，在涉及**智能体间交互**的特定指标上，如“到最近物体的距离”和“碰撞似然度”，它与作为理想上限的“Logged Oracle”仍存在显著差距。还有提升的空间.jpg。

#### 定性结果佐证

在复杂的交叉口场景中，简单的启发式模型（如恒速模型）会生成导致碰撞的不合理轨迹。相比之下，数据驱动的学习型模型能够产生安全、平滑且符合人类驾驶习惯的行为。

![image-20251124082413655](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶行为仿真benchmark-WOSAC/image-20251124082413655.png)