---
title: CS146S学习记录
date: 2026-02-22 09:11:51
categories: 计算机
tags:
  - LLM
  - vibe coding
cover: /img/cover_31.jpg
abbrlink: 3744789499
---

>  偷个闲，心血来潮学一下很火的CS146S，就听英文版了，当作练一下英语听力
>
>  课程源链接：[CS146S: The Modern Software Developer - Stanford University](https://themodernsoftware.dev/)
>
>  [ShouZhengAI/CS146S_CN: 动手学CS146S中文版课程，包含assignments，vibe coding工具等，本项目将长期持续维护，致力于打造中文最好的vibe coding教程。](https://github.com/ShouZhengAI/CS146S_CN)
>
>  这里是中文版资料的git仓库，整理的很好,也有b站有中文字幕的链接

## Introduction and how an LLM is made

[Deep Dive into LLMs like ChatGPT - YouTube](https://www.youtube.com/watch?v=7xTGNNLPyMI)

>  ​	发现搞科研的都喜欢用Mac是吗，感觉我的下一台电脑也可以考虑下

### 基础介绍（可以直接跳过）

![image-20260222092312355](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/CS146S/image-20260222092312355_1.png)

一个叫FineWeb的英语网页数据集，15-trillion tokens，44TB，这么大啊。。。

下面其实就是老生常谈的Transformer入门，可以再听一遍复习一下

序列化

<img src="https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/CS146S/image-20260222094757060_1.png" alt="image-20260222094757060" style="zoom: 50%;" />

推理

<img src="https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/CS146S/image-20260222095607015_1.png" alt="image-20260222095607015" style="zoom: 67%;" />

神经网络内部

一个很有趣的网站课程里的[LLM Visualization](https://bbycroft.net/llm)，Transformer的架构非常直观，可以清晰地看到Q,K,V，还有动画演示计算过程

<img src="https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/CS146S/image-20260222100249718_1.png" alt="image-20260222100249718" style="zoom: 25%;" />

就是闭环地一个个蹦

![image-20260222101137882](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/CS146S/image-20260222101137882_1.png)

兴致勃勃地跟着学vibe coding，学到一半了发现cursor不让中国学生认证。。。唉，算了，那以后再学吧