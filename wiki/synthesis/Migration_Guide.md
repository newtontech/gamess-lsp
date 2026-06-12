# Migration Guide (迁移指南)

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> 覆盖来源：2

## 核心论点 / Core Arguments

从其他量子化学软件迁移到 GAMESS，或在不同 GAMESS 版本间迁移，需要了解输入文件差异。

## 从 Gaussian 到 GAMESS / From Gaussian to GAMESS

### 基本差异

| 特性 | Gaussian | GAMESS |
|------|----------|--------|
| 输入结构 | `#` 方法/基组 | `$CONTRL` 组 |
| 几何部分 | `molecule` 部分 | `$DATA` 组 |
| 注释 | `!` 开头 | `!` 开头（兼容） |
| 内存 | `%mem=` | `$SYSTEM MWORDS=` |
| 方法指定 | `# B3LYP/6-31G(d)` | `$CONTRL DFTTYP=B3LYP` |

### 输入文件转换

#### Gaussian 示例

```bash
# B3LYP/6-31G(d) Opt

0 1
O  0.0  0.0  0.1175
H  0.0  0.7572  -0.4700
H  0.0  -0.7572  -0.4700
```

#### GAMESS 等效

```gamess
! B3LYP/6-31G(d) optimization
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END
 $BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
 $DATA
Water
Cnv 2

O     8.0   0.000000   0.000000   0.117489
H     1.0   0.000000   0.757210  -0.469957
 $END
```

### 方法映射

| Gaussian | GAMESS |
|----------|--------|
| `HF` | `SCFTYP=RHF` |
| `B3LYP` | `DFTTYP=B3LYP` |
| `MP2` | `MPLEVL=2` |
| `CCSD(T)` | `CCTYP=CCSD(T)` |
| `Opt` | `RUNTYP=OPTIMIZE` |
| `Freq` | `RUNTYP=HESSIAN` |

### 基组映射

| Gaussian | GAMESS |
|----------|--------|
| `6-31G(d)` | `GBASIS=N31 NGAUSS=6 NDFUNC=1` |
| `6-31+G(d,p)` | `GBASIS=N31 NGAUSS=6 NDFUNC=1 DIFFSP=.TRUE.` |
| `cc-pVDZ` | `GBASIS=CC-PVDZ` |
| `aug-cc-pVDZ` | `GBASIS=AUG-CC-PVDZ` |

## 从 ORCA 到 GAMESS / From ORCA to GAMESS

### 输入结构差异

#### ORCA 示例

```bash
! B3LYP def2-SVP Opt

* xyz 0 1
O 0.0 0.0 0.1175
H 0.0 0.7572 -0.4700
H 0.0 -0.7572 -0.4700
*
```

#### GAMESS 等效

```gamess
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END
 $BASIS GBASIS=DEF2-SVP $END
 $DATA
Water
C1

O 8.0 0.0 0.0 0.1175
H 1.0 0.0 0.7572 -0.4700
H 1.0 0.0 -0.7572 -0.4700
 $END
```

## GAMESS 版本差异 / GAMESS Version Differences

### 主要版本

- **GAMESS (US)**: 爱荷华州立大学版本
- **GAMESS-UK**: 英国版本（不同软件）

### 输入兼容性

大多数 GAMESS (US) 输入在不同子版本间兼容。

## 特殊功能迁移 / Special Features

### PCM 溶剂

#### Gaussian
```bash
# SCRF=(PCM,Solvent=Water)
```

#### GAMESS
```gamess
$PCM SOLVNT=WATER $END
```

### 频率计算

#### Gaussian
```bash
# Freq
```

#### GAMESS
```gamess
$CONTRL RUNTYP=HESSIAN $END
$FORCE METHOD=ANALYTIC $END
```

### 激发态

#### Gaussian
```bash
# TD(NStates=10)
```

#### GAMESS
```gamess
$CONTRL TDDFT=EXCITE $END
$TDDFT NSTATE=10 $END
```

## 输出文件差异 / Output File Differences

### Gaussian 输出

- `.log` 文件包含所有信息
- `.chk` 文件包含二进制数据

### GAMESS 输出

- `.log` 或 `.out` 文件
- `.dat` 辅助文件
- `.rst` 重启文件

## 关键词转换工具 / Keyword Conversion Tools

### 常用转换

1. **电荷和自旋**: Gaussian 需要单独行，GAMESS 在 `$CONTRL` 中
2. **坐标**: Gaussian 使用 Cartesian 或内坐标，GAMESS `$DATA` 使用特定格式
3. **内存**: Gaussian `%mem=`, GAMESS `MWORDS=`

### 自动转换

考虑编写脚本进行自动转换，特别是对于:
- 几何部分
- 方法/基组规范
- 计算类型

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[GAMESS_Input_Syntax]]
- [[Best_Practices]]

## 来源列表 / Source List

- `raw/assets/README.md` - 功能概述
- `src/gamess_lsp/keywords.py` - 关键词参考
