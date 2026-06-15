# SCF Convergence (SCF 收敛)

> 类型：概念 / 计算方法
> 学科/领域：量子化学计算

## 定义 / Definition

自洽场 (SCF) 收敛是迭代求解 Hartree-Fock 或 Kohn-Sham 方程直到能量和密度矩阵稳定的过程。

## SCF 过程 / SCF Process

### 基本步骤

1. **初始猜测**: 构建初始密度矩阵
2. **Fock 矩阵**: 基于当前密度构建
3. **对角化**: 得到新轨道和能量
4. **密度更新**: 从新轨道构建新密度
5. **收敛检查**: 能量/密度变化
6. **重复**: 直到收敛或达到最大迭代

### 收敛判据

```gamess
$SCF CONV=1.0E-05 $END
```

能量变化阈值（默认 1.0E-05）。

## 收敛加速方法 / Convergence Acceleration

### 1. DIIS (Direct Inversion in Iterative Subspace)

**原理**: 使用前几次迭代的外推

```gamess
$SCF DIIS=.TRUE. $END
```

**适用**: 大多数情况，默认开启

**缺点**: 有时会导致振荡

### 2. SOSCF (Second-Order SCF)

**原理**: 使用二阶优化

```gamess
$SCF SOSCF=.TRUE. $END
```

**适用**: 接近收敛时加速

**优点**: 快速收敛到高精度

**缺点**: 早期迭代可能不稳定

### 3. 阻尼 (Damping)

**原理**: 混合新旧密度

```gamess
$GUESS GUESS=DAMP $END
```

**适用**: 振荡情况

### 4. 电平移 (Level Shifting)

移动虚拟轨道能级以防止占据-虚拟混合。

### 5. 直接 SCF (DIRSCF)

**原理**: 每次迭代重新计算积分

```gamess
$SCF DIRSCF=.TRUE. $END
```

**适用**: 内存有限，大分子

**缺点**: 慢

## 收敛问题诊断 / Convergence Issues

### 症状 1: 能量振荡

**表现**: 能量上下波动

**原因**: DIIS 外推不稳定

**解决方案**:
```gamess
$SCF DIIS=.FALSE. $END
```

或尝试 SOSCF:
```gamess
$SCF SOSCF=.TRUE. $END
```

### 症状 2: 能量单调但不收敛

**表现**: 能量持续变化但很慢

**原因**: 收敛标准太严或势能面复杂

**解决方案**:
1. 放宽收敛标准:
```gamess
$SCF CONV=1.0E-04 $END
```

2. 增加最大迭代:
```gamess
$CONTRL MAXIT=100 $END
```

### 症状 3: SCF 崩溃

**表现**: 能量发散到无穷大

**原因**: 初始猜测太差或系统有问题

**解决方案**:
1. 更好的初始猜测:
```gamess
$GUESS GUESS=HUCKEL $END
```

2. 尝试不同 SCF 类型:
```gamess
$CONTRL SCFTYP=UHF MULT=2 $END
```

## 高级技巧 / Advanced Techniques

### 1. 分步填充

逐个填充电子，适用于困难系统。

### 2. 占据-虚拟混合抑制

通过电平移或直接 SCF 抑制混合。

### 3. 自适应阻尼

自动调整阻尼因子。

### 4. 开壳层系统

```gamess
$CONTRL SCFTYP=UHF MULT=2 $END
$SCF DIRSCF=.TRUE. $END
```

### 5. 自旋污染检查

UHF 计算检查 `<S²>` 值。

## SCF 输出解释 / SCF Output Interpretation

### 标准输出

```
ITER   EXCHANGE    COULOMB      POTENTIAL    TOTAL ENERGY    CHANGE
   1   -12.3456    23.4567      11.1111      -75.123456
   2   -12.3789    23.4901      11.1222      -75.124567   -0.001111
...
CONVERGED
```

### 关键指标

- **CHANGE**: 能量变化，应趋向 0
- **DENSITY CHANGE**: 密度矩阵变化
- **<S²>**: 自旋平方（UHF），理想值 S(S+1)

## SCF 参数调优 / SCF Parameter Tuning

### 标准设置

```gamess
$SCF
 DIRSCF=.FALSE.
 DIIS=.TRUE.
 SOSCF=.FALSE.
 CONV=1.0E-05
$END
```

### 困难系统

```gamess
$SCF
 DIRSCF=.TRUE.
 DIIS=.FALSE.
 SOSCF=.TRUE.
 CONV=1.0E-04
$END
```

### 极困难系统

```gamess
$SCF
 DIRSCF=.TRUE.
 DIIS=.FALSE.
 CONV=1.0E-04
$END
$CONTRL MAXIT=200 $END
```

## 特殊情况 / Special Cases

### 1. 双自由基

可能需要多重态平均或 MCSCF。

### 2. 过渡金属

考虑:
- 高自旋 vs 低自旋
- 多参考特征
- 相对论效应

### 3. 阴离子

需要:
- 弥散函数
- 更好的初始猜测

### 4. 激发态

使用:
- CIS/TD-DFT
- 特定态 SCF
- ΔSCF

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Electronic_Structure_Methods]]
- [[Molecular_Orbitals]]
- [[Troubleshooting]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - SCF, CONTRL 组关键词
- `docs/DIAGNOSTIC_ENGINE_V1.md` - 诊断信息
## Raw evidence

- raw/assets/examples/water_dft.inp
