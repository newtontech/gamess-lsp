# OpenQC

> 类型：项目 / 生态系统
> 创建日期：2026-06-12
> 来源数：2

## 简介 / Introduction

OpenQC 是 newtontech 计算化学 LSP 家族，提供多个量子化学软件的语言服务器支持。`gamess-lsp` 是其中的 GAMESS (US) 语言服务器实现。

## OpenQC-VSCode 对齐 / Alignment

gamess-lsp 作为独立的 GAMESS 语言服务器，需要与 newtontech/OpenQC-VSCode 扩展保持语言行为一致。

### 需要对齐的功能

- **文件扩展名处理**: `.inp` GAMESS 文件
- **诊断**: 未知组、未闭合部分、必需关键词
- **代码片段**: 常见 GAMESS 计算的代码片段行为
- **完成和悬停**: `$` 组和关键词的词汇
- **解析器固件**: 用于冒烟测试的最小解析器

### 发布检查

在公开 OpenQC 发布之前，对该服务器和扩展分别对一个有效和一个无效的 GAMESS 输入进行冒烟测试。

## OpenQC 家族 / OpenQC Family

计算化学 LSP 家族包括：
- gamess-lsp (GAMESS-US)
- (其他量子化学软件 LSP 实现)

## 相关来源 / Related Sources

- `docs/OPENQC_ALIGNMENT.md` - 对齐规范
- `raw/assets/README.md` - 项目概述

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[LSP_Server]]

## 历史更新 / History

- 2026-06-12: 创建 OpenQC 实体页面
