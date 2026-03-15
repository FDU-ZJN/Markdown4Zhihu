---
title: MICRO2025论文阅读
date: 2025-10-22 08:04:13
categories: IC
tags:
  - MICRO
  - 体系结构
  - 论文
cover: /img/cover_16.jpg
highlight_shrink: true
abbrlink: 1253395412
description: MICRO 2025 Systems for Al (Training) 部分的论文阅读，论文内容集中在分布式训练有关的通信
---

### 分布式训练策略

| 维度                 | 数据并行 (DP)                                                | 流水线并行 (PP)                                              | 张量并行 (TP)                                                |

| :------------------- | :----------------------------------------------------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |

| **并行核心思想**     | **数据维度**：将训练数据分批，在不同的设备上使用**相同的模型副本**进行处理。 | **模型维度（层间）**：将模型按**层**拆分成多个阶段，每个设备负责模型的一个连续部分。 | **模型维度（层内）**：将单个**层内的运算和参数**进行拆分，分布到多个设备上。 |

| **如何划分**         | 划分**训练数据集**。                                         | 划分**模型的层**。                                           | 划分**层的权重矩阵/计算**。                                  |

| **设备上的模型状态** | 每个设备拥有**完整模型**的一个副本。                         | 每个设备只拥有**模型的一部分**（一组连续的层）。             | 每个设备拥有**一层或几层的部分参数**。                       |

| **通信内容**         | **梯度**（反向传播后）                                       | **激活值**（前向传播时） **梯度**（反向传播时）              | **部分激活值/计算结果**（前向和反向传播过程中）              |

| **通信时机**         | 每次迭代的**反向传播结束后**。                               | 在前向和反向传播过程中，**阶段与阶段之间**。                 | 在**单个层的前向和反向计算过程中**。                         |

| **主要优势**         | - 实现简单，应用广泛。 - 对于模型较小、数据量大的情况非常有效。 | - 可以训练**模型过大，无法放入单个设备显存**的模型。 - 通信量相对可控。 | - 能极细粒度地降低**单个巨大层**的内存占用（如大模型中的FFN、Attention层）。 |

| **主要挑战/代价**    | - 每个设备仍需容纳**整个模型**，对于大模型不适用。 - 全局同步梯度会产生通信瓶颈，尤其是设备数量多时。 | - 存在**流水线气泡**，造成设备空闲，降低计算效率。 - 需要仔细进行模型切分以平衡各阶段负载 | \- **通信非常频繁**（每层都可能需要通信），对设备间互联带宽要求极高。 |


>  [(33 封私信 / 80 条消息) 一文深度全面解析大模型分布式并行策略：DP/TP/PP/CP/EP/SP - 知乎](https://zhuanlan.zhihu.com/p/1937826285264011929)
>
>  一个讲训练模式的文章，觉得讲的不错。
>
>  | 并行策略       | 缩写                          | 核心通信                        | 通信发生时机与目的                                      |

>  | :------------- | :---------------------------- | :------------------------------ | :------------------------------------------------------ |

>  | **数据并行**   | Data Parallelism (**DP**)     | **All-Reduce**                  | 反向传播结束后，同步所有设备间的梯度。                  |

>  | **流水线并行** | Pipeline Parallelism (**PP**) | **点对点通信** (Peer-to-Peer)   | 在流水线相邻阶段之间传递激活值（前向）和梯度（反向）。  |

>  | **张量并行**   | Tensor Parallelism (**TP**)   | **All-to-All**                  | 在前向/反向传播的**计算过程中**，交换和重组中间激活值。 |

>  | **序列并行**   | Sequence Parallelism (**SP**) | **All-to-All** / **All-Gather** | 在处理序列维度时，重组与序列维度相关的激活值。          |

>  | **专家并行**   | Expert Parallelism (**EP**)   | **All-to-All**                  | 在混合专家模型中，将数据路由到不同设备上                |


# NetZlP

![image-20251022081259452](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251022081259452.png)

>  在分布式大模型训练中实现**网络内无损压缩**梯度和激活,实现了压缩算法和硬件加速器

顶级超大规模集群将其每个计算节点连接到多个400 Gbps网络链路[13, 49]。然而，公共云中经济实惠的集群仍然依赖于中低带宽的网络链路。范围从低至10 Gbps到常见的50 Gbps。

并非所有人都能轻易负担得起访问网络带宽超过100 Gbps的高端实例。当网络带宽降低到50 Gbps时，Llama-3 70B、GPT-3 175B和Llama-3 405B的每次训练迭代的通信时间分别增加2.2×、2.0×和1.7×。

## 压缩算法

在分布式大模型训练中，梯度和激活通常采用 **bfloat16** 格式存储（16位浮点数）。标准无损压缩算法（如 LZ4 和 Snappy）主要依赖于**字典匹配**，通过滑动窗口查找重复的字符（8位字节序列）来压缩数据 。

 bfloat16 数据的 **低 8 位** 接近随机分布（1的概率约为 50%），这使得标准压缩算法很难找到重复的字节序列 。实验显示，LZ4 和 Snappy 几乎无法压缩 bfloat16 格式的梯度和激活（压缩比接近 100%）。

| 格式             | 总位数  | 符号位 | 指数位 | 尾数位  |

| :--------------- | :------ | :----- | :----- | :------ |

| **FP32 (float)** | 32 bits | 1 bit  | 8 bits | 23 bits |

| **FP16 (half)**  | 16 bits | 1 bit  | 5 bits | 10 bits |

| **bfloat16**     | 16 bits | 1 bit  | 8 bits | 7 bits  |


### 位级别转换：字节和比特分组

虽然尾数位是随机的，但梯度和激活的 **指数位** 具有较高的“1”的概率（1.07169×10−8 = 0_01100100_0111000) 。

