---
title: 自动驾驶仿真扩散模型-VBD
date: 2025-11-24 18:47:52
categories: 计算机
tags:
  - 自动驾驶
  - 论文
cover: /img/cover_23.jpg
highlight_shrink: true
abbrlink: 3513325653
description: WOSAC第二名，使用扩散模型
---

>  直觉上感觉扩散模型确实挺适合的，生成图片和生成这种场景都是从有噪声的初始场景出发去噪声



## 理论基础——动力学

### 正向模拟

将智能体的**动作**转换为下一个**状态**

**输入（动作）：** 加速度  <img src="https://www.zhihu.com/equation?tex=\dot{v}" alt="\dot{v}" class="ee_img tr_noresize" eeimg="1"> 、航向角变化率  <img src="https://www.zhihu.com/equation?tex=\dot{\psi}" alt="\dot{\psi}" class="ee_img tr_noresize" eeimg="1"> ，时间步长  <img src="https://www.zhihu.com/equation?tex=\Delta t" alt="\Delta t" class="ee_img tr_noresize" eeimg="1"> 。

**当前状态：** 全局坐标  <img src="https://www.zhihu.com/equation?tex=(x, y)" alt="(x, y)" class="ee_img tr_noresize" eeimg="1"> 、航向角  <img src="https://www.zhihu.com/equation?tex=\psi" alt="\psi" class="ee_img tr_noresize" eeimg="1"> 、速度分量  <img src="https://www.zhihu.com/equation?tex=v_x, v_y" alt="v_x, v_y" class="ee_img tr_noresize" eeimg="1"> 。

**输出：** 下一个时间步的状态  <img src="https://www.zhihu.com/equation?tex=(x(t+1), y(t+1), \psi(t+1), v(t+1), v_x(t+1), v_y(t+1))" alt="(x(t+1), y(t+1), \psi(t+1), v(t+1), v_x(t+1), v_y(t+1))" class="ee_img tr_noresize" eeimg="1"> 

![image-20251124191022584](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251124191022584.png)

### 反向推演

根据**状态的变化**计算出相应的**动作**。

**输入（状态）：**  <img src="https://www.zhihu.com/equation?tex=t+1" alt="t+1" class="ee_img tr_noresize" eeimg="1">  时刻和  <img src="https://www.zhihu.com/equation?tex=t" alt="t" class="ee_img tr_noresize" eeimg="1">  时刻的智能体状态（主要是速度和航向角）。

**输出（动作）：**  <img src="https://www.zhihu.com/equation?tex=t" alt="t" class="ee_img tr_noresize" eeimg="1">  时刻的加速度  <img src="https://www.zhihu.com/equation?tex=\dot{v}(t)" alt="\dot{v}(t)" class="ee_img tr_noresize" eeimg="1">  和航向角变化率  <img src="https://www.zhihu.com/equation?tex=\dot{\psi}(t)" alt="\dot{\psi}(t)" class="ee_img tr_noresize" eeimg="1"> 。

![image-20251124191147559](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251124191147559.png)

## 模型整体结构

![image-20251124191405282](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251124191405282.png)

由三个核心组件组成

| **组件 **                             | **功能**                                                     | **输入**                                                     | **输出**                                |

| ------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ | --------------------------------------- |

| **场景编码器** ( <img src="https://www.zhihu.com/equation?tex=\mathcal{E}_{\phi}" alt="\mathcal{E}_{\phi}" class="ee_img tr_noresize" eeimg="1"> ) | 提取并编码**场景上下文信息**，生成简洁且富有信息的**潜在表征**。 | 1. 智能体的历史轨迹信息。 2. 地图折线的几何信息。            | 潜在表征  <img src="https://www.zhihu.com/equation?tex=\hat{c}" alt="\hat{c}" class="ee_img tr_noresize" eeimg="1">  ，作为后续模块的条件 |

