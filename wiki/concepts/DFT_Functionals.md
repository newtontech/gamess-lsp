# DFT Functionals (DFT 泛函)

> 类型：概念 / 密度泛函理论
> 学科/领域：计算化学

## 定义 / Definition

密度泛函理论 (DFT) 中的交换-相关泛函近似处理电子间的交换和相关作用。选择合适的泛函对计算结果至关重要。

## 泛函分类 / Functional Classes

### 1. LDA (Local Density Approximation)

**SVWN**: Slater-Vosko-Wilk-Nusair

- 最简单的泛函
- 适用于均匀电子气
- 对分子系统表现较差

```gamess
$CONTRL DFTTYP=SVWN $END
```

### 2. GGA (Generalized Gradient Approximation)

**纯 GGA**:
- **PBE**: Perdew-Burke-Ernzerhof，通用
- **BLYP**: Becke-Lee-Yang-Parr，有机分子

```gamess
$CONTRL DFTTYP=PBE $END
```

### 3. 杂化泛函 (Hybrid)

混合精确交换和 DFT 交换：

**B3LYP** (Becke-3-Lee-Yang-Parr):
```
E_xc = 0.2 E_x^HF + 0.8 E_x^B88 + 0.19 E_c^VWN + 0.81 E_c^LYP
```

**最常用的泛函**，适用于:
- 分子几何
- 振动频率
- 热力学

```gamess
$CONTRL DFTTYP=B3LYP $END
```

**PBE0** (PBE-0):
```
E_xc = 0.25 E_x^HF + 0.75 E_x^PBE + E_c^PBE
```

**M06 系列**:
- **M06**: 通用
- **M06-L**: 纯 DFT（无精确交换）
- **M06-2X**: 高非动态相关，22% 精确交换
- **M06-HF**: 高动态相关，100% 精确交换

```gamess
$CONTRL DFTTYP=M062X $END
```

### 4. meta-GGA

包含动能密度：

**TPSS**: Tao-Perdew-Staroverov-Scuseria

**M06-L**: meta-GGA 版本

### 5. 双杂化泛函 (Double Hybrid)

包含 MP2 型相关：

**B2PLYP**: Becke-2-parameter-LYP

```gamess
$CONTRL DFTTYP=B2PLYP $END
```

### 6. 范围分离泛函 (Range-Separated)

长程和短程使用不同处理：

**ωB97X-D**: ωB97 色散校正
- 适用于激发态
- 适用于电荷转移
- 包含经验色散

**CAM-B3LYP**: Coulomb-attenuated B3LYP
- 适用于电荷转移激发态

```gamess
$CONTRL DFTTYP=WB97X $END
$DFT LAMBDA=0.3 $END
```

## 泛函选择指南 / Functional Selection Guide

| 任务 | 推荐泛函 | 原因 |
|------|----------|------|
| 通用几何 | B3LYP | 平衡，广泛验证 |
| 热力学 | M06-2X | 高精度 |
| 弱相互作用 | B3LYP-D3, M06-2X | 色散处理 |
| 激发态 | CAM-B3LYP, ωB97X-D | 长程校正 |
| 电荷转移 | ωB97X-D | 范围分离 |
| 轨道能量 | M06-2X, ωB97X-D | 更准确 |
| 大系统 | PBE, BLYP | 快速 |
| 过渡金属 | M06-L, TPSSH | 金属处理 |

## 色散校正 / Dispersion Corrections

### DFT-D3

Grimme D3 色散校正：

```gamess
$DFT ... $END
```

某些泛函内置色散：
- **B3LYP-D3**
- **ωB97X-D**

### 经验色散

GAMESS 支持各种色散方案。

## DFT 网格设置 / DFT Grid Settings

### 网格密度

```gamess
$DFT
 NRAD=96
 NLEB=302
$END
```

- **NRAD**: 径向点数（默认 96）
- **NLEB**: Lebedev 角点数（默认 302）

### 网格质量

| 质量 | NRAD | NLEB | 应用 |
|------|------|------|------|
| 粗糙 | 64 | 194 | 预研 |
| 标准 | 96 | 302 | 默认 |
| 精细 | 128 | 590 | 高精度 |
| 很精细 | 150 | 1202 | 精确热力学 |

### 网格方法

```gamess
$DFT METHOD=GRID $END
```

- **GRID**: 标准数值积分
- **GRIDFREE**: 无网格方法（特定泛函）

## 泛函精度比较 / Functional Accuracy

### 基准测试结果

**B3LYP/6-31G(d)**:
- 几何: 平均误差 ~0.01 Å
- 频率: 平均误差 ~30 cm⁻¹（标度后）
- 能量: 平均误差 ~3-5 kcal/mol

**M06-2X/cc-pVTZ**:
- 几何: 平均误差 ~0.008 Å
- 频率: 平均误差 ~20 cm⁻¹
- 能量: 平均误差 ~2 kcal/mol

**ωB97X-D/aug-cc-pVTZ**:
- 激发能: 平均误差 ~0.2 eV
- 电荷转移: 改善显著

## 泛函的局限性 / Functional Limitations

### B3LYP 局限

- 低估电荷转移能
- 低估反应能垒
- 不适合色散主导系统

### M06-2X 局限

- 较高的计算成本（54% 精确交换）
- 可能过高束缚弱相互作用

### 泛函依赖性

不同泛函可能给出显著不同的结果：
- 关键反应应测试多个泛函
- 与实验或高级理论对比

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Electronic_Structure_Methods]]
- [[Excited_States]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - DFT 组关键词