![image-20251027090838491](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251027090838491.png)

**字节分组：** 将所有 bfloat16 数值中的**高字节**（包含符号位和指数位）集中在一起，再将所有**低字节**（包含尾数位）集中在一起 7。

**比特分组：** 将所有 bfloat16 数值中的**第  <img src="https://www.zhihu.com/equation?tex=N" alt="N" class="ee_img tr_noresize" eeimg="1">  个比特**（例如，所有数的第 15 位）集中在一起，依此类推 。

通过分组，可压缩性更高的指数位和符号位被排列到相邻位置，从而帮助 LZ4 等算法更容易识别重复模式，大幅提高字典匹配的效率 。

### 值级别转换：Delta 压缩

梯度和激活的值在训练迭代过程中是**逐渐变化**的 。

从当前迭代的每个梯度或激活值中，减去一个**有代表性的基准值** ：

-  理想情况下，可以减去上一迭代的对应值（称为“真 Delta 压缩”）。
-  在 NIC 内存受限的实际场景中，论文提出为每一层使用一个**单基准值**，例如该层中所有值的**最小值** ( <img src="https://www.zhihu.com/equation?tex=D_{min}" alt="D_{min}" class="ee_img tr_noresize" eeimg="1"> ) 。

进行减法操作后得到的**Delta 值**会更集中于零点附近，这使得原本随机的**尾数位更趋向于 0**，从而使数据整体更具可压缩性 。

实验证明，**Delta 压缩结合比特分组**辅助下的 NETZIP-LZ4，相比标准 LZ4 实现了巨大的提升 ：

梯度的数据量平均减少了 **67%** 。

激活的数据量平均减少了 **70%** 。

## 压缩加速器

提出了NetZIP-accelerator加速器，集成到NIC ASIC中。

NETZIP-accelerator 采用了**线内**的架构 ，意味着它将整个处理模块直接放置在数据流向网络（或从网络接收）的路径上。

**集成位置：** 加速器将 NETZIP-algorithm 的转换功能与一个**LZ4加速器**集成到 NIC（网卡）内部 。

**解决传输开销：** 传统的压缩方式（在 CPU、GPU 或 SNIC 上运行）需要额外的内存传输 。例如，数据在发送前必须经历：发送方 GPU 内存 -> CPU 内存 -> CPU 压缩 -> CPU 内存 -> NIC 的路径 。这些**额外的传输**显著增加了端到端的压缩/解压缩延迟 。

作为“线内”加速器，NETZIP-accelerator **消除了**这些不必要的梯度和激活数据的**额外传输** ，从而直接在数据流经 NIC 时完成转换、压缩和解压缩，大幅减少了总体延迟 。

### 压缩路径

当数据从主机（GPU 内存）通过 NIC 发送到网络时，会经过压缩路径：

**组件顺序：** **Tx (DE)MUX**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  **Delta 编码器**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  **分组暂存缓冲区**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  **分组器**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  **压缩器**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  **Tx MUX/协议引擎**

| **组件**                | **功能**                | **机制/实现细节**                                            |

| ----------------------- | ----------------------- | ------------------------------------------------------------ |

| **Tx (DE)MUX**          | **流量控制/选择性压缩** | 根据自定义标头中的 **1 位压缩标志**，决定数据包的去向： 1. 如果标志未设置（非梯度/激活数据包），直接将数据包转发给协议引擎（不压缩）。 2. 如果标志设置，将数据包导向 Delta 编码器进行压缩。 |

| **Delta 编码器**        | **值级别转换**          | 负责执行  <img src="https://www.zhihu.com/equation?tex=G_{i} - D_{min}" alt="G_{i} - D_{min}" class="ee_img tr_noresize" eeimg="1">  操作，由三个单元组成： 1. **基值计算单元：** 遍历数据包中**同一层 ID**（由 15 位 Layer ID 标识）的 bfloat16 值，找出该层的**最小值  <img src="https://www.zhihu.com/equation?tex=D_{min}" alt="D_{min}" class="ee_img tr_noresize" eeimg="1"> ** 作为基值。 2. **基值寄存器：** 存储每一层的  <img src="https://www.zhihu.com/equation?tex=D_{min}" alt="D_{min}" class="ee_img tr_noresize" eeimg="1">  基值。 3. **增量值计算单元：** 计算每个中间值（梯度或激活）与  <img src="https://www.zhihu.com/equation?tex=D_{min}" alt="D_{min}" class="ee_img tr_noresize" eeimg="1">  的差值，生成 **Delta 值**。计算完成后，将 Delta 值和  <img src="https://www.zhihu.com/equation?tex=D_{min}" alt="D_{min}" class="ee_img tr_noresize" eeimg="1">  一起传出。 |

| **分组暂存缓冲**        | **缓存与双缓冲**        | 采用**双缓冲架构**： 1. 当一个缓冲区在**接收**当前 4 kB 数据包时。 2. 另一个缓冲区则存储**前一个**已完成 Delta 编码的数据包，供分组器使用。此设计确保了数据流的连续性，最小化延迟。 |

