# Frequency Calculation (频率计算)

> 类型：概念 / 计算化学方法
> 学科/领域：光谱学、热力学

## 定义 / Definition

频率计算通过计算 Hessian 矩阵（二阶能量导数）获得分子的振动频率，用于验证几何构型、计算热力学性质和模拟光谱。

## 计算设置 / Calculation Setup

### 分析方法

```gamess
$CONTRL RUNTYP=HESSIAN $END
$FORCE METHOD=ANALYTIC VIBANL=.TRUE. $END
```

### 优化后自动频率

```gamess
$CONTRL RUNTYP=OPTIMIZE $END
$STATPT NSTEP=50 HSSEND=.TRUE. $END
```

- **HSSEND=.TRUE.**: 优化完成后自动计算频率

## FORCE 组关键词

### METHOD (计算方法)

| 方法 | 描述 | 成本 | 精度 |
|------|------|------|------|
| ANALYTIC | 分析二阶导数 | 高 | 最高 |
| SEMIANALYTIC | 半解析 | 中 | 高 |
| FULLYNUMERIC | 完全数值 | 低 | 中 |

```gamess
$FORCE METHOD=ANALYTIC $END
```

### VIBANL (振动分析)

执行简正模式分析。

```gamess
$FORCE VIBANL=.TRUE. $END
```

### PURIFY (纯化)

从振动中移除平动和转动。

```gamess
$FORCE PURIFY=.TRUE. $END
```

### TEMP (温度)

热力学性质计算的温度。

```gamess
$FORCE TEMP=298.15 $END
```

### PRES (压力)

热力学性质计算的压力。

```gamess
$FORCE PRES=1.0 $END
```

## 频率解读 / Frequency Interpretation

### 实频 vs 虚频

| 频率类型 | 数学含义 | 物理含义 | 几何类型 |
|----------|----------|----------|----------|
| 实频 (ω² > 0) | 局部极小 | 稳定结构 | 稳定几何 |
| 虚频 (ω² < 0) | 一阶鞍点 | 过渡态 | 过渡态 |

### 频率单位换算

```
GAMESS 输出 (cm⁻¹) → 能量转换
E = h * c * ν̃

典型范围:
- X-H 伸缩: 2500-3500 cm⁻¹
- C=O 伸缩: 1600-1800 cm⁻¹
- C-C 伸缩: 1000-1300 cm⁻¹
- 变形模式: < 1000 cm⁻¹
```

## 热力学性质 / Thermodynamic Properties

频率计算输出包含：

### 电子能 + 零点能 (E + ZPE)
```
E_ZPE = E_elec + Σ(1/2 * h * ν_i)
```

### 焓 (H)
```
H = E + ZPE + H_trans + H_rot + H_vib
```

### Gibbs 自由能 (G)
```
G = H - T * S
  = E + ZPE + G_trans + G_rot + G_vib
```

### 熵 (S)
```
S = S_trans + S_rot + S_vib + S_elc
```

## 红外光谱模拟

### 红外强度

每个振动模式的红外强度从偶极矩导数计算。

### 谱图特征

- **峰位置**: 振动频率
- **峰强度**: 红外强度
- **峰形状**: 通常用 Lorentzian 或 Gaussian 展宽

### 同位素效应

重同位素降低振动频率（ν ∝ 1/√μ）：

```gamess
$DATA
Deuterated water
C1

D(D)    2.0   0.000000   0.757210  -0.469957
 $END
```

## 频率校正

### 标度因子

DFT 泛函系统性高估频率，需标度：

| 泛函 | 标度因子 | 温度范围 |
|------|----------|----------|
| B3LYP/6-31G(d) | 0.961 | 298 K |
| B3LYP/cc-pVTZ | 0.967 | 298 K |
| M06-2X | 0.97 | 298 K |

```gamess
$FORCE SCLFAC=0.961 $END
```

### 谐振校正

实际分子存在非谐性，可进行非谐分析：

```gamess
$VIB ANHALG=1 $END
```

## 计算流程示例

### 完整热力学计算

```gamess
! 1. 几何优化
$CONTRL RUNTYP=OPTIMIZE SCFTYP=RHF DFTTYP=B3LYP $END
$BASIS GBASIS=CC-PVDZ $END
$STATPT NSTEP=50 HSSEND=.TRUE. $END
```

频率自动在优化后计算，输出：
- 验证极小值（全实频）
- 零点能
- 热力学性质 (298.15 K, 1 atm)

### 振动频率标度

```
ν_scaled = ν_raw × scale_factor
```

### 热力学量计算

```
ΔH_rxn = Σ H_products - Σ H_reactants
ΔG_rxn = Σ G_products - Σ G_reactants
ΔS_rxn = Σ S_products - Σ S_reactants
```

## 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 虚频 | 未收敛到极小值 | 重新优化 |
| 低频虚频 (~10i) | 数值精度 | 使用更严格收敛 |
| 缺失频率 | 对称性过高 | 降低对称性 |

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Geometry_Optimization]]
- [[Calculation_Types]]
- [[Thermodynamics]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - FORCE, HESSIAN 关键词
- `raw/assets/examples/h2o_freq.inp` - 频率计算示例
