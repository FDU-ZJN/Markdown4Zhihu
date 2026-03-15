---
title: 统一高效因子图加速器设计
date: 2025-11-16 22:39:41
categories: 具身智能
tags:
  - 体系结构
  - 论文
cover: /img/cover_17.jpg
highlight_shrink: true
abbrlink: 1253343412
description: 针对机器人优化的统一高效因子图加速器设计
---

![image-20251116224113124](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251116224113124.png)



## 问题和解决

#### 问题

定位问题稀疏矩阵，用处理器浪费计算资源。

通常使用加速器堆叠算法，芯片面积很大。

### 先前工作

#### 1. 定位

**P-BA ：** 针对 ORB-based SLAM 系统，将计算密集型的**Bundle Adjustment (BA)** 任务的核心部分（Jacobian 计算和 Schur 消元）放在 FPGA 上加速，其余在软件中实现。

**BAX ：** 完整的 BA 硬件加速器，使用**通用向量单元**，但它只针对 BA 这一特定子任务。

#### 2. 规划

**BLITZCRANK：** 利用**因子图 抽象来减少优化问题的规模。通过优化因子图的**推理顺序**，它相比 CPU 软件实现，实现了 **7.4 倍**加速和 **29.7 倍**能耗降低。

#### 3. 控制

**Lin et al. ：** 开发了一种基于采样的运动控制加速器，旨在最大化**控制率**和**轨迹时间步数量**，相比现有技术 [38] 实现了 **22 倍**和 **26 倍**的提升。

> 后面都可以看看

#### 解决

提出新型位姿表示法，结合因子图抽象，为定位、规划与控制算法构建了统一的因子计算模型

针对系数矩阵**J**提出高效稀疏数据压缩格式，有效减少索引信息存储量，并优化矩阵访问与更新效率

设计高速高能效因子图加速器，支持因子图计算模型与稀疏格式。

## 前置知识

![在这里插入图片描述](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/20200720210941626.png)

![image-20251116230925728](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251116230925728.png)

因子图计算

>  线性代数快忘完了，QR分解是将将矩阵分解为一个正交矩阵Q和一个上三角矩阵R的乘积

##  姿态表示方法

### 不同的姿态表示方法

| **算法** | **表示方法**                                        | **核心操作**                         |

| -------- | --------------------------------------------------- | ------------------------------------ |

| 运动规划 | 特殊欧几里得群  <img src="https://www.zhihu.com/equation?tex=SE(3)" alt="SE(3)" class="ee_img tr_noresize" eeimg="1">  和 李代数  <img src="https://www.zhihu.com/equation?tex=\mathfrak{se}(3)" alt="\mathfrak{se}(3)" class="ee_img tr_noresize" eeimg="1">  | 旋转通过**乘法运算**实现（群乘法）。 |

| 定位     | **四元数  <img src="https://www.zhihu.com/equation?tex=q" alt="q" class="ee_img tr_noresize" eeimg="1">  和 位置向量  <img src="https://www.zhihu.com/equation?tex=T(3)" alt="T(3)" class="ee_img tr_noresize" eeimg="1"> **                   | 旋转通过**加法运算**实现。           |


> 数学，已畏惧，下面是查了下的快乐数学补课部分

####  <img src="https://www.zhihu.com/equation?tex=SE(3)" alt="SE(3)" class="ee_img tr_noresize" eeimg="1"> 

在三维空间中，一个点的姿态有**六个自由度**，包括三个平移自由度（位置）和三个旋转自由度（方向）。

