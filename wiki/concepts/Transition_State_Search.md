# Transition State Search (过渡态搜索)

> 类型：概念 / 计算化学方法
> 学科/领域：反应动力学

## 定义 / Definition

过渡态 (TS) 是反应势能面上的一阶鞍点，连接反应物和产物，对应反应能垒。过渡态搜索是确定反应机理的关键步骤。

## SADPOINT (鞍点搜索)

GAMESS 的 RUNTYP=SADPOINT 用于寻找过渡态。

### 基本设置

```gamess
$CONTRL RUNTYP=SADPOINT SCFTYP=RHF DFTTYP=B3LYP $END
$STATPT METHOD=RFO IFOLOW=1 NSTEP=50 $END
```

### STATPT 关键词

- **METHOD**: 优化算法 (RFO, QA, GDIIS, SCHLEGEL)
- **IFOLOW**: 跟踪的模式（负振动模式）
- **OPTTOL**: 收敛容差
- **NSTEP**: 最大步数
- **HESS**: Hessian 来源

## 过渡态搜索策略

### 1. 初猜结构准备

好的初猜对过渡态搜索至关重要：

**方法 A: 反应物/产物线性插值**
```
R  ---TS_guess---  P
```
在反应物和产物之间插值

**方法 B: 同步跃迁**
同时形成/断裂键的几何

**方法 C: 化学直觉**
基于类似反应的已知过渡态

### 2. 从初猜到过渡态

```gamess
$CONTRL RUNTYP=SADPOINT SCFTYP=RHF DFTTYP=B3LYP $END
$BASIS GBASIS=CC-PVDZ $END
$STATPT METHOD=RFO IFOLOW=1 NSTEP=100 OPTTOL=0.0001 $END
$DATA
Transition state guess
C1

... (初猜坐标)
 $END
```

### 3. 频率验证

过渡态应有且仅有一个虚频（负频率）：

```gamess
$CONTRL RUNTYP=HESSIAN $END
$FORCE METHOD=ANALYTIC VIBANL=.TRUE. $END
```

**验证标准**：
- 一个虚频 (imaginary frequency)
- 虚频模式对应反应坐标
- 力常数矩阵有一个负特征值

## IRC (Intrinsic Reaction Coordinate)

验证过渡态确实连接预期的反应物和产物。

### IRC 设置

```gamess
$CONTRL RUNTYP=IRC $END
$IRC METHOD=RFO FORWRD=.TRUE. NPOINT=50 STRIDE=0.1 $END
```

### IRC 关键词

- **METHOD**: 跟踪方法 (RFO, TRUST, EULER, LQA)
- **FORWRD**: 向前/向后跟踪
- **NPOINT**: IRC 点数
- **STRIDE**: 步长 (amu^(1/2) * Bohr)

### IRC 分析

1. **向前 IRC**: 从 TS 向产物方向
2. **向后 IRC**: 从 TS 向反应物方向
3. **能量图**: 绘制势能剖面
4. **几何变化**: 观察键长/键角变化

## 常见问题及解决

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 无虚频 | 搜索到极小值 | 改变初猜，增加 IFOLOW |
| 多个虚频 | 复杂势能面 | 选择不同模式，优化初猜 |
| 收敛困难 | 势能面复杂 | 增加 NSTEP，改变 METHOD |
| IRC 不连接 | TS 错误 | 重新搜索 TS |

## 活化能计算

### 经典能垒
```
Ea = E_TS - E_reactant
```

### Gibbs 自由能垒
```
ΔG‡ = G_TS - G_reactant
```

需要 TS 和反应物的频率计算以获得热力学校正。

## 反应速率 (Eyring 方程)

```
k = (k_B T / h) * exp(-ΔG‡ / RT)
```

- k_B: Boltzmann 常数
- h: Planck 常数
- R: 气体常数
- T: 温度

## 计算流程示例

```gamess
! 1. 反应物优化
$CONTRL RUNTYP=OPTIMIZE DFTTYP=B3LYP $END
$BASIS GBASIS=CC-PVDZ $END
$STATPT NSTEP=50 HSSEND=.TRUE. $END
```

```gamess
! 2. 过渡态搜索
$CONTRL RUNTYP=SADPOINT DFTTYP=B3LYP $END
$STATPT METHOD=RFO IFOLOW=1 NSTEP=100 $END
```

```gamess
! 3. TS 频率
$CONTRL RUNTYP=HESSIAN $END
$FORCE METHOD=ANALYTIC $END
```

```gamess
! 4. IRC 验证
$CONTRL RUNTYP=IRC $END
$IRC METHOD=RFO NPOINT=50 $END
```

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Geometry_Optimization]]
- [[Calculation_Types]]
- [[Frequency_Calculation]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - SADPOINT, IRC 关键词
- `raw/assets/examples/irc_reaction.inp` - IRC 示例
