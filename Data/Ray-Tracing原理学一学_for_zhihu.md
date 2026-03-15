---
title: 光线追踪的通俗原理
date: 2025-12-10 10:00:05
categories: 计算机
tags:
  - 图形学
  - 光线追踪
  - UE5
cover: /img/cover_29.jpg
highlight_shrink: true
abbrlink: 3513323678
description: 来学学了解一下光线追踪
---

>玩UE5时知道有lumen这样的光线追踪算法，一本讲物理渲染的经典，后面有兴趣可以整来看看

![image-20251210102623950](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/image-20251210102623950_1.png)

openGL学习：[主页 - LearnOpenGL CN](https://learnopengl-cn.github.io/)

GAMES101

 Path Tracing：[计算机图形学：15-462/662 2018年秋季](http://15462.courses.cs.cmu.edu/fall2018/)（CMU 15462)

光追三部曲：

[Shirley P. Ray Tracing](https://zhida.zhihu.com/search?content_id=338418991&content_type=Answer&match_order=1&q=Shirley+P.+Ray+Tracing&zhida_source=entity) in One Weekend[J]. 2016.

Shirley P. Ray Tracing The Next Week[J]. 2016.

Shirley P. Ray Tracing The Rest Of Your Life[J]. 2016.

>  突然感觉挺有意思的，或许后面有兴趣可以写个光追渲染引擎

## 基本原理

很简单的纯几何

![在这里插入图片描述](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/4242c7f59eb9e11e7f47791246592fd1_1.gif)

将三维物体的特征点与眼睛连接成一条线，这条线会穿过画布（Canvas）留下一个交点，无数个这样的“连线”与画布的交点，组成了三维物体在二维平面的投影

已经获得了三维物体在二维平面上投影的位置信息；接下来，这些“连线”还会将三维物体上的颜色/亮度信息（亮度归根结底还是要转化为颜色），带回到二维平面上来，形成最终的图像

**可惜的是前向追踪不太可行**

第一，从物体表面反射的光子是随机方向的，真正能击中画板的光子，千万里挑一

第二，就算一个光子幸运的击中了画板，它仅仅是带来了一个像素的一小部分信息，而我们需要足够多的信息才能组成一张完整的图像

第三，如何界定“此时的信息已经够多了，程序可以停下来了”？这又是实践中的一个难题

因此使用**逆向追踪**

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/v2-43dcc8f28882c3e986f93b94fe251a43_1440w_1.jpg)

逆向追踪从相机(人眼)出发的光线，而非从光源出发(因为大部分光线不会进入相机)

**递归光线追踪**

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/v2-2a68908fd4e81f1292473e338d155032_1440w_1.jpg)

光线从相机出发，穿过每个像素，与场景中的物体相交。然后根据交点处的材质属性，生成反射光线、折射光线以及阴影光线。这些次级光线会继续追踪，直到满足终止条件。

>严老师表示：是我最喜欢的递归

### 判断相交

>  基本原理听起来很简单，但真要算光线与表面相交还是要有很多计算的，就比如游戏中经常使用的三角形

<img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/v2-48a177a4c4727b3d49333079a9788a99_1440w_1.jpg" alt="img" style="zoom:50%;" />

<img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/v2-34c02ea56e229b545e1ba98b2be6cd10_1440w_1.jpg" alt="img" style="zoom:25%;" />

简单的平面表达式

<img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/v2-079b2170e646aeb01500a2e393aa052d_1440w_1.jpg" alt="img" style="zoom:25%;" />

<img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/v2-1d765c6b8c2c8875ff51f09dd96c577e_1440w_1.jpg" alt="img" style="zoom:25%;" />

Möller Trumbore Algorithm算法，判断光线是否在平面的三角形里。

游戏里每帧要处理百万条光线以及光线递归反射或折射，一个场景可能包含数百万个几何图元(如三角形网格、曲面)，你都要计算的话，电脑不给你干冒烟了。

所以通常会采取一些简化，比如包围盒，如果光线都不跟包围盒相交，跟物体更加不会相交，我在写UE5游戏中视野碰撞盒的逻辑也是这样的。

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/v2-a5889db21dd408e2d2c269fc248eef82_1440w_1.jpg)

