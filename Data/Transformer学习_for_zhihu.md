---
title: Transformer图文详解
date: 2025-11-22 20:17:56
categories: 计算机
tags:
  - Transformer
cover: /img/cover_21.jpg
highlight_shrink: true
abbrlink: 1253334553
description: 从Money is all you need开始学习Transformer
---

>  传世经典[1706.03762](https://arxiv.org/pdf/1706.03762) 							Money is all you need（雾）Money is all I need（确信）
>
>  ![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-f6380627207ff4d1e72addfafeaff0bb_1440w_1.jpg)
>
>  左侧编码，右侧解码，多头自注意力由多个自注意力组成。Add 表示残差连接，用于防止网络退化。Norm用于对每一层的激活值进行归一化。

## 输入

Transformer 中单词的输入表示 **x**由**单词 Embedding** 和**位置 Embedding** 相加得到。

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-b0a11f97ab22f5d9ebc396bc50fa9c3f_1440w_1.jpg)

Input Embedding：单词的 Embedding 有很多种方式可以获取，例如可以采用 Word2Vec、Glove 等算法预训练得到，也可以在 Transformer 中训练得到。

Position Encoding：位置 Embedding 用 **PE**表示，在Transformer中的计算公式为：

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-8b442ffd03ea0f103e9acc37a1db910a_1440w_1.jpg)

这样做能利用序列的顺序和位置关系（毕竟狗咬人和人咬狗肯定不一个意思）

## self-attention

<img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-6444601b4c41d99e70569b0ea388c3bd_1440w_1.jpg" alt="img" style="zoom:50%;" />

**输入 (Q, K, V)**：**Q (Query)**: 查询向量，**K (Key)**: 键向量，**V (Value)**: 值向量


<img src="https://www.zhihu.com/equation?tex=Q K^T$$，积的结果代表了查询和键之间的**相似度**，得到注意力分数矩阵。这个矩阵的每一行**代表一个特定的 Query 向量与所有 Key 向量的相似度得分**。

-  Scale：将注意力分数除以 √dₖ，防止点积结果过大导致softmax梯度消失。

-  Mask (opt.)：在解码器中用于掩盖后续位置的信息，确保当前位置只能关注之前的位置。**防止模型“作弊”**，确保它只能访问在当前位置之前或允许访问的信息。

-  SoftMax：注意力权重归一化（按行归一化，毕竟是相似度在归一化嘛）

-  Matmul2：将注意力权重与值向量 V 相乘

   最后就得到了我们的**传世经典**：

   ![image-20251122215913218](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/image-20251122215913218_1.png)

>  Q：突然发现一个问题，X是怎么转化为Q,K,V的？
>
>  翻了翻相关博客大概是：从X乘线性矩阵**WQ,WK,WV**计算得到**Q,K,V**，这三个矩阵都是可训练的
>
>  第一次看论文忘了时间，很天才有趣的想法，挺有意思，但今天就到这里早点回去吧

## Multi-Head Attention

<img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-b0ea8f5b639786f98330f70405e94a75_1440w_1.jpg" alt="img" style="zoom: 33%;" />

个人理解：词与词之间的关系是复杂的，因此需要多个注意力层来分别表示不同特征，比如语义关系啦，逻辑关系啦什么等等

论文里使用了8层

得到 8 个输出矩阵之后，Multi-Head Attention 将它们拼接在一起，然后传入一个**Linear**层，得到 Multi-Head Attention 最终的输出**Z**。

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-35d78d9aa9150ae4babd0ea6aa68d113_1440w_1.jpg)

## Encoder整体

### Add & Norm

Add是残差连接（再加一下自己），避免梯度爆炸，归一化使每一层始终保持相似的均值和方差，加速模型收敛。

![image-20251123160819131](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/image-20251123160819131_1.png)

### Feed Forward

两层的全连接，第一层加Relu。

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-47b39ca4cc3cd0be157d6803c8c8e0a1_1440w_1.jpg)