- **表示方式：** 姿态变换可以用一个  <img src="https://www.zhihu.com/equation?tex=4 \times 4" alt="4 \times 4" class="ee_img tr_noresize" eeimg="1">  的**齐次坐标变换矩阵**  <img src="https://www.zhihu.com/equation?tex=\mathbf{T}" alt="\mathbf{T}" class="ee_img tr_noresize" eeimg="1">  来描述，该矩阵属于特殊欧几里得群  <img src="https://www.zhihu.com/equation?tex=SE(3)" alt="SE(3)" class="ee_img tr_noresize" eeimg="1"> 。
- **矩阵结构：**  <img src="https://www.zhihu.com/equation?tex=\mathbf{T}" alt="\mathbf{T}" class="ee_img tr_noresize" eeimg="1">  矩阵由两部分组成：
  1. **方向 (Orientation)：** 一个  <img src="https://www.zhihu.com/equation?tex=3 \times 3" alt="3 \times 3" class="ee_img tr_noresize" eeimg="1">  的**旋转矩阵  <img src="https://www.zhihu.com/equation?tex=\mathbf{R}" alt="\mathbf{R}" class="ee_img tr_noresize" eeimg="1"> **，属于特殊正交群  <img src="https://www.zhihu.com/equation?tex=SO(3)" alt="SO(3)" class="ee_img tr_noresize" eeimg="1">  ( <img src="https://www.zhihu.com/equation?tex=\mathbf{R} \in SO(3) \in \mathbb{R}^{3 \times 3}" alt="\mathbf{R} \in SO(3) \in \mathbb{R}^{3 \times 3}" class="ee_img tr_noresize" eeimg="1"> )。
  2. **位置 (Position)：** 一个  <img src="https://www.zhihu.com/equation?tex=3 \times 1" alt="3 \times 1" class="ee_img tr_noresize" eeimg="1">  的**平移向量  <img src="https://www.zhihu.com/equation?tex=\mathbf{t}" alt="\mathbf{t}" class="ee_img tr_noresize" eeimg="1"> ** ( <img src="https://www.zhihu.com/equation?tex=\mathbf{t} \in T(3) \in \mathbb{R}^{3}" alt="\mathbf{t} \in T(3) \in \mathbb{R}^{3}" class="ee_img tr_noresize" eeimg="1"> )。


<img src="https://www.zhihu.com/equation?tex=\mathbf{T} = \begin{pmatrix} \mathbf{R} & \mathbf{t} \\ \mathbf{0}^T & 1 \end{pmatrix}" alt="\mathbf{T} = \begin{pmatrix} \mathbf{R} & \mathbf{t} \\ \mathbf{0}^T & 1 \end{pmatrix}" class="ee_img tr_noresize" eeimg="1">

### 冗余性

**旋转矩阵  <img src="https://www.zhihu.com/equation?tex=\mathbf{R}" alt="\mathbf{R}" class="ee_img tr_noresize" eeimg="1">  的冗余：** 旋转本身只有 3 个自由度，但却使用一个包含 **9 个变量**的  <img src="https://www.zhihu.com/equation?tex=\mathbf{R}" alt="\mathbf{R}" class="ee_img tr_noresize" eeimg="1">  矩阵来表示。（原因：这 9 个变量之间存在 6 个**约束条件**（正交性  <img src="https://www.zhihu.com/equation?tex=\mathbf{R}^T \mathbf{R} = \mathbf{I}" alt="\mathbf{R}^T \mathbf{R} = \mathbf{I}" class="ee_img tr_noresize" eeimg="1">  和行列式  <img src="https://www.zhihu.com/equation?tex=\text{det}(\mathbf{R})=1" alt="\text{det}(\mathbf{R})=1" class="ee_img tr_noresize" eeimg="1"> ）。

**变换矩阵  <img src="https://www.zhihu.com/equation?tex=\mathbf{T}" alt="\mathbf{T}" class="ee_img tr_noresize" eeimg="1">  的冗余：** 完整的姿态只有 6 个自由度，却使用一个  <img src="https://www.zhihu.com/equation?tex=4 \times 4" alt="4 \times 4" class="ee_img tr_noresize" eeimg="1">  矩阵，即 **16 个变量**来表示。（原因：除了旋转矩阵本身的 6 个约束外，底部一行（ <img src="https://www.zhihu.com/equation?tex=\mathbf{0}^T" alt="\mathbf{0}^T" class="ee_img tr_noresize" eeimg="1">  和 1）是固定的。）

###  <img src="https://www.zhihu.com/equation?tex=\mathfrak{se}(3)" alt="\mathfrak{se}(3)" class="ee_img tr_noresize" eeimg="1">  

李代数  <img src="https://www.zhihu.com/equation?tex=\mathfrak{se}(3)" alt="\mathfrak{se}(3)" class="ee_img tr_noresize" eeimg="1">  的元素由一个**六维向量  <img src="https://www.zhihu.com/equation?tex=\boldsymbol{\xi}" alt="\boldsymbol{\xi}" class="ee_img tr_noresize" eeimg="1"> ** 确定，这个向量精确地包含了姿态的所有 6 个独立自由度。


<img src="https://www.zhihu.com/equation?tex=\boldsymbol{\xi} = \begin{pmatrix} \boldsymbol{\rho} \\ \boldsymbol{\phi} \end{pmatrix} \in \mathbb{R}^6" alt="\boldsymbol{\xi} = \begin{pmatrix} \boldsymbol{\rho} \\ \boldsymbol{\phi} \end{pmatrix} \in \mathbb{R}^6" class="ee_img tr_noresize" eeimg="1">