| **分组器 (Grouper)**    | **位级别转换**          | 对 Delta 值执行 **字节或比特粒度** 的重排列（即 NETZIP-algorithm 中的**比特/字节分组**），将可压缩的部分聚集在一起。 |

| **压缩器 (Compressor)** | **无损压缩**            | 对分组后的 Delta 值进行 **LZ4 无损压缩**。压缩完成后，将**基值  <img src="https://www.zhihu.com/equation?tex=D_{min}" alt="D_{min}" class="ee_img tr_noresize" eeimg="1">  附加到压缩后的有效载荷末尾**（用于解压缩时的恢复）。  **故障处理：** 如果压缩后的大小仍超过 4 kB，则直接丢弃压缩结果，将**原始未压缩数据包**（移除自定义标头后）发送给协议引擎。 |

| **Tx MUX**              | **出口选择**            | 将压缩后的数据包（或在压缩失败时将原始数据包）发送给协议引擎，准备发往网络。 |


### 解压缩路径（Decompression Path）

当数据从网络接收到 NIC 时，会经过解压缩路径：

**组件顺序：** **Rx DEMUX**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  **解压缩器**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  **解分组暂存缓冲区**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  **解分组器**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  **Delta 解码器**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  **Rx MUX/DMA 引擎+缓冲区**

| **组件**             | **功能**                | **机制/实现细节**                                            |

| -------------------- | ----------------------- | ------------------------------------------------------------ |

| **Rx DEMUX**         | **流量控制/解压缩判断** | 从协议引擎接收数据包后，检查其自定义标头中的 **1 位压缩标志**： 1. 如果未压缩，直接通过 Rx MUX 转发给 DMA 引擎+缓冲区（不解压）。 2. 如果已压缩，将数据包导向解压缩器。 |

| **解压缩器**         | **无损解压缩**          | 对数据包的有效载荷进行 **LZ4 解压缩**。解压后的数据被写入**解分组暂存缓冲区**。 |

| **解分组暂存缓冲区** | **缓存**                | 存储解压缩后的有效载荷。                                     |

| **解分组器**         | **位级别恢复**          | 将解压缩后的比特或字节序列**重新排列**回其**原始顺序**（即 Delta 值的顺序）。并将解分组后的 Delta 值与**附带的基值**一起发送给 Delta 解码器。 |

| **Delta 解码器**     | **值级别恢复**          | 对解分组器传来的每个 **Delta 值**，执行 **加法运算**：  <img src="https://www.zhihu.com/equation?tex=\text{原始值} = \text{Delta 值} + D_{min}" alt="\text{原始值} = \text{Delta 值} + D_{min}" class="ee_img tr_noresize" eeimg="1"> ，从而完全恢复原始的梯度或激活值。 |

| **Rx MUX**           | **出口**                | 将恢复后的原始数据包发送给 DMA 引擎+缓冲区，最终传输到接收方的 GPU 内存。 |


### Asic实现

**FPGA 实现（基准）：**

最初的实现基于 **Xilinx U280 FPGA**（采用 16nm 工艺）。

目前以 **300 MHz** 的时钟频率运行。

**ASIC 预估（目标）：**

通过使用 **7nm 工艺**，项目团队预估该设计可以优化并达到高达 **1 GHz** 的时钟频率。

**芯片面积：** 预估面积约为 ** <img src="https://www.zhihu.com/equation?tex=2 \text{mm}^2" alt="2 \text{mm}^2" class="ee_img tr_noresize" eeimg="1"> **。

这面积不到主流 Mellanox CX-7 NIC 芯片物理面积的 **0.1%**。

**功耗：** 功耗约为 **0.5 W**。

这仅占 CX-7 NIC 热设计功耗**25 W** 的大约 **2%**。

# Eﬀiciency of Distributed Training

![image-20251026175746443](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251026175746443.png)

>  一篇分析**大规模分布式大语言模型训练**性能、功耗与热行为的论文，研究方法感觉不需要太关注，它的结论还是比较有意思的，感觉是面向特别大规模计算中心的，估计自己这辈子都没机会用上(˘•ω•˘)

## 扩展策略（Scale-up vs. Scale-out）

![image-20251026180929133](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251026180929133.png)

| **模型类型**                                                 | **最佳硬件**                                          | **优势原因**                                                 |

| ------------------------------------------------------------ | ----------------------------------------------------- | ------------------------------------------------------------ |

| **小且计算密集型**（如  <img src="https://www.zhihu.com/equation?tex=\text{Llama3-70B}, \text{Mixtral-8x7B}" alt="\text{Llama3-70B}, \text{Mixtral-8x7B}" class="ee_img tr_noresize" eeimg="1"> ） | **Scale-out**（横向扩展，如  <img src="https://www.zhihu.com/equation?tex=64 \times \text{H100}" alt="64 \times \text{H100}" class="ee_img tr_noresize" eeimg="1"> ） | 具备**更高的聚合计算能力**。对于这些计算受限的模型，更多的 GPU 核心直接转化为更高的性能（ <img src="https://www.zhihu.com/equation?tex=\text{H100}" alt="\text{H100}" class="ee_img tr_noresize" eeimg="1">  在计算上花费的时间更少）。 |

