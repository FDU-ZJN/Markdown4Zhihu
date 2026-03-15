---
title: 开源GPU哪家强
date: 2025-11-26 14:11:39
categories: IC
tags:
  - GPU
  - 体系结构
cover: /img/cover_24.jpg
highlight_shrink: true
abbrlink: 3543225653
description: 较有影响力的开源GPU调研对比
---

>  我们需要开源驱动，还需要开源GPU，还需要Windows开源，Intel、AMD的CPU开源ლ(´ڡ`ლ)
>
>  ![cover_24](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/cover_24_1.jpg)
>
>  Arch用户表示英伟达的开源驱动真不好用

![img](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/v2-b65bf20b64dd18fc2dae434bfda5e155_1440w_1.webp)

>  原来GPU还能不支持图像吗

## 乘影Ventus



github仓库:[THU-DSP-LAB/ventus-gpgpu: GPGPU processor supporting RISCV-V extension, developed with Chisel HDL](https://github.com/THU-DSP-LAB/ventus-gpgpu)（文档、PPT）

论文：[Ventus: A High-performance Open-source GPGPU Based on RISC-V and Its Vector Extension | IEEE Conference Publication | IEEE Xplore](https://ieeexplore.ieee.org/document/10818098)（ICCD）

![image-20251127173935149](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251127173935149_1.png)

### 硬件

![image-20251126145632042](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251126145632042_1.png)

![image-20251126150136003](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251126150136003_1.png)

>  看仓库仿真用的是verilator，xs

### 软件

![image-20251126145840918](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251126145840918_1.png)

![image-20251126150118311](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251126150118311_1.png)

![image-20251126151345399](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251126151345399_1.png)

SM确实和处理器长的挺像的，而更高层的CTA调度大概就是GPU的逻辑了

### 结果

![image-20251126150216443](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251126150216443_1.png)

在台积电 (TSMC) 的 12nm 工艺库下，一个 8-warp-16-thread 配置的 Ventus 单个 SM可达到 **1.2 GHz** 的时钟频率，并占用  <img src="https://www.zhihu.com/equation?tex=876084~\mu m^{2}" alt="876084~\mu m^{2}" class="ee_img tr_noresize" eeimg="1">  的面积

>他甚至不愿意给GFLOPS
>应该还没流片，感觉是在vortex的基础上实现的，怪不得那时觉得像。GPUGPU与RISC-V生态结合起来，毕竟CUDA一家独大，就用RISC-V的生态优势来弥补自造生态的不足。
>
>加了不少SIMT指令，大量uniform寄存器，前端生态怎么维护可能也是个问题？

## Vortex

官网：[vortex.cc.gatech.edu/](https://link.zhihu.com/?target=https%3A//vortex.cc.gatech.edu/)（下论文）

git:[vortexgpgpu/vortex](https://github.com/vortexgpgpu/vortex)

PPT:[vortexgpgpu/vortex_tutorials](https://github.com/vortexgpgpu/vortex_tutorials)

主论文：[Vortex: Extending the RISC-V ISA for GPGPU and 3D-Graphics Research](https://vortex.cc.gatech.edu/publications/vortex_micro21_final.pdf)

![image-20251126154601000](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251126154601000_1.png)

![image-20251126153940595](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251126153940595_1.png)

![image-20251126154014260](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251126154014260_1.png)

### 结果

![image-20251126154816434](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251126154816434_1.png)

![image-20251127173328111](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251127173328111_1.png)

在早期使用 15nm 教育版工艺库进行综合时，一个 **8W-4T 单核心** 的 Vortex 设计预计功耗为 **46.8 mW**，运行频率为 **300 MHz**。

32个核心时在Stratix 10 FPGA上达到**25.6 GFlops @ 200MHz**，但没说在什么精度。

贴个便宜的V100性能图

![image-20251205090022330](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251205090022330_1.png)

时钟是1380MHZ，4090我记得双精度大概有1.3T

>  只使用5条指令扩展，软件栈似乎比ventus更完善

![image-20251126155742143](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251126155742143_1.png)
偶然看到的一篇加速3DGS的GPU的论文，看时间是最近两天放在arxiv的，scoop？

## miaow（发音为“me-ow”）

github地址：[VerticalResearchGroup/miaow: An open source GPU based off of the AMD Southern Islands ISA.](https://github.com/VerticalResearchGroup/miaow)

![image-20251127152717794](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251127152717794_1.png)

>  这界面真够干净的

纯verilog写，太强了，

![image-20251127153456857](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251127153456857_1.png)

**RTL 实现部分**: 计算单元（CU）是使用可综合的Verilog RTL实现的 。

![image-20251205082858508](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251205082858508_1.png)

**行为级模型部分**: L2缓存、片上网络（OCN）和内存控制器等组件则使用行为级C/C++模块拟 。

![image-20251127172021604](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251127172021604_1.png)

![image-20251127172306629](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/开源GPU哪家强/image-20251127172306629_1.png)

>个人觉得可能更倾向于一个开源的GPU教学方案？主要部分在11年前就完成了。