其中  <img src="https://www.zhihu.com/equation?tex=\boldsymbol{\rho} \in \mathbb{R}^3" alt="\boldsymbol{\rho} \in \mathbb{R}^3" class="ee_img tr_noresize" eeimg="1">  表示平移分量， <img src="https://www.zhihu.com/equation?tex=\boldsymbol{\phi} \in \mathbb{R}^3" alt="\boldsymbol{\phi} \in \mathbb{R}^3" class="ee_img tr_noresize" eeimg="1">  表示旋转轴角分量。

这个六维向量  <img src="https://www.zhihu.com/equation?tex=\boldsymbol{\xi}" alt="\boldsymbol{\xi}" class="ee_img tr_noresize" eeimg="1">  被映射为一个  <img src="https://www.zhihu.com/equation?tex=4 \times 4" alt="4 \times 4" class="ee_img tr_noresize" eeimg="1">  的**反对称矩阵  <img src="https://www.zhihu.com/equation?tex=\mathbf{\Phi}" alt="\mathbf{\Phi}" class="ee_img tr_noresize" eeimg="1"> **，即李代数  <img src="https://www.zhihu.com/equation?tex=\mathfrak{se}(3)" alt="\mathfrak{se}(3)" class="ee_img tr_noresize" eeimg="1">  的元素：


<img src="https://www.zhihu.com/equation?tex=\mathbf{\Phi} = \boldsymbol{\xi}^{\wedge} = \begin{pmatrix} \boldsymbol{\phi}^{\wedge} & \boldsymbol{\rho} \\ \mathbf{0}^T & 0 \end{pmatrix} \in \mathfrak{se}(3) \subset \mathbb{R}^{4 \times 4}" alt="\mathbf{\Phi} = \boldsymbol{\xi}^{\wedge} = \begin{pmatrix} \boldsymbol{\phi}^{\wedge} & \boldsymbol{\rho} \\ \mathbf{0}^T & 0 \end{pmatrix} \in \mathfrak{se}(3) \subset \mathbb{R}^{4 \times 4}" class="ee_img tr_noresize" eeimg="1">

其中  <img src="https://www.zhihu.com/equation?tex=\boldsymbol{\phi}^{\wedge} \in \mathbb{R}^{3 \times 3}" alt="\boldsymbol{\phi}^{\wedge} \in \mathbb{R}^{3 \times 3}" class="ee_img tr_noresize" eeimg="1">  是由  <img src="https://www.zhihu.com/equation?tex=\boldsymbol{\phi}" alt="\boldsymbol{\phi}" class="ee_img tr_noresize" eeimg="1">  向量构造的**反对称矩阵**。

需要涉及复杂扰动导数模型的变换：


<img src="https://www.zhihu.com/equation?tex=\mathbf{T} = \exp(\mathbf{\Phi}) = \exp(\boldsymbol{\xi}^{\wedge})" alt="\mathbf{T} = \exp(\mathbf{\Phi}) = \exp(\boldsymbol{\xi}^{\wedge})" class="ee_img tr_noresize" eeimg="1">


<img src="https://www.zhihu.com/equation?tex=\frac{\partial f}{\partial \boldsymbol{\xi}} = \frac{\partial f}{\partial \mathbf{T}} \cdot \frac{\partial \mathbf{T}}{\partial \boldsymbol{\xi}}" alt="\frac{\partial f}{\partial \boldsymbol{\xi}} = \frac{\partial f}{\partial \mathbf{T}} \cdot \frac{\partial \mathbf{T}}{\partial \boldsymbol{\xi}}" class="ee_img tr_noresize" eeimg="1">

 <img src="https://www.zhihu.com/equation?tex=\frac{\partial \mathbf{T}}{\partial \boldsymbol{\xi}}" alt="\frac{\partial \mathbf{T}}{\partial \boldsymbol{\xi}}" class="ee_img tr_noresize" eeimg="1">  中 <img src="https://www.zhihu.com/equation?tex=\mathbf{T}" alt="\mathbf{T}" class="ee_img tr_noresize" eeimg="1">  是  <img src="https://www.zhihu.com/equation?tex=\boldsymbol{\xi}" alt="\boldsymbol{\xi}" class="ee_img tr_noresize" eeimg="1">  的非线性指数函数。

![image-20251117225312278](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251117225312278.png)