| **行为预测器**                        | 基于场景条件和预设目标，预测**每个智能体**的**多模式**（ <img src="https://www.zhihu.com/equation?tex=M" alt="M" class="ee_img tr_noresize" eeimg="1">  种）未来轨迹分布。 | 1. 潜在表征  <img src="https://www.zhihu.com/equation?tex=\hat{c}" alt="\hat{c}" class="ee_img tr_noresize" eeimg="1">  (来自场景编码器)。 2. 静态终点锚点（无限的轨迹目的地变为有限的锚点） 。 | 每个智能体独立的预测轨迹集合。          |

| **去噪器** ( <img src="https://www.zhihu.com/equation?tex=\mathcal{D}_{\theta}" alt="\mathcal{D}_{\theta}" class="ee_img tr_noresize" eeimg="1"> )   | 通过去噪过程，从带噪声的输入中生成**所有智能体**之间相互协调的**联合规划**。 | 1. 潜在表征  <img src="https://www.zhihu.com/equation?tex=\hat{c}" alt="\hat{c}" class="ee_img tr_noresize" eeimg="1">  (来自场景编码器)。 2. 带噪声的轨迹  <img src="https://www.zhihu.com/equation?tex=\tilde{u}, \tilde{x}" alt="\tilde{u}, \tilde{x}" class="ee_img tr_noresize" eeimg="1"> 。 3. 噪声水平的位置编码。 | 所有智能体协调一致的未来集体轨迹。      |


## 场景编码器

>  果然到现在都是各种魔改transformer了，不会是原版那种简单的自注意力了

### 输入

| **输入张量 **  | **尺寸**         | 初始编码方法                            | **特征内容**                                                 | 编码输出                                    |

| -------------- | ---------------- | --------------------------------------- | ------------------------------------------------------------ | ------------------------------------------- |

| **智能体历史** |  <img src="https://www.zhihu.com/equation?tex=[A, T_h, D_a]" alt="[A, T_h, D_a]" class="ee_img tr_noresize" eeimg="1">   | 共享 **GRU** 网络 + 智能体类型嵌入      |  <img src="https://www.zhihu.com/equation?tex=x, y" alt="x, y" class="ee_img tr_noresize" eeimg="1">  坐标、航向角 ( <img src="https://www.zhihu.com/equation?tex=\psi" alt="\psi" class="ee_img tr_noresize" eeimg="1"> )、速度 ( <img src="https://www.zhihu.com/equation?tex=v_x, v_y" alt="v_x, v_y" class="ee_img tr_noresize" eeimg="1"> )、边界框尺寸。 | ** <img src="https://www.zhihu.com/equation?tex=[A, D]" alt="[A, D]" class="ee_img tr_noresize" eeimg="1"> **                                |

| **地图折线**   |  <img src="https://www.zhihu.com/equation?tex=[Ml, M_p, D_p]" alt="[Ml, M_p, D_p]" class="ee_img tr_noresize" eeimg="1">  | **MLP** + **Max-Pooling** (沿  <img src="https://www.zhihu.com/equation?tex=M_p" alt="M_p" class="ee_img tr_noresize" eeimg="1">  轴) |  <img src="https://www.zhihu.com/equation?tex=x, y" alt="x, y" class="ee_img tr_noresize" eeimg="1">  坐标、方向角、车道类型、停止点坐标。                  | MLP →  <img src="https://www.zhihu.com/equation?tex=[Ml, M_p, D]" alt="[Ml, M_p, D]" class="ee_img tr_noresize" eeimg="1"> ，再池化聚合为 <img src="https://www.zhihu.com/equation?tex=[Ml, D]" alt="[Ml, D]" class="ee_img tr_noresize" eeimg="1">  |

