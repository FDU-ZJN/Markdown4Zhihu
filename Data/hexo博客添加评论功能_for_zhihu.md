---
title: hexo-butterfly主题giscus评论
abbrlink: 932177725
date: 2025-11-28 13:25:08
categories: 网站
tags:
  - 博客
cover: /img/cover_25.jpg
highlight_shrink: false
description: 使用giscus在hexo-butterfly实现评论功能
---

>  尝试gitalk失败，一直network error，遂放弃

## 安装giscus

链接：[GitHub Apps - giscus](https://github.com/apps/giscus)

![image-20251128180923734](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/hexo博客添加评论功能/image-20251128180923734.png)

可以选安装到全局也可以选择安装到某一个仓库（后面可以改），然后点击 **Install** 安装

## 配置对应仓库的Discuss

找到你安装的对应仓库，打开settings，将Discussion勾选

![image-20251128181108419](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/hexo博客添加评论功能/image-20251128181108419.png)

随后点击 **Set up discussions**，进入 Discussions 配置界面（我已经配置好了，所以没有，正常在Discussions右边绿色）。

![创建Announcements板块](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/hexo博客添加评论功能/d45dd33592f48f704e95cbca1b749912.png)

进行下一步前，检查是否满足以下要求

![image-20251128181428464](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/hexo博客添加评论功能/image-20251128181428464.png)

## Giscuss配置

配置地址：[giscus](https://giscus.app/zh-CN)

填写仓库信息，格式 `myusername/myrepo`

![image-20251128181346906](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/hexo博客添加评论功能/image-20251128181346906.png)

选择Discussion 的标题包含页面的 URL

![如图所示](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/hexo博客添加评论功能/65642a36d4d5e378f6e0134ee8a3c42b.png)

分类选择刚建成的Announcement

![选择分类](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/hexo博客添加评论功能/a63f2ce0ae62f84980ab7cca4f3341c3.png)

## 博客配置

按照自动生成的配置填写_config.yml配置

![如图所示](https://cdn.statically.io/gh/FDU-ZJN/Markdown4Zhihu/master/Data/hexo博客添加评论功能/ad8fcfd04a3cca32affeba67ab9ae2bd.png)将启用 giscus 处复制的 data-repo 的值粘贴至 butterfly 主题配置文件中的 repo 处；
将 data-repo-id 处复制的值粘贴值配置文件中的 repo-id 处；
将 data-category-id 处复制的值粘贴至配置文件中的 category-id 处
不加引号

```yml
# Giscus
# https://giscus.app/
giscus:
  repo:
  repo_id:
  category_id:
  theme:
    light: light
    dark: dark
  option:

```

在主题配置选择 use: Giscus

```yml
comments:
  # Up to two comments system, the first will be shown as default
  # Leave it empty if you don't need comments
  # Choose: Disqus/Disqusjs/Livere/Gitalk/Valine/Waline/Utterances/Facebook Comments/Twikoo/Giscus/Remark42/Artalk
  # Format of two comments system : Disqus,Waline
  use:
    - Giscus 
  # Display the comment name next to the button
  text: true
  # Lazyload: The comment system will be load when comment element enters the browser's viewport.
  # If you set it to true, the comment count will be invalid
  lazyload: false
  # Display comment count in post's top_img
  count: false
  # Display comment count in Home Page
  card_post_count: false
```

注意检查你的主题配置是否有giscuss，如果有，就不要在根目录博客配置再写一遍，否则主题配置就会覆盖掉，表现为博客底部有评论二字但没有窗口。（被坑的真惨）