###  新姿态表示  <img src="https://www.zhihu.com/equation?tex=< \mathfrak{so}(n), T(n) >" alt="< \mathfrak{so}(n), T(n) >" class="ee_img tr_noresize" eeimg="1"> 



**姿态结构：** 姿态  <img src="https://www.zhihu.com/equation?tex=\boldsymbol{\xi}" alt="\boldsymbol{\xi}" class="ee_img tr_noresize" eeimg="1">  被表示为一个二元组  <img src="https://www.zhihu.com/equation?tex=< \boldsymbol{\phi}, \mathbf{t} >" alt="< \boldsymbol{\phi}, \mathbf{t} >" class="ee_img tr_noresize" eeimg="1"> 。

**旋转部分 ( <img src="https://www.zhihu.com/equation?tex=\boldsymbol{\phi}" alt="\boldsymbol{\phi}" class="ee_img tr_noresize" eeimg="1"> ):** 使用李代数  <img src="https://www.zhihu.com/equation?tex=\mathfrak{so}(n)" alt="\mathfrak{so}(n)" class="ee_img tr_noresize" eeimg="1">  的元素，即 **旋转向量  <img src="https://www.zhihu.com/equation?tex=\boldsymbol{\phi}" alt="\boldsymbol{\phi}" class="ee_img tr_noresize" eeimg="1"> **。它通过  <img src="https://www.zhihu.com/equation?tex=\mathbf{R}_i = \text{Exp}(\boldsymbol{\phi}_i)" alt="\mathbf{R}_i = \text{Exp}(\boldsymbol{\phi}_i)" class="ee_img tr_noresize" eeimg="1">  映射到旋转矩阵  <img src="https://www.zhihu.com/equation?tex=\mathbf{R}_i" alt="\mathbf{R}_i" class="ee_img tr_noresize" eeimg="1"> 。

**平移部分 ( <img src="https://www.zhihu.com/equation?tex=\mathbf{t}" alt="\mathbf{t}" class="ee_img tr_noresize" eeimg="1"> ):** 使用一个简单的 **平移向量  <img src="https://www.zhihu.com/equation?tex=\mathbf{t}" alt="\mathbf{t}" class="ee_img tr_noresize" eeimg="1"> **。

广义运算：

![image-20251117225337979](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251117225337979.png)

## 计算模型

![image-20251117225404624](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251117225404624.png)

### Lidar因子误差


<img src="https://www.zhihu.com/equation?tex=\mathbf{e} (\boldsymbol{\xi}_i, \boldsymbol{\xi}_j) = (\boldsymbol{\xi}_i \ominus \boldsymbol{\xi}_j) \ominus \Delta \boldsymbol{\xi}_{\text{obs}} \tag{3}" alt="\mathbf{e} (\boldsymbol{\xi}_i, \boldsymbol{\xi}_j) = (\boldsymbol{\xi}_i \ominus \boldsymbol{\xi}_j) \ominus \Delta \boldsymbol{\xi}_{\text{obs}} \tag{3}" class="ee_img tr_noresize" eeimg="1">

到


<img src="https://www.zhihu.com/equation?tex=\mathbf{e} (\boldsymbol{\xi}_i, \boldsymbol{\xi}_j) = < \text{Log}(\Delta \mathbf{R}_{\text{obs}}^T \mathbf{R}_j^T \mathbf{R}_i), \Delta \mathbf{R}_{\text{obs}}^T (\mathbf{R}_j^T (\mathbf{t}_i - \mathbf{t}_j) - \Delta \mathbf{t}_{\text{obs}}) > \tag{4}" alt="\mathbf{e} (\boldsymbol{\xi}_i, \boldsymbol{\xi}_j) = < \text{Log}(\Delta \mathbf{R}_{\text{obs}}^T \mathbf{R}_j^T \mathbf{R}_i), \Delta \mathbf{R}_{\text{obs}}^T (\mathbf{R}_j^T (\mathbf{t}_i - \mathbf{t}_j) - \Delta \mathbf{t}_{\text{obs}}) > \tag{4}" class="ee_img tr_noresize" eeimg="1">

![image-20251117225524202](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251117225524202.png)

> 被数学轰炸了，还是有点一知半解，但这样看的话确实避免了冗余和太复杂的计算

## 稀疏矩阵存储

### 稀疏矩阵压缩格式

线性二次调节器 (LQR)：

![image-20251117225536496](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251117225536496.png)

稀疏，分块，连续

| **特征**               | **传统的 CSR 格式 **                        | **基于连续性优化的新格式**                         |

| ---------------------- | ------------------------------------------- | -------------------------------------------------- |

