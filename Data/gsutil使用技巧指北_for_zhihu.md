---
title: gsutil使用技巧指北
date: 2025-11-29 08:50:08
categories: 工具
tags:
  - 闲谈
cover: /img/cover_26.jpg
abbrlink: 1253334338
description: 记录一下使用gsutil下载
---

## 认证

```bash
gcloud auth login
```

用自己google账号生成的凭证即可

## 下载

```bash
gsutil -m cp -n -r gs://waymo_open_dataset_motion_v_1_3_1/uncompressed/tf_example/training/* training/
```

| 命令         | 作用                       | 解释                              |

| ------------ | -------------------------- | --------------------------------- |

| `gsutil cp`  | 执行文件复制（下载）操作。 | 基础功能。                        |

| **`-m`**     | **多线程/多进程**。        | **速度快**，处理故障能力强。      |

| **`-n`**     | **不覆盖** (No-clobber)。  | **实现续传**，跳过已完成的文件。  |

| `-r`         | 递归复制。                 | 确保处理目录和所有文件。          |

| `gs://.../*` | 云端（GCS）源路径。        | 指定 Waymo 训练数据集的所有文件。 |

| `training/`  | 本地目标路径。             | 指定下载文件存放的本地目录。      |


可以安装crcmod进一步加速

```bash
pip install crcmod
```



