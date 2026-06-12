# Thermodynamics (热力学)

> 类型：概念 / 物理化学
> 学科/领域：计算化学、统计热力学

## 定义 / Definition

统计热力学将分子的量子力学性质（振动频率、转动惯量、电子能级）与宏观热力学量（焓、熵、自由能）联系起来。

## 热力学量 / Thermodynamic Quantities

### 基本关系

```
G = H - T*S
H = E + PV
E = E_elec + E_ZPE + E_vib + E_rot + E_trans
```

### 零点能 (Zero-Point Energy, ZPE)

绝对零度时振动能：

```
E_ZPE = Σ(1/2 * h * ν_i)
```

其中 ν_i 是振动频率。

### 焓 (Enthalpy, H)

```
H = E_elec + E_ZPE + H_trans + H_rot + H_vib
```

### 熵 (Entropy, S)

```
S = S_trans + S_rot + S_vib + S_elc
```

### Gibbs 自由能 (Gibbs Free Energy, G)

```
G = H - T*S
```

## 分子贡献 / Molecular Contributions

### 平动 (Translational)

理想气体平动贡献：

```
S_trans = R * [3/2 * ln(M) + 5/2 * ln(T) - ln(P) - 1.164]
```

其中 M 是分子质量，T 是温度，P 是压力。

### 转动 (Rotational)

线性分子：

```
S_rot = R * [ln(T/σθ_rot) + 1]
```

非线性分子：

```
S_rot = R * [1/2 * ln(π I_A I_B I_C) + 3/2 * ln(T) - ln(σ) - 1.5]
```

其中 I 是转动惯量，σ 是对称数。

### 振动 (Vibrational)

每个振动模式：

```
S_vib,i = R * [x/(exp(x)-1) - ln(1-exp(-x))]
```

其中 `x = hν/kT`。

### 电子 (Electronic)

基态非简并：

```
S_elc = R * ln(g_0)
```

其中 g_0 是基态简并度。

## GAMESS 热力学输出

### 频率计算输出

```
ZERO POINT ENERGY = 0.0XXXXXX hartree
THERMAL ENERGY    = 0.0XXXXXX hartree
ENTHALPY          = 0.0XXXXXX hartree
GIBBS FREE ENERGY = 0.0XXXXXX hartree
```

### 温度依赖性

温度设置：

```gamess
$FORCE TEMP=298.15 PRES=1.0 $END
```

常见温度：
- 298.15 K (25°C, 标准条件)
- 273.15 K (0°C)
- 373.15 K (100°C)

## 反应热力学 / Reaction Thermodynamics

### 反应焓变

```
ΔH_rxn = Σ H_products - Σ H_reactants
```

### 反应熵变

```
ΔS_rxn = Σ S_products - Σ S_reactants
```

### 反应自由能变

```
ΔG_rxn = Σ G_products - Σ G_reactants
```

### 平衡常数

```
K_eq = exp(-ΔG_rxn / RT)
```

## 计算流程 / Calculation Workflow

### 1. 几何优化和频率

```gamess
$CONTRL RUNTYP=OPTIMIZE SCFTYP=RHF DFTTYP=B3LYP $END
$BASIS GBASIS=CC-PVDZ $END
$STATPT NSTEP=50 HSSEND=.TRUE. $END
$FORCE METHOD=ANALYTIC VIBANL=.TRUE. TEMP=298.15 $END
```

### 2. 提取热力学量

从输出文件提取：
- E + ZPE
- 焓 (H)
- 熵 (S)
- Gibbs 自由能 (G)

### 3. 计算反应量

对反应物和产物重复上述步骤，计算差值。

## 溶剂化热力学 / Solvation Thermodynamics

### 溶剂化自由能

```
ΔG_sol = G_solution - G_gas
```

### PCM 热力学

```gamess
$PCM SOLVNT=WATER $END
$FORCE TEMP=298.15 $END
```

## 准确性考虑 / Accuracy Considerations

### 误差来源

1. **频率标度因子**: DFT 系统性高估频率
2. **简谐近似**: 忽略非谐性
3. **理想气体假设**: 忽略分子间作用
4. **刚性转子近似**: 忽略离心变形

### 标度因子

| 泛函/基组 | 标度因子 |
|-----------|----------|
| B3LYP/6-31G(d) | 0.9613 |
| B3LYP/cc-pVTZ | 0.967 |
| M06-2X | 0.97 |

### 高级方法

- VPT2 (二阶微摄振动理论)
- 非谐频率计算（GAMESS 支持）

## 应用场景 / Applications

- **反应能量学**: 反应焓、活化能
- **平衡常数**: K_eq, K_a, K_b
- **相变**: 蒸发焓、升华焓
- **溶剂效应**: 溶剂化能
- **温度效应**: 热容、温度依赖性质

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Frequency_Calculation]]
- [[Geometry_Optimization]]
- [[Solvation_Models]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - FORCE 组热力学关键词
- `raw/assets/examples/h2o_freq.inp` - 频率/热力学示例
