# Geometry Optimization (几何优化)

> 类型：概念 / 计算化学方法
> 学科/领域：量子化学

## 定义 / Definition

几何优化是寻找分子能量最小值对应构型的过程，通过调整原子坐标使能量和梯度最小化。

## 优化设置 / Optimization Setup

### 基本优化

```gamess
$CONTRL RUNTYP=OPTIMIZE SCFTYP=RHF DFTTYP=B3LYP $END
$BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
$STATPT OPTTOL=0.0001 NSTEP=50 $END
```

## STATPT 组选项

### METHOD (优化方法)

| 方法 | 描述 | 适用场景 |
|------|------|----------|
| RFO | 有理函数优化 | 通用，默认 |
| QA | 二次近似 | 简单系统 |
| GDIIS | 几何微分外推 | 接近收敛时 |
| CONOPT | 约束优化 | 有约束的优化 |
| SCHLEGEL | Schlegel 方法 | 过渡态 |
| EF | Euler 预测-校正 | 简单势能面 |

```gamess
$STATPT METHOD=RFO $END
```

### OPTTOL (收敛容差)

梯度最大元素的收敛阈值。

```gamess
$STATPT OPTTOL=0.0001 $END
```

- 默认: 0.0001 Hartree/Bohr
- 更严格: 0.00001 (高精度)
- 更宽松: 0.001 (快速预研)

### NSTEP (最大步数)

优化停止的最大迭代次数。

```gamess
$STATPT NSTEP=50 $END
```

- 默认: 50
- 大分子: 100-200
- 困难优化: 更大

### HESS (Hessian 来源)

指定 Hessian 矩阵的获取方式。

```gamess
$STATPT HESS=GUESS $END
```

- **GUESS**: 对角猜测（默认）
- **CALC**: 初始步计算
- **READ**: 从文件读取

### HSSEND (优化后计算 Hessian)

优化完成后进行频率计算。

```gamess
$STATPT HSSEND=.TRUE. $END
```

用途：验证极小值（全实频）或过渡态（一个虚频）。

## 优化策略

### 1. 预优化 → 精细优化

先用小基组快速预优化，再用大基组精确优化：

```gamess
! 第一步：小基组预优化
$CONTRL RUNTYP=OPTIMIZE DFTTYP=B3LYP $END
$BASIS GBASIS=STO NGAUSS=3 $END
$STATPT NSTEP=30 $END
```

```gamess
! 第二步：大基组精细优化（使用预优化几何）
$CONTRL RUNTYP=OPTIMIZE DFTTYP=B3LYP $END
$BASIS GBASIS=CC-PVTZ $END
$STATPT NSTEP=50 $END
$DATA
... (使用第一步优化的坐标)
```

### 2. 收敛困难处理

#### 增加 SCF 收敛帮助

```gamess
$SCF DIIS=.TRUE. SOSCF=.TRUE. CONV=1.0E-06 $END
```

#### 调整信任半径

```gamess
$STATPT TRMAX=0.3 TRMIN=0.05 $END
```

#### 使用更鲁棒的优化器

```gamess
$STATPT METHOD=CONOPT $END
```

### 3. 约束优化

虽然 GAMESS 本身不直接支持约束优化，可以通过修改 $DATA 或使用特定方法实现。

## 优化收敛标准

默认标准 (OPTTOL=0.0001)：
1. 最大梯度 < 0.0001 Hartree/Bohr
2. 位移变化足够小
3. 能量变化足够小

## 优化失败排查

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| SCF 不收敛 | 初始猜测差 | 改变 GUESS，增加 MAXIT |
| 优化震荡 | 势能面复杂 | 改变 METHOD，减小 TRMAX |
| 步数用尽 | 构型远离极小值 | 预优化，增加 NSTEP |
| 虚频 | 鞍点而非极小值 | 沿虚频模式位移 |

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Calculation_Types]]
- [[Transition_State_Search]]
- [[Frequency_Calculation]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - STATPT 组关键词
- `raw/assets/examples/water_dft.inp` - 几何优化示例