| **交通灯**     |  <img src="https://www.zhihu.com/equation?tex=[Mt, D_t]" alt="[Mt, D_t]" class="ee_img tr_noresize" eeimg="1">       | **MLP**                                 |  <img src="https://www.zhihu.com/equation?tex=x, y" alt="x, y" class="ee_img tr_noresize" eeimg="1">  坐标、灯光状态                                        | MLP  <img src="https://www.zhihu.com/equation?tex=[Mt, D]" alt="[Mt, D]" class="ee_img tr_noresize" eeimg="1">                                |


 <img src="https://www.zhihu.com/equation?tex=A" alt="A" class="ee_img tr_noresize" eeimg="1"> ：智能体数量 (如  <img src="https://www.zhihu.com/equation?tex=A=64" alt="A=64" class="ee_img tr_noresize" eeimg="1"> )

 <img src="https://www.zhihu.com/equation?tex=T_h" alt="T_h" class="ee_img tr_noresize" eeimg="1"> ：历史时间步长 

 <img src="https://www.zhihu.com/equation?tex=Ml" alt="Ml" class="ee_img tr_noresize" eeimg="1"> ：地图折线数量 

 <img src="https://www.zhihu.com/equation?tex=M_p" alt="M_p" class="ee_img tr_noresize" eeimg="1"> ：折线上的航点数量

 <img src="https://www.zhihu.com/equation?tex=Mt" alt="Mt" class="ee_img tr_noresize" eeimg="1"> ：交通灯数量

 <img src="https://www.zhihu.com/equation?tex=D" alt="D" class="ee_img tr_noresize" eeimg="1"> ：特征大小

**初始场景编码张量尺寸：** 三种张量经过处理后，被拼接 形成初始张量，尺寸为  <img src="https://www.zhihu.com/equation?tex=[A + M, D]" alt="[A + M, D]" class="ee_img tr_noresize" eeimg="1"> ，其中  <img src="https://www.zhihu.com/equation?tex=M = Ml + Mt" alt="M = Ml + Mt" class="ee_img tr_noresize" eeimg="1">  是地图元素的总数。