通过线性变换，先将数据映射到高纬度的空间再映射到低纬度的空间，提取了更深层次的特征。（一个博客的说法）

### 结构

<img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-45db05405cb96248aff98ee07a565baa_1440w_1.jpg" alt="img" style="zoom:33%;" />六层Encoder Block串联组成整个Encoder。

## Decoder整体

<img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/image-20251123162011036_1.png" alt="image-20251123162011036" style="zoom: 50%;" />包含两个 Multi-Head Attention 层, K,V由Encoder提供，**Q**使用上一个 Decoder block 的输出计算

### 第一个Multi-Head Attention

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-4616451fe8aa59b2df2ead30fa31dc98_1440w_1.jpg)

使用了前面说的Mask,就像你在做翻译时，可以看你前面翻译好的词，但不能看后面未来的作弊。

计算就是在softmax前挡一下就行

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-35d1c8eae955f6f4b6b3605f7ef00ee1_1440w_1.jpg)

>  疑问：在为什么在QK乘后再挡，我理解这能说的通，将前面词汇与该词汇的注意力关系置0，这样就相当于前面的词与后面还没出现的词没有任何关系，那为什么不一开始就挡掉将对应位置的embedding变为空，完全模拟这几个词不存在。
>
>  我大概明白了，softmax前将对应位挡掉（-无穷）能保证输出的注意力为0，一开始就挡，最后输出的注意力在这几位不会为0，也就是错误的注意还未出现的词。

### 第二个Multi-Head Attention

结构无变化， 使用Encoder 的输出 **C**计算得到 **K, V**，使用上一个 Decoder block 的输出 **Z** 计算得到 **Q**

这样做的好处是在 Decoder 的时候，每一位单词都可以利用到 Encoder 所有单词的信息。

### Decoder的线性层

经过6层decoder block后的输出矩阵维度为

$ <img src="https://www.zhihu.com/equation?tex=[\text{Batch Size}, \text{序列长度 }, \text{模型维度 } d_{\text{model}}]" alt="Q K^T" alt="[\text{Batch Size}, \text{序列长度 }, \text{模型维度 } d_{\text{model}}]" alt="Q K^T" class="ee_img tr_noresize" eeimg="1"> $，积的结果代表了查询和键之间的**相似度**，得到注意力分数矩阵。这个矩阵的每一行**代表一个特定的 Query 向量与所有 Key 向量的相似度得分**。

-  Scale：将注意力分数除以 √dₖ，防止点积结果过大导致softmax梯度消失。

-  Mask (opt.)：在解码器中用于掩盖后续位置的信息，确保当前位置只能关注之前的位置。**防止模型“作弊”**，确保它只能访问在当前位置之前或允许访问的信息。

-  SoftMax：注意力权重归一化（按行归一化，毕竟是相似度在归一化嘛）

-  Matmul2：将注意力权重与值向量 V 相乘

   最后就得到了我们的**传世经典**：

   ![image-20251122215913218](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/image-20251122215913218_1.png)

>  Q：突然发现一个问题，X是怎么转化为Q,K,V的？
>
>  翻了翻相关博客大概是：从X乘线性矩阵**WQ,WK,WV**计算得到**Q,K,V**，这三个矩阵都是可训练的
>
>  第一次看论文忘了时间，很天才有趣的想法，挺有意思，但今天就到这里早点回去吧

## Multi-Head Attention

<img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-b0ea8f5b639786f98330f70405e94a75_1440w_1.jpg" alt="img" style="zoom: 33%;" />

个人理解：词与词之间的关系是复杂的，因此需要多个注意力层来分别表示不同特征，比如语义关系啦，逻辑关系啦什么等等

论文里使用了8层

得到 8 个输出矩阵之后，Multi-Head Attention 将它们拼接在一起，然后传入一个**Linear**层，得到 Multi-Head Attention 最终的输出**Z**。

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-35d78d9aa9150ae4babd0ea6aa68d113_1440w_1.jpg)

