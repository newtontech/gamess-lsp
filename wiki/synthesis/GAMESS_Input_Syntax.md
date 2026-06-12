# GAMESS Input Syntax Reference (GAMESS 输入语法参考)

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> 覆盖来源：3

## 核心论点 / Core Arguments

GAMESS 输入文件采用结构化的 `$GROUP` 关键词-值对格式，理解其语法规则是正确设置计算的基础。

## 基本结构 / Basic Structure

### 文件组成

```gamess
! 注释行（可选）

 $GROUP1 KEY1=VALUE1 KEY2=VALUE2 $END
 $GROUP2 KEY1=VALUE1 $END
 $DATA
Title
Symmetry

Atom1 Z x y z
Atom2 Z x y z
 $END
```

### 语法规则

1. **注释**: 以 `!` 开头
2. **组**: 以 `$` 开头，`$END` 结尾
3. **关键词**: `KEY=VALUE` 格式
4. **大小写**: 关键词和组名不区分大小写
5. **空格**: 关键词、值和 `=` 之间可有空格

## $DATA 组语法

### 基本格式

```gamess
 $DATA
Title (comment line, ignored)
PointGroup (symmetry specification)
 (blank line)

AtomSymbol  Z  x  y  z
AtomSymbol  Z  x  y  z
...
 $END
```

### 点群指定

| 点群 | GAMESS 名称 |
|------|-------------|
| C1 | C1 |
| Cs | CS |
| C2 | C2 |
| C2v | CNV 2 |
| C3v | CNV 3 |
| D2h | D2H |
| 等等 | ... |

### 坐标格式

```gamess
O  8.0  0.000000  0.000000  0.117489
H  1.0  0.000000  0.757210  -0.469957
```

- **列 1**: 元素符号
- **列 2**: 原子序数 (Z)
- **列 3-5**: x, y, z 坐标 (默认 Bohr)

## 常见组语法 / Common Group Syntax

### $CONTRL (必需)

```gamess
$CONTRL
 SCFTYP=RHF
 DFTTYP=B3LYP
 RUNTYP=OPTIMIZE
 MULT=1
$END
```

### $SYSTEM

```gamess
$SYSTEM
 MWORDS=100
 TIMLIM=10000
$END
```

### $BASIS

```gamess
$BASIS
 GBASIS=CC-PVDZ
 NDFUNC=1
 DIFFSP=.TRUE.
$END
```

### $STATPT

```gamess
$STATPT
 METHOD=RFO
 OPTTOL=0.0001
 NSTEP=50
$END
```

## 逻辑关键词 / Logical Keywords

### 布尔值设置

```gamess
KEY=.TRUE.   ! 启用
KEY=.FALSE.  ! 禁用
KEY=1        ! 启用 (数值)
KEY=0        ! 禁用 (数值)
```

### 常用布尔关键词

| 关键词 | 含义 | 默认值 |
|--------|------|--------|
| DIIS | SCF 加速收敛 | .TRUE. |
| NOSYM | 禁用对称性 | .FALSE. |
| HSSEND | 优化后频率 | .FALSE. |

## 数值关键词 / Numerical Keywords

### 整数

```gamess
MULT=1       ! 自旋多重度
NSTATE=10    ! 激发态数量
NSTEP=50     ! 最大迭代次数
```

### 浮点数

```gamess
OPTTOL=0.0001    ! 收敛容差
TEMP=298.15      ! 温度
CONV=1.0E-06     ! SCF 收敛标准
```

### 科学计数法

```gamess
CONV=1.0E-05
ETHRSH=0.5
DFTTHR=1.0E-11
```

## 字符串关键词 / String Keywords

### 方法指定

```gamess
SCFTYP=RHF
DFTTYP=B3LYP
GBASIS=CC-PVDZ
SOLVNT=WATER
```

## 多值关键词 / Multiple Values

### 列表

某些关键词可接受多个值（较少见）：

```gamess
! 示例：多个模式（概念上）
MODES=ALL
```

## 条件语法 / Conditional Syntax

### 组的存在即启用

```gamess
! 启用 MP2
$CONTRL MPLEVL=2 $END
$MP2 $END
```

```gamess
! 不启用 MP2
$CONTRL MPLEVL=0 $END
! 无 $MP2 组
```

### 方法间互斥

某些计算类型和方法组合互斥：
- CCTYP 需要 MPLEVL=0
- MCSCF 需要 SCFTYP=MCSCF

## 输入文件示例 / Complete Examples

### 最小输入（单点能）

```gamess
$CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
$BASIS GBASIS=STO NGAUSS=3 $END
$DATA
Water
C1

O  8.0  0.0  0.0  0.117489
H  1.0  0.0  0.757210  -0.469957
H  1.0  0.0  -0.757210  -0.469957
 $END
```

### 完整 DFT 优化

```gamess
! Water DFT optimization
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END
 $SYSTEM MWORDS=100 $END
 $BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
 $SCF DIIS=.TRUE. CONV=1.0E-05 $END
 $STATPT OPTTOL=0.0001 NSTEP=50 $END
 $DATA
Water molecule optimization
Cnv 2

O     8.0   0.000000   0.000000   0.117489
H     1.0   0.000000   0.757210  -0.469957
 $END
```

## 常见语法错误 / Common Syntax Errors

| 错误 | 原因 | 修正 |
|------|------|------|
| 未知的组 | 组名拼写错误 | 检查组名 |
| 未闭合的组 | 缺少 $END | 添加 $END |
| 无效的值 | 值不在允许列表中 | 检查有效值 |
| 缺失必需关键词 | 组不完整 | 添加缺失关键词 |

## 来源列表 / Source List

- `raw/assets/README.md` - 语法概述
- `src/gamess_lsp/keywords.py` - 完整语法数据库
- `raw/assets/examples/` - 语法示例