瞄了眼那篇ISSCC

![image-20251214194126412](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/image-20251214194126412_1.png)

他用了两种边界盒：空边界盒仅用于光线传输估计和阴影计算，跳过昂贵的着色计算。目标边界盒内部包含用户定义的需要详细渲染的物体子集。

BBOX Intersection Evaluator 先检测与TBBOX的交点，只有相交的才由 Triangle Mesh Intersection Evaluator 进行精确的三角形求交计算。

## 从UE5学习光线追踪

### 默认模式——lumen

>UE5说：“要有光！”就有了光。

发电ing：Lumen，作为虚幻引擎5中最牛逼的两个系统之一（另一个是Nanite），成功的做到了在游戏中实时计算全局光照这一壮举。

在RTX硬件光追推出之前。很少有游戏可以做到实时的去计算游戏场景中光线多次弹射所产生的全局光照。即使有了以后，很多低端显卡计算能力不强甚至没有。

而lumine实现了**基于软件和硬件加速混合**，大大增加了其跨平台的应用性（做游戏时我的fw 4060毫无鸭梨）

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/b2ee30ea-8997-47fb-896e-d6569137c9cf_1)

#### 核心数据准备

Lumen 不是直接对海量的原始三角形进行光线追踪，而是使用了两种高效的代理表示：

**网格体距离场**：引擎会为场景中的静态物体和重要的动态物体生成一个有符号距离场。他是一个体素化的体积，其中每个体素存储的是到最近物体表面的距离。正值表示在物体外部，负值表示在物体内部，零值就是表面。

这样做使其追踪速度极快。要判断一条光线是否击中表面，只需在SDF中“步进”，根据距离值安全地跳过空区域，效率远高于与数百万三角形逐一求交。这使得软件光线追踪成为可能。

**表面缓存**：为了获得击中点的材质颜色（反照率），Lumen 将场景中可见表面的材质信息（反照率、法线、粗糙度等）烘焙到几张低分辨率的纹理图集中，称为表面缓存。光线击中SDF后，通过索引即可快速获取材质数据，无需访问复杂的原始材质节点树。

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Ray-Tracing原理学一学/4a82f55f-1bb0-44e5-8e0b-2c57e9c8b0da_1)

#### 光线追踪阶段（两种模式）

Lumen 采用两种光线追踪后端，动态选择：

**软件光线追踪**：这是 Lumen 的默认和核心模式。它完全在GPU的通用计算着色器中运行，不依赖于特定的硬件RT核心。它主要追踪两种光线：

屏幕空间追踪：优先在当前的屏幕深度缓冲中寻找命中点，速度最快，但只能看到屏幕内的信息。

网格体距离场追踪：当光线射出屏幕外或需要追踪背面时，使用上面提到的SDF进行追踪。这提供了屏幕外的全局信息。

**硬件光线追踪**：当用户的GPU支持硬件光线追踪（DXR/Vulkan RT）且启用时，Lumen可以将其作为更高质量的后端。HWRT直接对三角形进行追踪，精度远高于SDF，尤其擅长处理非常精细的几何体（如铁丝网、树叶）和准确的细节反射。但它比软件模式更耗性能。

#### 全局光照求解与缓存

Lumen 不会为每一帧的每一个像素都重新追踪大量光线，那样开销无法承受。它采用了一个智能缓存与传播系统：

**辐照度探测网格**：在场景中布置一个三维的网格点阵。每个网格点会向多个方向发射有限数量的光线（通过SDF或HWRT），来探测周围的间接光照信息，并将结果（颜色、方向）存储在该点上。

**辐射度缓存**：这是一种更高级的缓存，直接附着在物体表面上，能提供比体积网格更高分辨率的间接光照。

**帧间传播与空间插值**：光照结果是渐进式更新和传播的。每一帧只更新一部分探针，并利用历史帧数据和相邻探针的数据进行插值、去噪，最终形成平滑、稳定的全局光照效果。这就是为什么移动光源时，间接光会“流淌”开来，而不是瞬间全变。

>还有更细节一点的东西，像是反射，折射，辐射场，后面再看看吧，这次就简单了解一下这个领域。