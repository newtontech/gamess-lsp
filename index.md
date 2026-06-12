# GAMESS-LSP LLM Wiki

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> Wiki 类型：Karpathy 风格 LLM Wiki

## Wiki 概述 / Wiki Overview

本 Wiki 采用 Andrej Karpathy 的 LLM Wiki 模式，将原始证据文件与衍生 Wiki 页面分离，为 GAMESS 量子化学域和 gamess-lsp 语言服务器提供结构化的知识库。

## 目录结构 / Directory Structure

```
gamess-lsp/
├── raw/              # 原始证据文件（只读）
│   └── assets/       # 源文件、文档、示例
├── wiki/             # LLM 维护的衍生页面
│   ├── entities/     # 实体页面（软件、组件等）
│   ├── concepts/     # 概念页面（跨领域概念）
│   └── synthesis/    # 综合页面（API 参考、目录）
├── index.md          # 本页面（导航中心）
└── log.md           # 更改日志
```

## 按主题浏览 / Browse by Topic

### GAMESS 软件基础

- [[GAMESS]] - GAMESS (US) 量子化学软件概述
- [[OpenQC]] - OpenQC 计算化学 LSP 生态系统

### LSP 服务器

- [[LSP_Server]] - Language Server Protocol 实现概述
- [[Diagnostic_Engine]] - 诊断引擎 v1 规范

### 量子化学概念

- [[Electronic_Structure_Methods]] - 电子结构方法（HF, DFT, MP2, CCSD）
- [[Basis_Sets]] - 基组（Pople, cc-pVXZ, ECP）
- [[Calculation_Types]] - 计算类型（ENERGY, OPTIMIZE, SADPOINT, IRC）
- [[Solvation_Models]] - 溶剂化模型（PCM, COSMO, SMD）
- [[Geometry_Optimization]] - 几何优化方法和策略
- [[Excited_States]] - 激发态计算（CIS, TD-DFT, EOM-CCSD）
- [[Transition_State_Search]] - 过渡态搜索和 IRC
- [[Frequency_Calculation]] - 振动频率和热力学
- [[DFT_Functionals]] - DFT 泛函（B3LYP, M06, ωB97X-D）
- [[SCF_Convergence]] - SCF 收敛和加速方法
- [[Molecular_Orbitals]] - 分子轨道理论
- [[Molecular_Symmetry]] - 分子对称性和点群
- [[Thermodynamics]] - 统计热力学

### 参考和指南

- [[GAMESS_Input_Syntax]] - 输入文件语法参考
- [[LSP_Capabilities]] - LSP 功能能力完整列表
- [[Diagnostics_Catalog]] - 诊断代码和错误消息目录
- [[Code_Snippets]] - 可用代码片段模板
- [[Best_Practices]] - GAMESS 计算最佳实践
- [[Troubleshooting]] - 故障排除指南
- [[Migration_Guide]] - 从其他软件迁移到 GAMESS

## 实体索引 / Entity Index

### 软件项目
- GAMESS - 量子化学软件包
- OpenQC - 计算化学 LSP 家族

### 组件
- LSP_Server - Language Server 实现
- Diagnostic_Engine - 诊断系统

## 概念索引 / Concept Index

### 理论方法
- Hartree-Fock (RHF, UHF, ROHF)
- DFT (B3LYP, PBE, M06)
- 后-HF (MP2, CCSD, CCSD(T))
- 多组态 (MCSCF, CASSCF)
- 激发态 (CIS, TD-DFT, EOM-CC)

### 计算类型
- 单点能 (ENERGY)
- 几何优化 (OPTIMIZE)
- 过渡态 (SADPOINT)
- IRC 反应路径 (IRC)
- 频率分析 (HESSIAN/FORCE)

### 技术细节
- 基组选择
- 溶剂模型
- 优化策略
- 收敛标准

## 综合索引 / Synthesis Index

### 参考文档
- GAMESS 输入语法
- LSP 能力
- 诊断目录
- 代码片段

### 工作流程
- 几何优化流程
- 频率计算流程
- 激发态计算流程
- 过渡态搜索流程

## 快速查找 / Quick Reference

### 常见问题

| 问题 | 参考页面 |
|------|----------|
| 如何设置 DFT 计算？ | [[Electronic_Structure_Methods]], [[DFT_Functionals]] |
| 选择哪个基组？ | [[Basis_Sets]] |
| 优化不收敛怎么办？ | [[Geometry_Optimization]], [[SCF_Convergence]] |
| 如何计算频率？ | [[Frequency_Calculation]] |
| 激发态用什么方法？ | [[Excited_States]] |
| 添加溶剂效应 | [[Solvation_Models]] |
| 选择 DFT 泛函 | [[DFT_Functionals]] |
| SCF 不收敛 | [[SCF_Convergence]], [[Troubleshooting]] |
| LSP 有哪些功能？ | [[LSP_Capabilities]] |
| 诊断错误含义 | [[Diagnostics_Catalog]] |
| 从 Gaussian 迁移 | [[Migration_Guide]] |

### 输入模板

- 水分子 DFT 优化: [[Code_Snippets]]
- MP2 能量: [[Code_Snippets]]
- 频率计算: [[Code_Snippets]]
- TD-DFT: [[Code_Snippets]]
- 过渡态: [[Code_Snippets]]

## 更改历史 / Change History

参见 `log.md` 获取详细的更改历史。

## 引用指南 / Citation Guide

所有 Wiki 页面包含：
- 来源文件引用（如 `raw/assets/README.md`）
- 相关页面链接（使用 `[[Page_Name]]` 格式）
- 不确定性标记（当信息不确定时）

## 贡献指南 / Contribution Guidelines

1. **添加原始文件**: 放入 `raw/assets/`
2. **更新 Wiki 页面**: 基于 raw 文件更新 wiki/ 下的页面
3. **更新 index.md**: 添加新页面链接
4. **记录到 log.md**: 添加更改条目

---

**Wiki 统计**:
- 实体页面: 4
- 概念页面: 13
- 综合页面: 7
- 总计: 24 页

**最后更新**: 2026-06-12
