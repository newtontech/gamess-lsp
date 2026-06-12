# GAMESS (US)

> 类型：软件 / 量子化学程序
> 创建日期：2026-06-12
> 来源数：3

## 简介 / Introduction

GAMESS (US) 是 **General Atomic and Molecular Electronic Structure System** 的缩写，是一个广泛使用的量子化学软件包，由爱荷华州立大学的 Gordon 研究小组开发。它提供从头算 (ab initio) 电子结构计算、分子动力学模拟、光谱模拟等功能。

## 关键属性 / Key Attributes

- **开发者**: 爱荷华州立大学 Gordon 研究小组
- **许可**: 学术免费，商业需许可
- **语言**: Fortran 主要，部分 C
- **平台**: Linux, macOS, Windows (通过 WSL)
- **并行**: 支持 MPI 并行计算
- **输入格式**: 基于 `$` 组的关键词-值对格式

## 输入文件格式 / Input File Format

GAMESS 输入文件 (`.inp`) 采用结构化的 `$GROUP` 格式：

```gamess
! Water molecule DFT calculation
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END
 $SYSTEM MWORDS=100 $END
 $BASIS GBASIS=CC-PVDZ $END
 $DATA
Water molecule
Cnv 2

O     8.0   0.000000   0.000000   0.117489
H     1.0   0.000000   0.757210  -0.469957
 $END
```

## 支持的计算方法 / Supported Methods

- **Hartree-Fock**: RHF, UHF, ROHF
- **DFT**: B3LYP, PBE, M06 系列, ωB97 系列
- **后-HF**: MP2, MP3, MP4, CCSD, CCSD(T)
- **多组态方法**: MCSCF, CASSCF, RASSCF
- **激发态**: CIS, TD-DFT, EOM-CC
- **相对论**: DKH, ZORA

## 支持的性质计算 / Supported Properties

- 几何优化和过渡态搜索
- 振动频率和热力学
- 分子轨道分析
- NBO 分析
- 溶剂效应 (PCM, COSMO, SMD)
- 激发态和光谱

## 相关来源 / Related Sources

- `raw/assets/README.md` - 项目概述和功能
- `raw/assets/examples/water_dft.inp` - 水分子 DFT 优化示例
- `src/gamess_lsp/keywords.py` - 完整的关键词数据库

## 相关实体/概念 / Related Entities/Concepts

- [[LSP_Server]]
- [[Electronic_Structure_Methods]]
- [[Basis_Sets]]
- [[Solvation_Models]]

## 历史更新 / History

- 2026-06-12: 创建 GAMESS 实体页面