>  **地图折线**这个池化聚合觉得很激进，一条线聚成了一个点了，大概就是最突出的、最极端的特征，比如急转弯的那个点
>
>  GRU学了一下，这一篇[(36 封私信 / 80 条消息) 人人都能看懂的GRU - 知乎](https://zhuanlan.zhihu.com/p/32481747)讲的不错，简单说就是个高效的处理时间序列的RNN，T_h的时间序列的轨迹间肯定是有关系的，所以用RNN聚合压缩，2014年的。
>
>  >  RNN:我不明白，为什么大家都在谈论Transformer，仿佛这语言处理对我们注定了凶多吉少。。。。那种勃勃生机、万物竞发的境界，犹在眼前。短短三年之后，这里竟至于一变而成为我们的葬身之地了么？
>  >
>  >  <img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251124195519814.png" alt="image-20251124195519814" style="zoom: 50%;" />
>
>  智能体类型嵌入我觉得和刚看Transformer的词嵌入差不多，都是转为能反映语义关系的向量。

### 针对设计

#### 局部坐标系

 在编码之前，所有元素的**位置属性**都被转换到它们的**局部坐标系**中。

**智能体**参考点是它们的**最后记录状态**。地图元素参考点是它们的第一个航点。

 这样做可以使模型对场景的绝对位置不敏感，专注于**相对关系**和**局部环境**，提高模型的**泛化能力**。

#### 边属性  <img src="https://www.zhihu.com/equation?tex=e^{ij}" alt="e^{ij}" class="ee_img tr_noresize" eeimg="1">  

对于**每对场景元素**  <img src="https://www.zhihu.com/equation?tex=(i, j)" alt="(i, j)" class="ee_img tr_noresize" eeimg="1"> ，它们之间的**相对位置**被计算出来，并使用 **MLP** 编码成边属性  <img src="https://www.zhihu.com/equation?tex=e^{ij}" alt="e^{ij}" class="ee_img tr_noresize" eeimg="1"> 。

### 基于查询的注意力

![image-20251124201548252](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251124201548252.png)

修改的地方就是将**边属性  <img src="https://www.zhihu.com/equation?tex=\mathbf{e}^{ij}" alt="\mathbf{e}^{ij}" class="ee_img tr_noresize" eeimg="1">  同时加到 Key 和 Value** 中，然后使用的是交叉注意力，q来自自身i,K,V来自邻域j。

这样模型可以**显式地**将两个元素之间的**几何和空间关系**融入到注意力权重计算和特征聚合中，允许模型**对称地**处理不同类型的元素之间的相互作用，例如车辆对交通灯的关注，或行人对车辆的避让，都通过  <img src="https://www.zhihu.com/equation?tex=\mathbf{e}^{ij}" alt="\mathbf{e}^{ij}" class="ee_img tr_noresize" eeimg="1">  的加持得到更精确的建模。

### 整体结构

**层数:** 6 个 **Post-norm** 基于查询的 Transformer 层。

**激活函数:** **GELU** 激活函数。

**注意力头:** 每层 8 个注意力头。

**维度 :** 隐藏维度  <img src="https://www.zhihu.com/equation?tex=D=256" alt="D=256" class="ee_img tr_noresize" eeimg="1"> 。

**最终输出尺寸:** 场景编码张量保持初始形状  <img src="https://www.zhihu.com/equation?tex=[A+M, D]" alt="[A+M, D]" class="ee_img tr_noresize" eeimg="1"> ，作为下游模块的潜在表征  <img src="https://www.zhihu.com/equation?tex=\hat{c}" alt="\hat{c}" class="ee_img tr_noresize" eeimg="1"> 。

## 去噪器

![image-20251124204327199](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251124204327199.png)

### 输入

**带噪声的动作  <img src="https://www.zhihu.com/equation?tex=\tilde{\mathbf{u}}" alt="\tilde{\mathbf{u}}" class="ee_img tr_noresize" eeimg="1"> ：** 尺寸为  <img src="https://www.zhihu.com/equation?tex=[A, T_f, 2]" alt="[A, T_f, 2]" class="ee_img tr_noresize" eeimg="1"> ，其中 2 代表动作向量  <img src="https://www.zhihu.com/equation?tex=[\dot{v}, \dot{\psi}]^T" alt="[\dot{v}, \dot{\psi}]^T" class="ee_img tr_noresize" eeimg="1"> 。它是从地面真值中提取并加入噪声的。

**噪声水平：** 通过一个嵌入层编码为  <img src="https://www.zhihu.com/equation?tex=[1, 1, D]" alt="[1, 1, D]" class="ee_img tr_noresize" eeimg="1">  的张量。

**场景编码张量 ：** 尺寸为  <img src="https://www.zhihu.com/equation?tex=[A+M, D]" alt="[A+M, D]" class="ee_img tr_noresize" eeimg="1"> 。

#### 处理流程

使用**前向动力学模型  <img src="https://www.zhihu.com/equation?tex=f" alt="f" class="ee_img tr_noresize" eeimg="1"> ** 将  <img src="https://www.zhihu.com/equation?tex=\tilde{\mathbf{u}}" alt="\tilde{\mathbf{u}}" class="ee_img tr_noresize" eeimg="1">  转换为带噪声的状态  <img src="https://www.zhihu.com/equation?tex=\tilde{\mathbf{x}}" alt="\tilde{\mathbf{x}}" class="ee_img tr_noresize" eeimg="1"> 。

 使用 **MLP** 将  <img src="https://www.zhihu.com/equation?tex=\tilde{\mathbf{x}}" alt="\tilde{\mathbf{x}}" class="ee_img tr_noresize" eeimg="1">  编码成尺寸为  <img src="https://www.zhihu.com/equation?tex=[A, T_f, D]" alt="[A, T_f, D]" class="ee_img tr_noresize" eeimg="1">  的张量。

将这个  <img src="https://www.zhihu.com/equation?tex=[A, T_f, D]" alt="[A, T_f, D]" class="ee_img tr_noresize" eeimg="1">  维度的张量与**噪声水平嵌入**和时间位置嵌入结合，形成送入解码器的初始轨迹嵌入。

### 自注意力

输入来自来自**上一层**的**智能体轨迹特征**。 <img src="https://www.zhihu.com/equation?tex=[A \cdot T_f, D]" alt="[A \cdot T_f, D]" class="ee_img tr_noresize" eeimg="1"> 

>  跟上面三维有点对不上，应该是reshape了一下

使用**因果关系掩码**，确保当前时间步  <img src="https://www.zhihu.com/equation?tex=t" alt="t" class="ee_img tr_noresize" eeimg="1">  只能看到过去信息，防作弊。负责处理智能体之间的相互作用和时序因果关系。

输出还是 <img src="https://www.zhihu.com/equation?tex=[A \cdot T_f, D]" alt="[A \cdot T_f, D]" class="ee_img tr_noresize" eeimg="1"> 

### 交叉注意力

| 角色                    | 输入                                                         | 尺寸               |

| ----------------------- | ------------------------------------------------------------ | ------------------ |

| **查询 ( <img src="https://www.zhihu.com/equation?tex=\mathbf{Q}" alt="\mathbf{Q}" class="ee_img tr_noresize" eeimg="1"> )** | 来自**自注意力层的输出**（建模了联合关系的轨迹特征）。       |  <img src="https://www.zhihu.com/equation?tex=[A \cdot T_f, D]" alt="[A \cdot T_f, D]" class="ee_img tr_noresize" eeimg="1">  |

| **键 ( <img src="https://www.zhihu.com/equation?tex=\mathbf{K}" alt="\mathbf{K}" class="ee_img tr_noresize" eeimg="1"> )**   | **场景编码张量  <img src="https://www.zhihu.com/equation?tex=\hat{\mathbf{c}}" alt="\hat{\mathbf{c}}" class="ee_img tr_noresize" eeimg="1"> ** (来自  <img src="https://www.zhihu.com/equation?tex=\mathcal{E}_{\phi}" alt="\mathcal{E}_{\phi}" class="ee_img tr_noresize" eeimg="1"> )。 |  <img src="https://www.zhihu.com/equation?tex=[A+M, D]" alt="[A+M, D]" class="ee_img tr_noresize" eeimg="1">          |

| **值 ( <img src="https://www.zhihu.com/equation?tex=\mathbf{V}" alt="\mathbf{V}" class="ee_img tr_noresize" eeimg="1"> )**   | 同 Key。                                                     |  <img src="https://www.zhihu.com/equation?tex=[A+M, D]" alt="[A+M, D]" class="ee_img tr_noresize" eeimg="1">          |


K,V来自场景编码，Q来自自注意力输出，通过交叉注意力处理**外在约束**（场景和地图对轨迹的限制）

### 输出

Transformer 解码阶段后，得到的轨迹嵌入 被送入一个 **MLP** 进行最终解码。

**最终输出：** 清理后的动作张量  <img src="https://www.zhihu.com/equation?tex=\hat{\mathbf{u}}" alt="\hat{\mathbf{u}}" class="ee_img tr_noresize" eeimg="1"> ，尺寸为  <img src="https://www.zhihu.com/equation?tex=[A, T_f, 2]" alt="[A, T_f, 2]" class="ee_img tr_noresize" eeimg="1"> 。

**状态推导：** 使用**前向动力学模型  <img src="https://www.zhihu.com/equation?tex=f" alt="f" class="ee_img tr_noresize" eeimg="1"> ** 将这些预测的动作  <img src="https://www.zhihu.com/equation?tex=\hat{\mathbf{u}}" alt="\hat{\mathbf{u}}" class="ee_img tr_noresize" eeimg="1">  转化为清理后的状态轨迹  <img src="https://www.zhihu.com/equation?tex=[A, T, 3]" alt="[A, T, 3]" class="ee_img tr_noresize" eeimg="1"> （包括  <img src="https://www.zhihu.com/equation?tex=x, y, \psi" alt="x, y, \psi" class="ee_img tr_noresize" eeimg="1"> ）。

## 行为预测器

### 输入

#### Q

**智能体的静态锚点**，形状为  <img src="https://www.zhihu.com/equation?tex=[A, Mo, 2]" alt="[A, Mo, 2]" class="ee_img tr_noresize" eeimg="1"> ，**锚点**包含  <img src="https://www.zhihu.com/equation?tex=Mo = 64" alt="Mo = 64" class="ee_img tr_noresize" eeimg="1">  个**典型的  <img src="https://www.zhihu.com/equation?tex=x, y" alt="x, y" class="ee_img tr_noresize" eeimg="1">  坐标**，它们是在  <img src="https://www.zhihu.com/equation?tex=T = 80" alt="T = 80" class="ee_img tr_noresize" eeimg="1">  时刻从数据中通过  <img src="https://www.zhihu.com/equation?tex=K" alt="K" class="ee_img tr_noresize" eeimg="1"> -means （这个倒玩过，聚类算法）算法提取的。

**智能体特征**，形状为 <img src="https://www.zhihu.com/equation?tex=[A, 1, 256]" alt="[A, 1, 256]" class="ee_img tr_noresize" eeimg="1"> ，二者结合形成维度为 ** <img src="https://www.zhihu.com/equation?tex=[A, M_o, 256]" alt="[A, M_o, 256]" class="ee_img tr_noresize" eeimg="1"> ** 的查询张量

将  <img src="https://www.zhihu.com/equation?tex=M_o" alt="M_o" class="ee_img tr_noresize" eeimg="1">  个目标模式的特征与  <img src="https://www.zhihu.com/equation?tex=A" alt="A" class="ee_img tr_noresize" eeimg="1">  个智能体的基础特征结合起来。

#### K，V

由编码后的场景输入提供。

### 推理

四层交叉注意力Transformer层

添加一个 MLP 解码头来解码所有智能体可能采取的行动序列，产生张量 [A, Mo, Tf , 2]，再使用前向动力学模型 转化为 <img src="https://www.zhihu.com/equation?tex=[A, Mo, Tf , 4]" alt="[A, Mo, Tf , 4]" class="ee_img tr_noresize" eeimg="1"> (x, y, ψ, v)。

另一个 MLP 层解码 Transformer 层之后的嵌入，以得出这些预测轨迹的边缘分数（概率），形状[A, Mo]。

>  突然感觉去噪器和行为预测器好像，他们二者的关系是相协同的
>
>  **预测器**提供一组**目标**（ <img src="https://www.zhihu.com/equation?tex=M_o" alt="M_o" class="ee_img tr_noresize" eeimg="1">  个边际模式）。
>
>  **去噪器**生成一个**联合规划**。
>
>  通过一个**成本函数  <img src="https://www.zhihu.com/equation?tex=\mathcal{J}" alt="\mathcal{J}" class="ee_img tr_noresize" eeimg="1"> **，去噪器的输出（联合规划）被鼓励**靠近**预测器给出的高概率目标模式。
>
>  ![image-20251125081915661](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251125081915661.png)

## 训练

### 总损失函数

![image-20251125083438091](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251125083438091.png)

去噪损失  <img src="https://www.zhihu.com/equation?tex=\mathcal{L}_{\mathcal{D}_{\theta}}" alt="\mathcal{L}_{\mathcal{D}_{\theta}}" class="ee_img tr_noresize" eeimg="1">  和预测器损失  <img src="https://www.zhihu.com/equation?tex=\mathcal{L}_{\mathcal{P}_{\psi}}" alt="\mathcal{L}_{\mathcal{P}_{\psi}}" class="ee_img tr_noresize" eeimg="1">  

### 去噪器训练

![image-20251125083520085](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251125083520085.png)

**获取真值动作：** 从地面真值状态  <img src="https://www.zhihu.com/equation?tex=x" alt="x" class="ee_img tr_noresize" eeimg="1">  中，使用**逆动力学函数  <img src="https://www.zhihu.com/equation?tex=f^{-1}" alt="f^{-1}" class="ee_img tr_noresize" eeimg="1"> ** 提取动作轨迹  <img src="https://www.zhihu.com/equation?tex=u" alt="u" class="ee_img tr_noresize" eeimg="1"> 。

**添加噪声：** 根据扩散调度，将噪声  <img src="https://www.zhihu.com/equation?tex=\epsilon" alt="\epsilon" class="ee_img tr_noresize" eeimg="1">  添加到真值动作  <img src="https://www.zhihu.com/equation?tex=u" alt="u" class="ee_img tr_noresize" eeimg="1">  中，得到带噪声动作  <img src="https://www.zhihu.com/equation?tex=\tilde{u}_k" alt="\tilde{u}_k" class="ee_img tr_noresize" eeimg="1"> 。

**去噪预测：** 去噪器  <img src="https://www.zhihu.com/equation?tex=\mathcal{D}_{\theta}" alt="\mathcal{D}_{\theta}" class="ee_img tr_noresize" eeimg="1">  预测去噪后的动作  <img src="https://www.zhihu.com/equation?tex=\hat{u}" alt="\hat{u}" class="ee_img tr_noresize" eeimg="1"> 。

**状态滚展：** 使用**前向动力学函数  <img src="https://www.zhihu.com/equation?tex=f" alt="f" class="ee_img tr_noresize" eeimg="1"> ** 将  <img src="https://www.zhihu.com/equation?tex=\hat{u}" alt="\hat{u}" class="ee_img tr_noresize" eeimg="1">  转换为预测状态  <img src="https://www.zhihu.com/equation?tex=\hat{x}" alt="\hat{x}" class="ee_img tr_noresize" eeimg="1"> 。

**计算损失并更新：** 计算  <img src="https://www.zhihu.com/equation?tex=\mathcal{L}_{\mathcal{D}_{\theta}}=\mathcal{SL}_{1}(\hat{x}-x)" alt="\mathcal{L}_{\mathcal{D}_{\theta}}=\mathcal{SL}_{1}(\hat{x}-x)" class="ee_img tr_noresize" eeimg="1">  并更新去噪器参数。

![image-20251125083622648](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251125083622648.png)

### 行为预测器

![image-20251125083812668](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251125083812668.png)

#### 轨迹匹配损失


<img src="https://www.zhihu.com/equation?tex=\mathcal{SL}_{1}(\hat{x}(\hat{u}^{a,m^{*}})-x^{a})" alt="\mathcal{SL}_{1}(\hat{x}(\hat{u}^{a,m^{*}})-x^{a})" class="ee_img tr_noresize" eeimg="1">

惩罚预测轨迹与真实轨迹之间的**距离误差**

** <img src="https://www.zhihu.com/equation?tex=x^a" alt="x^a" class="ee_img tr_noresize" eeimg="1"> ：** 是智能体  <img src="https://www.zhihu.com/equation?tex=a" alt="a" class="ee_img tr_noresize" eeimg="1">  在未来时间步的**地面真值状态轨迹**（即真实发生的轨迹）。

** <img src="https://www.zhihu.com/equation?tex=\hat{x}(\hat{u}^{a,m})" alt="\hat{x}(\hat{u}^{a,m})" class="ee_img tr_noresize" eeimg="1"> ：** 是模型预测的  <img src="https://www.zhihu.com/equation?tex=M_o" alt="M_o" class="ee_img tr_noresize" eeimg="1">  条轨迹中**与真实轨迹最接近的那一条**（称为  <img src="https://www.zhihu.com/equation?tex=m^*" alt="m^*" class="ee_img tr_noresize" eeimg="1">  模式）所对应的状态轨迹。

#### 分类概率损失


<img src="https://www.zhihu.com/equation?tex=\beta CE(m^{*},\hat{\omega}^{a})" alt="\beta CE(m^{*},\hat{\omega}^{a})" class="ee_img tr_noresize" eeimg="1">

确保模型为“最佳模式”  <img src="https://www.zhihu.com/equation?tex=m^*" alt="m^*" class="ee_img tr_noresize" eeimg="1">  分配最高的概率。

#### m*的选择

![image-20251125083903039](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251125083903039.png)

**如果终点有效** 选择**最接近**地面真值终点  <img src="https://www.zhihu.com/equation?tex=x_T" alt="x_T" class="ee_img tr_noresize" eeimg="1">  的**静态锚点**  <img src="https://www.zhihu.com/equation?tex=ac^i" alt="ac^i" class="ee_img tr_noresize" eeimg="1">  对应的模式。

**如果终点无效 ** 选择**平均位移误差**最小的预测轨迹模式。

## 实现细节

 1 Hz 的频率进行重新规划

模型控制场景中自动驾驶汽车附近的64个智能体，而其余智能体则遵循恒定速度策略。

仿真时域为8秒，需要8个重新规划步骤来生成一个场景。

从相同的初始状态生成总共32个场景。

![image-20251125082948241](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/自动驾驶仿真扩散模型-VBD/image-20251125082948241.png)