| **大且通信密集型**（如  <img src="https://www.zhihu.com/equation?tex=\text{GPT3-175B}, \text{Mixtral-8x22B}" alt="\text{GPT3-175B}, \text{Mixtral-8x22B}" class="ee_img tr_noresize" eeimg="1"> ） | **Scale-up**（纵向扩展，如  <img src="https://www.zhihu.com/equation?tex=32 \times \text{H200}" alt="32 \times \text{H200}" class="ee_img tr_noresize" eeimg="1"> ）  |  <img src="https://www.zhihu.com/equation?tex=\text{H200}" alt="\text{H200}" class="ee_img tr_noresize" eeimg="1">  拥有 ** <img src="https://www.zhihu.com/equation?tex=1.76\times" alt="1.76\times" class="ee_img tr_noresize" eeimg="1">  更大的显存**和**更少的节点**。这减少了跨节点通信，提升了**通信局部性（node-locality）**，使其性能可以匹敌甚至超越  <img src="https://www.zhihu.com/equation?tex=\text{H100}" alt="\text{H100}" class="ee_img tr_noresize" eeimg="1"> 。 |


在通信量大的场景（例如  <img src="https://www.zhihu.com/equation?tex=\text{GPT3-175B}" alt="\text{GPT3-175B}" class="ee_img tr_noresize" eeimg="1">  的  <img src="https://www.zhihu.com/equation?tex=\text{TP2-PP16}" alt="\text{TP2-PP16}" class="ee_img tr_noresize" eeimg="1">  配置）， <img src="https://www.zhihu.com/equation?tex=\text{H200}" alt="\text{H200}" class="ee_img tr_noresize" eeimg="1">  能够以**更少的总 GPU 数量**（仅  <img src="https://www.zhihu.com/equation?tex=\text{H100}" alt="\text{H100}" class="ee_img tr_noresize" eeimg="1">  的一半）达到相当的吞吐量和更优的**单位  <img src="https://www.zhihu.com/equation?tex=\text{Token}" alt="\text{Token}" class="ee_img tr_noresize" eeimg="1">  能耗**。

>  感觉是没什么意外的结果

## 并行策略

### TP + PP 

**TP所需的集合通信和PP所需的点对点通信，会交织成一种“稀疏、非连续”的通信模式**。

-  **缺乏数据分块**：框架发出的通信操作是大量、细粒度的。例如，不是将一个大张量一次性发送，而是分解成许多小张量的Send/Recv操作。
-  **无法充分利用PCIe带宽**：PCIe等高速总线在传输大块连续数据时效率最高。频繁、小批量的通信请求会导致：
   -  **高延迟**：每个小请求都有开销。
   -  **低带宽利用率**：总线在多个小任务间切换，无法“饱和”运行，就像用大卡车一次次运送小包裹，卡车大部分时间是空的。
-  **加剧资源争用**：这些零散的通信任务会争抢有限的PCIe通道和网络接口卡资源，进一步增加延迟。

### PP-heavy 配置

在PP-Heavy（如`TP2-PP16`）配置中，流水线阶段很多，每个阶段内的模型切片较薄。

-  **通信集中化**：每个GPU只与它相邻的两个GPU（前一个阶段和后一个阶段）进行通信。通信路径非常固定和简单。
-  **大块数据传输**：由于每个流水线阶段要处理整个微批次的激活值，在阶段间传输的**数据块（Payload）更大**。

### TP/EP-heavy 配置

**节点内 vs 节点外带宽悬殊**：

-  **节点内**：通过NVLink互联，带宽可达**数百GB/s甚至TB/s**。
-  **节点间**：通过InfiniBand或以太网互联，带宽通常只有**100-800 Gb/s（约合10-100 GB/s）**，差了一个数量级。

**TP/EP-Heavy放大跨节点流量**：

-  如果一个TP=8的组分布在2个节点上（每节点4个GPU），那么每次All-Reduce都有大量数据需要在相对慢速的节点间链路上传输。
-  EP的All-to-All更是如此，会制造巨大的跨节点通信洪流。
   ![image-20251026185826939](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251026185826939.png)

| 并行策略         | 通信模式                            | 主要瓶颈                           | 对硬件拓扑的敏感性                         |

| :--------------- | :---------------------------------- | :--------------------------------- | :----------------------------------------- |

| **TP + PP 组合** | 稀疏、细粒度的集合通信 + 点对点通信 | PCIe/NIC带宽**利用率低下**，延迟高 | 高。通信模式与物理链路不匹配。             |

| **PP-Heavy**     | 集中、粗粒度的点对点通信            | 流水线**气泡**                     | 低。通信高效，但要注意阶段负载均衡。       |

| **TP/EP-Heavy**  | 密集、频繁的集合通信 / All-to-All   | **跨节点带宽** 成为天花板          | 极高。必须尽可能将通信组约束在单个节点内。 |


>  天哪，10-100 GB都嫌慢了，AI真烧钱
>
>  ![image-20251026185705673](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251026185705673.png)
>
>  

## 微批次大小

增加微批次大小并非总是有效的手段 。

-  超过最优值后，效率会降低，因为**通信带宽饱和**、计算回报递减以及**突发执行模式** 。