## Encoder整体

### Add & Norm

Add是残差连接（再加一下自己），避免梯度爆炸，归一化使每一层始终保持相似的均值和方差，加速模型收敛。

![image-20251123160819131](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/image-20251123160819131_1.png)

### Feed Forward

两层的全连接，第一层加Relu。

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-47b39ca4cc3cd0be157d6803c8c8e0a1_1440w_1.jpg)

通过线性变换，先将数据映射到高纬度的空间再映射到低纬度的空间，提取了更深层次的特征。（一个博客的说法）

### 结构

<img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-45db05405cb96248aff98ee07a565baa_1440w_1.jpg" alt="img" style="zoom:33%;" />六层Encoder Block串联组成整个Encoder。

## Decoder整体

<img src="https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/image-20251123162011036_1.png" alt="image-20251123162011036" style="zoom: 50%;" />包含两个 Multi-Head Attention 层, K,V由Encoder提供，**Q**使用上一个 Decoder block 的输出计算

### 第一个Multi-Head Attention

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-4616451fe8aa59b2df2ead30fa31dc98_1440w_1.jpg)

使用了前面说的Mask,就像你在做翻译时，可以看你前面翻译好的词，但不能看后面未来的作弊。

计算就是在softmax前挡一下就行

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-35d1c8eae955f6f4b6b3605f7ef00ee1_1440w_1.jpg)

>  疑问：在为什么在QK乘后再挡，我理解这能说的通，将前面词汇与该词汇的注意力关系置0，这样就相当于前面的词与后面还没出现的词没有任何关系，那为什么不一开始就挡掉将对应位置的embedding变为空，完全模拟这几个词不存在。
>
>  我大概明白了，softmax前将对应位挡掉（-无穷）能保证输出的注意力为0，一开始就挡，最后输出的注意力在这几位不会为0，也就是错误的注意还未出现的词。

### 第二个Multi-Head Attention

结构无变化， 使用Encoder 的输出 **C**计算得到 **K, V**，使用上一个 Decoder block 的输出 **Z** 计算得到 **Q**

这样做的好处是在 Decoder 的时候，每一位单词都可以利用到 Encoder 所有单词的信息。

### Decoder的线性层

经过6层decoder block后的输出矩阵维度为

$$[\text{Batch Size}, \text{序列长度 }, \text{模型维度 } d_{\text{model}}]" class="ee_img tr_noresize" eeimg="1">

线性层将模型的内部抽象表示  <img src="https://www.zhihu.com/equation?tex=d_{\text{model}}" alt="d_{\text{model}}" class="ee_img tr_noresize" eeimg="1">  维度，投影到**词汇表大小 (  <img src="https://www.zhihu.com/equation?tex=|\mathcal{V}|" alt="|\mathcal{V}|" class="ee_img tr_noresize" eeimg="1"> )** 维度。


<img src="https://www.zhihu.com/equation?tex=[\text{Batch Size}, \text{序列长度}, |\mathcal{V}|]" alt="[\text{Batch Size}, \text{序列长度}, |\mathcal{V}|]" class="ee_img tr_noresize" eeimg="1">

### 最终的softmax

根据输出矩阵的每一行预测下一个单词（输出概率最大的单词）

![img](https://raw.githubusercontent.com/FDU-ZJN/Markdown4Zhihu/master/Data/Transformer学习/v2-0938aa45a288b5d6bef6487efe53bd9d_1440w_1.jpg)

>  大体结构是懂得，其实感觉单论结构比卷积大概都简单，核心就在他的self-attention上，而他的self-attention的核心就在QK乘的那一下，得到注意力的那一瞬间，这大概就是大道至简吧。
>
>  但感觉计算量好恐怖，各种大矩阵乘。走的卷积相反的路了属于是。一个局部一个全局。不过注意力的并行性好完美地适配GPU了，时也势也。