| **非零块数据 (`VAL`)** | **大小： <img src="https://www.zhihu.com/equation?tex=NZ" alt="NZ" class="ee_img tr_noresize" eeimg="1">  块** (存储所有非零块)          | **大小： <img src="https://www.zhihu.com/equation?tex=NZ" alt="NZ" class="ee_img tr_noresize" eeimg="1">  块** (存储所有非零块)                 |

| **列索引 (`COL_IND`)** | **大小： <img src="https://www.zhihu.com/equation?tex=NZ" alt="NZ" class="ee_img tr_noresize" eeimg="1"> ** (存储**每个**非零块的列索引) | **大小： <img src="https://www.zhihu.com/equation?tex=M" alt="M" class="ee_img tr_noresize" eeimg="1"> ** (只存储**每行第一个**非零块的列索引) |

| **行信息数组**         | `ROW_PTR` (大小： <img src="https://www.zhihu.com/equation?tex=M+1" alt="M+1" class="ee_img tr_noresize" eeimg="1"> )，记录每行起始位置   | `NUM_NZ` (大小： <img src="https://www.zhihu.com/equation?tex=M" alt="M" class="ee_img tr_noresize" eeimg="1"> )，记录每行非零块数量/跨度      |


### 消元更新

![image-20251117225509960](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251117225509960.png)

使用了一种**滑动窗口**方法，只比较 `COL_IND` 数组中窗口内的元素与  <img src="https://www.zhihu.com/equation?tex=x_i" alt="x_i" class="ee_img tr_noresize" eeimg="1">  的列索引。窗口大小被确定为  <img src="https://www.zhihu.com/equation?tex=\lceil M/2 \rceil" alt="\lceil M/2 \rceil" class="ee_img tr_noresize" eeimg="1"> （在定位、规划和控制算法中的变量消除过程中，每个变量节点连接的因子节点数量最多为  <img src="https://www.zhihu.com/equation?tex=\lceil M/2 \rceil" alt="\lceil M/2 \rceil" class="ee_img tr_noresize" eeimg="1"> ）

> 上三角矩阵可以用回代法快速求解矩阵（线代老师要跳起来打我了）

## 硬件结构

![image-20251117230107721](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251117230107721.png)

### 因子计算单元

![image-20251117230703774](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251117230703774.png)

MO-DFG 中的每个**节点**（一个基本矩阵操作）都会被直接映射到硬件上的**一个基本计算单元**。被分配到特定的时钟周期 执行。

>  这种硬件的论文能看到比较细节底层的计算，不像纯软的论文直接摆个模型完事，可能这就是硬件的魅力吧

## 因子图推理单元

用来解线性方程组

### 消元模块

部分QR分解

![image-20251118081454073](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251118081454073.png)

电路图

![image-20251118085540019](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251118085540019.png)

u开根得到v没有对上，推测应当是转化为：


<img src="https://www.zhihu.com/equation?tex=\bar{H} = \bar{I} - 2\frac{\bar{u}\bar{u}^T}{\bar{u}^T\bar{u}}" alt="\bar{H} = \bar{I} - 2\frac{\bar{u}\bar{u}^T}{\bar{u}^T\bar{u}}" class="ee_img tr_noresize" eeimg="1">

这样就省了一个开根器

猜的是a输入的是再构造两个u，乘一下得到$ <img src="https://www.zhihu.com/equation?tex={\bar{u}\bar{u}^T}" alt="{\bar{u}\bar{u}^T}" class="ee_img tr_noresize" eeimg="1"> $，为什么不复用u

### 回代计算

![image-20251118091301346](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251118091301346.png)

从上到下一层层向下算，求解到上一层的根，经过PE更新解向量下一层的值

>  大脑在颤抖

## 流水线

因子计算和变量消除可以流水线化，当因子计算模块计算下一批数据时，变量消除模块可以同时处理上一批数据。

变量消除（QR 分解）是**从左上到右下**（沿对角线正向）进行的。回代是**从右下到左上**（沿对角线逆向）进行的。由于严格的数据依赖性和相反的计算方向，变量消除和回代**不能进行流水线**处理。

每次回代单元**更新一个位姿向量**时，因子计算单元就可以立即开始**下一轮的求解迭代**。

![image-20251118102357512](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251118102357512.png)

## 评估

![image-20251118103158856](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251118103158856.png)

![image-20251118103039774](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251118103039774.png)

![image-20251118103055095](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251118103055095.png)

![image-20251118103113655](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/Factor-Graph-Accelerator/image-20251118103113655.png)