-  突发执行模式会提高**峰值功耗**和芯片温度，加剧**热节流**效应

   #### NVIDIA 集群（H200/H100）

   -   在**张量并行**或 ** <img src="https://www.zhihu.com/equation?tex=\text{FSDP}" alt="\text{FSDP}" class="ee_img tr_noresize" eeimg="1">  主导**的配置中（如  <img src="https://www.zhihu.com/equation?tex=\text{TP8-FSDP}" alt="\text{TP8-FSDP}" class="ee_img tr_noresize" eeimg="1"> ），增大  <img src="https://www.zhihu.com/equation?tex=\text{MBS}" alt="\text{MBS}" class="ee_img tr_noresize" eeimg="1">  能有效提高计算与通信的比率，性能得到提升。
   -   在**流水线并行**密集型配置中（如  <img src="https://www.zhihu.com/equation?tex=\text{TP2-PP16}" alt="\text{TP2-PP16}" class="ee_img tr_noresize" eeimg="1"> ），增大  <img src="https://www.zhihu.com/equation?tex=\text{MBS}" alt="\text{MBS}" class="ee_img tr_noresize" eeimg="1">  导致效率急剧下降。
      -  **原因：** 流水线停顿的出现，使得执行模式更加**突发**，**间歇性地未充分利用**计算资源。

   #### 2. AMD MI250 集群

   -  **普遍提升：** 对于  <img src="https://www.zhihu.com/equation?tex=\text{MI250}" alt="\text{MI250}" class="ee_img tr_noresize" eeimg="1"> ，增大  <img src="https://www.zhihu.com/equation?tex=\text{MBS}" alt="\text{MBS}" class="ee_img tr_noresize" eeimg="1">  通常会提高训练效率。
   -  **根本原因：**  <img src="https://www.zhihu.com/equation?tex=\text{MI250}" alt="\text{MI250}" class="ee_img tr_noresize" eeimg="1">  的瓶颈首先出现在**内存容量**上，而不是像  <img src="https://www.zhihu.com/equation?tex=\text{NVIDIA}" alt="\text{NVIDIA}" class="ee_img tr_noresize" eeimg="1">  集群那样容易达到**热量应力**的限制。
   -  **正向循环：**  <img src="https://www.zhihu.com/equation?tex=\text{MBS}" alt="\text{MBS}" class="ee_img tr_noresize" eeimg="1">  增大  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  工作负载更计算密集  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">   <img src="https://www.zhihu.com/equation?tex=\text{GPU}" alt="\text{GPU}" class="ee_img tr_noresize" eeimg="1">  提升时钟频率  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">   <img src="https://www.zhihu.com/equation?tex=\text{SM}" alt="\text{SM}" class="ee_img tr_noresize" eeimg="1"> 利用率和整体效率提高。

   #### 3. 硬件压力与效率的脱钩

   -  **峰值压力持续上升：** 无论训练吞吐量是否提高，**峰值功率**和**热水平**都随着  <img src="https://www.zhihu.com/equation?tex=\text{MBS}" alt="\text{MBS}" class="ee_img tr_noresize" eeimg="1">  的增大而持续上升。
   -  系统效应：
      -  ** <img src="https://www.zhihu.com/equation?tex=\text{TP}" alt="\text{TP}" class="ee_img tr_noresize" eeimg="1">  密集配置：** 峰值功率过高  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  触发**时钟频率限制**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  降低计算效率。
      -  ** <img src="https://www.zhihu.com/equation?tex=\text{PP}" alt="\text{PP}" class="ee_img tr_noresize" eeimg="1">  密集配置：** 流水线停顿  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  **突发执行模式**  <img src="https://www.zhihu.com/equation?tex=\to" alt="\to" class="ee_img tr_noresize" eeimg="1">  计算资源被间歇性浪费。

![image-20251026190714254](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251026190714254.png)

## 热不平衡

-  服务器前后GPU因气流不均存在显著温差（最高达27%）。

   ![image-20251026191805343](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251026191805343.png)

-  热节流导致频率下降，形成“拖后腿”GPU，影响整体同步与效率。

-  通过**热感知调度**（如将冷GPU分配至计算密集型阶段）可提升效率与热均衡

>  人话：让不热的GPU多干点活，温度匀一下（通风口的位置，O(∩_∩)O，莫名有点生草）

## 优化技术

### 激活重计算

在模型的前向传播过程中，**不保存所有中间结果**，而是在反向传播需要时**临时重新计算**这些结果

**解锁内存受限配置**：对于Mixtral-8x22B，它使得 `E8-T1-P4` 配置成为可能，从而实现了**超过2倍的训练效率提升**，通过牺牲计算来换取内存空间，从而**扩展了可行的并行策略设计空间**

**普遍的性能下降**，毕竟时间换空间嘛

### 通信计算重叠

将通信操作与计算操作并行执行，以“隐藏”通信延迟。

能够**提升通信密集型场景的效率**，但**在PP-heavy配置中失效甚至有害**：通信和计算同时进行，会争抢GPU的**内存带宽**和**流多处理器** 等共享资源。这反而可能导致**计算内核的执行时间延长**

没从根本上解决有限的网络带宽。

### LoRA微调

冻结预训练模型的大部分权重，只训练注入到模型中的少量低秩适配器

由于绝大部分模型参数被冻结，无需计算梯度和更新，**计算强度和内存访问强度都大幅降低**,与全参数训练相比，LoRA微调期间的**GPU功耗、温度和时钟频率都显著更低**,可以在内存更小、功耗限制更严格的GPU上运行。

代价是**模型表达能力可能受到限制**。虽然LoRA在很多任务上表现接近全量微调，但对于某些复杂任务，其性能可能无法达到全参数训练的水平。

![image-20251026192901357](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251026192901357.png)

>  网上查到介绍原理的图，感觉这个使用还挺普遍的
>
>  [(33 封私信 / 80 条消息) 一文彻底搞懂LoRA！为什么大厂都用它微调？低成本实战指南→建议收藏！ - 知乎](https://zhuanlan.zhihu.com/p/1963969812788126050)
>
>  感觉这个原理写的挺好的，有空可以看看



# SkipReduce

![image-20251029135026682](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251029135026682.png)

在深度学习（DNN）领域，模型和数据集的规模正以前所未有的速度增长 。为了应对这种复杂性，分布式训练（即将训练任务分配给多个GPU或节点）已成为必需 。

然而，分布式训练引入了新的瓶颈：**通信开销** 。在使用数据并行时，所有“工人”（workers）在每次迭代后都需要通过 AllReduce 集合通信操作来同步梯度（gradients） 。由于训练是同步的，每个工人都必须等待通信完成才能进入下一次迭代 ，这直接导致了计算资源的浪费 和训练速度的瓶颈 。

在训练过程中，梯度天然是“稀疏”的 ，其数值分布集中在零附近 。这意味着并非所有梯度数据都对模型收敛至关重要 。

>[(33 封私信 / 80 条消息) 分布式训练中All-Reduce、All-Gather、Reduce-Scatter原理介绍 - 知乎](https://zhuanlan.zhihu.com/p/17201336684)
>
>查了下，大概明白分布式训练的原理了，可以作为前置知识

## **现有方案的局限**



 此前的研究也注意到了这一点，并提出了各种压缩方法来减少通信量：

### **Top-k 稀疏化** 

只发送幅度最大的 k% 的梯度 。但这种方法需要以特殊的稀疏格式（COO）发送，这带来了额外的索引开销（导致消息翻倍） ，并且难以集成到现有的通信库（如NCCL）中 。

### **PowerSGD：** 

使用低秩近似来压缩梯度 。

![image-20251029135934530](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251029135934530.png)

上述这些方法虽然减少了通信数据量，但引入了**显著的计算开销**（用于压缩、索引或重建） 。在早期的低带宽网络中，这些开销是值得的。但在现代HPC系统的高带宽（如16 GBps）环境下，**这些计算开销本身成为了新的瓶颈**，甚至抵消了通信节省带来的好处 。

![image-20251029141455729](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251029141455729.png)

>  SkipReduce不进行复杂的压缩，而是通过简单地“跳过” AllReduce 中的某些通信步骤，来“成批”地丢弃梯度，从而直接减少通信时间 。

## SkipReduce 算法实现

| **特性**     | **AllReduce_Dropout (细粒度跳过)**                   | **SkipReduce (粗粒度/切片级跳过)**             |

| ------------ | ---------------------------------------------------- | ---------------------------------------------- |

| **目标**     | 减少**消息携带的信息内容**（梯度信息）               | 减少**通信时间**（通过跳过步骤）               |

| **跳过单位** | **单个梯度元素**（基于伯努利过程）                   | **梯度切片**（Ring AllReduce 中的一步/迭代）   |

| **通信量**   | **消息大小保持不变**                                 | **通信步骤减少**，直接缩短了集体操作的持续时间 |

| **实现**     | 在归约核中对每个梯度元素进行随机决策（类似 Dropout） | **减少 Reduce-Scatter 循环的迭代次数**         |


如果决定跳过  <img src="https://www.zhihu.com/equation?tex=S" alt="S" class="ee_img tr_noresize" eeimg="1">  步 Reduce-Scatter 步骤，则 Reduce-Scatter 阶段只执行  <img src="https://www.zhihu.com/equation?tex=(N - 1 - S)" alt="(N - 1 - S)" class="ee_img tr_noresize" eeimg="1">  步。

每跳过一步 Reduce-Scatter，就相当于**跳过了每个 GPU 的一个完整的梯度切片**的最终归约。

### Static SkipReduce

每次迭代中，所有 GPU **跳过相同的、固定的梯度切片**。

**问题：** 导致**偏差**（或不公平性），因为相同的特定切片永远不会对集体通信结果做出贡献，可能损害模型准确性。

### Random SkipReduce

在每次训练迭代中，通过引入一个**随机偏移量**来移动 Reduce-Scatter 的切片索引， 确保**每次迭代中跳过的切片是变化的**，从而保证所有梯度切片都有机会参与到归约中，促进随机性。

**同步挑战与解决方案：** 所有 GPU 必须生成相同的随机数来保证索引同步。通过修改 NCCL，将**当前迭代计数**作为**通用种子**从主机传递给所有 GPU 来解决，避免了额外的同步开销。

在保持几乎相同的通信加速（仅高了 1.1% 的开销）的同时，**显著提高了模型准确率**，其中随机SkipReduce在75%的跳过率下将测试准确率提高了19个百分点。甚至在高跳过率下能与 AllReduce_Dropout 的精度相匹配。

### Selective SkipReduce

梯度稀疏性在模型的不同层之间是不均匀的，如某些层中大梯度幅度的集中所示。主要结论由于梯度的幅度与其重要性相关，因此具有高浓度大梯度幅度的层可以被认为更重要，因此对跳过更敏感。相反，具有较少重要梯度的层不太敏感，是跳过的更好候选者。

![image-20251029191104645](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251029191104645.png)

通过跳过大的、不重要的层，同时保护小的、关键的层以维持训练精度，从而实现显著的通信加速。

虽然理解为什么某些层具有相对更高的重要性可能需要严格的理论理解，并且超出了本文的范围，但某些层的重要性可以是直观的。例如，我们可以预期VGG-19中的第一个卷积层和transformers中的嵌入层对跳过更敏感，因为它们启动了输入到网络潜在空间的投影。

>  有点绷不住，哈哈

## 结果

### 时间-精度加速

![image-20251029192912960](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251029192912960.png)

**对比基线 AllReduce：** 在所有工作负载和运行中，SkipReduce 都能够**胜过基线 AllReduce**，并实现了相对于基线 AllReduce 的中值加速。

**对比 PowerSGD：** SkipReduce 在五次运行中实现了相对于 PowerSGD **平均 16% 的 TTA 加速**。

### 迭代时间对比

在 LLaMA3.2 上，SkipReduce 的迭代时间比 PowerSGD **慢 6%**

![image-20251029193046136](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251029193046136.png)

### 跳过 Reduce-Scatter (RS) 与 AllGather (AG) 的权衡

![image-20251029193359456](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251029193359456.png)

| **方案**                     | **跳过步骤**                                | **性能影响**         | **准确率损失**                                              | **关键发现**                                                 |

| ---------------------------- | ------------------------------------------- | -------------------- | ----------------------------------------------------------- | ------------------------------------------------------------ |

| **方案一 (SkipReduce 现有)** | 跳过 **50% 的 Reduce-Scatter (RS)**         | **收敛速度快**       | 相对较小                                                    | 仅针对 RS 阶段可以减少通信时间。                             |

| **方案二 (扩展 SkipReduce)** | 跳过 **25% 的 RS 和 25% 的 AllGather (AG)** | **显著降低收敛速度** | 训练准确率降低 **1.95** 个点；测试准确率降低 **1.3** 个点。 | **跳过 AllGather 的代价更高**，因为它涉及所有其他 GPU 的信息，导致更高的信息损失。 |


# Torus Networks

![image-20251031091603164](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251031091603164.png)

## 问题

All-to-All集合通信，由于其复杂的点对点通信模式和阻塞特性，已成为分布式DLRM和MoE加速中的主要性能瓶颈。此外，长时间的分布式处理经常遇到链路故障，与支持任意到任意连接（如Clos网络）的交换式拓扑不同，环形网络上的All-to-All通信会因共享路由路径而相互干扰，从而造成关键的性能限制。

无故障情况下，我们提出了 HalfRing 算法和 DimRotation 调度。HalfRing 利用双向链路在环上构建最短通信路径，而 DimRotation 在多个维度上分配每个数据块的通信序列，以实现完整的带宽利用率。在有故障的情况下，我们引入了 FoldedRing 算法和 MATE 调度。FoldedRing 促进环上的容错通信，而 MATE 通过利用来自其他维度的可用链路来加速故障环上的通信。

## 无故障场景优化

### HalfRing 算法（单维）

#### Ring算法的问题

总是沿着固定的方向（比如**顺时针**）进行传输，导致很多通信走的不是最短路径。

#### 改进

**最短路径优先：**

-  对于任何一对通信的节点，HalfRing 不再盲目地只走一个方向。
-  它会根据发送者和接收者之间的**实际距离**，选择**最短的路径**进行传输。

**双向同时传输：**

-  由于 HalfRing 确保所有通信都走最短路径，这使得通信链路的利用变得更“干净”：每个通信阶段**只在一个方向上**消耗链路带宽。

-  这样，**另一个方向**的链路（逆时针链路）就可以**完全空闲**下来，用于处理具有**相同跳数**的另一组通信。

-  通过这种方式，HalfRing 实现了**同时利用顺时针和逆时针链路**进行不同的通信任务，且**没有链路冲突**

   在具有奇数个节点的环中（N = 2k + 1），有 2k 个阶段，并且 All-to-All 可以在 k 对中完成。对于具有偶数个节点的环（N = 2k），有 2k − 1 个阶段，导致一个未配对的阶段，HalfRing 均匀地分割未配对阶段的数据，并将其在两个方向上发送，从而充分利用带宽。

![image-20251030100940440](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251030100940440.png)

### DimRotation 调度（多维）

3D环上的All-to-All需要跨X、Y和Z三个维度进行三个阶段，并且每个阶段都充分利用相应维度中所有环的带宽。在每个阶段，每个维度中的环同时传输数据。流水线调度将数据分成多个块，然后以相同的X-Y-Z维度顺序依次通信。流水线通过在不同维度上同时运行多个块来提高带宽利用率。

流水线调度不可避免地会引入气泡，如果块大小较大，流水线无法充分重叠不同维度上不同块的时间，从而导致性能不佳。相反，当块大小较小时，大量的块会引入显著的调度成本和通信初始化开销，从而增加整体延迟。

对于一个N维环面，数据被均匀地分成𝑁块，第𝑖𝑡ℎ块按照维度𝑖𝑡ℎ、𝑖𝑡ℎ+1、...等的顺序进行通信。如图，DimRotation允许三个块执行无冲突、全覆盖的多维通信，从而实现完全的带宽利用率。主要结论同时，块的数量被设置为完全重叠通信所需的最小值，从而显著减少调度开销。

![image-20251030104108200](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251030104108200.png)

>  简单查了下，维度顺序路由（DOR）规定了严格的维度传输顺序（如 X  <img src="https://www.zhihu.com/equation?tex=\rightarrow" alt="\rightarrow" class="ee_img tr_noresize" eeimg="1">  Y  <img src="https://www.zhihu.com/equation?tex=\rightarrow" alt="\rightarrow" class="ee_img tr_noresize" eeimg="1">  Z）。一旦数据包从 X 维进入 Y 维，它就不能再回到 X 维进行通信
>
>  沟槽的五级流水线还在追我，不过这是N级流水线了

## 容错算法

### 单维折叠环

![image-20251030204749486](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251030204749486.png)

当节点 1 和节点 4 之间出现链路故障时，所有逆时针链路带宽都会被重新利用，以补偿故障链路。通信以折叠环方式继续进行。折叠环完成阶段 1 所需的时间是环的两倍。

### 多维MATE调度

故障环上的慢速传输导致DimRotation调度中的不匹配。由于故障环，X维度的传输速度减慢，这反过来会影响其他维度的传输，导致整体All-to-All性能下降。

其次，FoldedRing算法只能解决环内的单个链路故障。对于两个或多个故障，FoldedRing无法在故障环上建立连接。因此，尽管故障链路的两个端点之间的通信仍然可以通过其他方向的路由继续进行，但All-to-All仍然被迫中断。

![image-20251030213729928](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251030213729928.png)

MATE 利用同一拓扑内**其他 X 维环**和**其他维度（如 Y 维）的链路**，为故障环上的每个节点构建**额外的、无冲突的双向连接**。通过这些额外的链路，MATE 使用高效的 **HalfRing** 算法来传输故障环上的**剩余数据**。同时，故障环本身仍使用 FoldedRing 传输**部分数据**。

![image-20251030215012209](https://cdn.jsdelivr.net/gh/FDU-ZJN/Markdown4Zhihu/master/Data/MICRO-2025-Systems-for-Al-Training-部分论文阅读/image-20251030215012209.png)

通过在这些额外的X维链接和故障环内的FoldedRing上分配数据以进行同时传输，增强了全对全通信。

| **MATE (基础版)**                                            | **MATEe (增强版)**                                           |

| ------------------------------------------------------------ | ------------------------------------------------------------ |

| **完全消除**正常阶段的通信。                                 | **分配**一部分数据在正常阶段通过故障环通信。                 |

| 承载**全部**需要在故障环上传输的数据。 ( <img src="https://www.zhihu.com/equation?tex=M" alt="M" class="ee_img tr_noresize" eeimg="1">  阶段数据量较大)  | 承载**剩余**未在正常阶段传输的数据。 ( <img src="https://www.zhihu.com/equation?tex=M_e" alt="M_e" class="ee_img tr_noresize" eeimg="1">  阶段数据量较小)  |

| **纯粹分离：** 将故障环的通信完全推迟到加速阶段，利用其他维度资源统一解决。 | **混合利用：** 充分利用故障环的**残余带宽**，减轻加速阶段的压力。 |


>  废物（FoldedRing）利用的程度的区别

## 实现效果

### **无故障 场景优化效果**

| **对比项**                    | **方案**                       | **性能提升 (平均)**              | **备注**            |

| :---------------------------- | :----------------------------- | :------------------------------- | :------------------ |

| 与基准 (Ring + Pipeline) 对比 | HalfRing 算法                  | 1.56×                            | 单独使用            |

| 与基准 (Ring + Pipeline) 对比 | DimRotation 调度               | 1.45×                            | 单独使用            |

| 与基准 (Ring + Pipeline) 对比 | HalfRing + DimRotation         | 2.28×                            | 结合使用            |

| 与 Google TPUv4 DOR 对比      | HalfRing + DimRotation         | 1.57×                            | 在模拟 TPUv4 pod 上 |

| 真实模型（端到端）性能        | HalfRing + DimRotation vs 基准 | All-to-All: 1.97×，总时间: 1.64× | DLRM 和 MoE 模型    |


------

### **容错 (Fault-Tolerant) 场景优化效果**

| **对比项**                    | **方案**              | **性能提升 (平均)**              | **备注**              |

| :---------------------------- | :-------------------- | :------------------------------- | :-------------------- |

| 与基准 (Ring + Pipeline) 对比 | FoldedRing + Pipeline | 0.55×                            | 容错但性能下降        |

| 与基准 (Ring + Pipeline) 对比 | FoldedRing + MATE     | 1.36×                            | 容错且性能提升        |

| 与基准 (Ring + Pipeline) 对比 | FoldedRing + MATEe    | 1.37×                            | 容错且性能提升        |

| 与 Google TPUv4 WFR 对比      | MATEe                 | 1.61×                            | All-to-All 带宽饱和时 |

| 真实模型（端到端）性能        | MATE vs 基准          | All-to-All: 1.24×，总时间: 1.20× | 单链路故障            |

| 真实模型（端到端）性能        | MATEe vs 基准         | All-to-All: 1.38×，总时间: 1.29× | 单链路故障            |


------

### **其他关键效果**

| **效果类型** | **方案**                      | **性能提升或特点**   | **场景说明**              |

| :----------- | :---------------------------- | :------------------- | :------------------------ |

| 可扩展性     | MATE / MATEe                  | 性能随维度增加而提升 | 从2D到4D网络              |

| 非均匀通信   | HalfRing + DimRotation vs DOR | 1.27×                | MoE 模型非均匀 All-to-All |

| 非均匀通信   | MATEe vs WFR                  | 1.17×                | 故障情况下，MoE 模型      |

| 多重故障     | MATE vs WFR                   | 1.14× 到 1.55×       | 多种多重链路故障类型      |


