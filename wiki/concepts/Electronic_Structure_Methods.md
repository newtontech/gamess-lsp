# Electronic Structure Methods (电子结构方法)

> 类型：概念 / 量子化学理论
> 学科/领域：量子化学

## 定义 / Definition

电子结构方法是用于计算分子电子波函数和能量的量子力学方法。GAMESS 支持多种从头算 (ab initio) 和密度泛函理论 (DFT) 方法。

## Hartree-Fock 方法

### RHF (Restricted HF)
限制性 Hartree-Fock，适用于闭壳层系统（所有电子成对）。

```gamess
$CONTRL SCFTYP=RHF $END
```

### UHF (Unrestricted HF)
非限制性 Hartree-Fock，适用于开壳层系统（自由基、某些激发态）。

```gamess
$CONTRL SCFTYP=UHF MULT=2 $END
```

### ROHF (Restricted Open-shell HF)
限制性开壳层 Hartree-Fock，适用于开壳层但保持自旋纯态。

```gamess
$CONTRL SCFTYP=ROHF $END
```

## 密度泛函理论 (DFT)

### 常用泛函

| 泛函 | 类型 | 用途 |
|------|------|------|
| B3LYP | 杂化 GGA | 通用，分子几何和能量 |
| PBE | GGA | 固态和分子 |
| M06-2X | 杂化 meta-GGA | 热力学和非共价作用 |
| ωB97X-D | 长程校正 | 激发态、电荷转移 |

```gamess
$CONTRL DFTTYP=B3LYP $END
$DFT METHOD=GRID NRAD=96 NLEB=302 $END
```

## 后-Hartree-Fock 方法

### MP2 (Møller-Plesset 二阶微扰)
考虑电子相关，适用于弱相关系统。

```gamess
$CONTRL MPLEVL=2 $END
$MP2 $END
```

### CCSD (Coupled Cluster Singles and Doubles)
高精度相关方法，适用于小分子精确计算。

```gamess
$CONTRL CCTYP=CCSD $END
$CC MAXCC=50 CCCONV=1.0E-06 $END
```

### CCSD(T)
加上三重微扰的 CCSD，"化学金标准"。

```gamess
$CONTRL CCTYP=CCSD(T) $END
```

## 多组态方法 (MCSCF)

### CASSCF (Complete Active Space SC)
适用于静态相关重要的情况（键断裂、激发态）。

```gamess
$CONTRL SCFTYP=MCSCF $END
$MCSCF CISTEP=ALDET $END
```

## 激发态方法

### CIS (Configuration Interaction Singles)
最简单的激发态方法，适用于低激发态。

```gamess
$CONTRL CITYP=CIS $END
$CIS NSTATE=5 $END
```

### TD-DFT (Time-Dependent DFT)
DFT 框架下的激发态计算，性价比高。

```gamess
$CONTRL TDDFT=EXCITE $END
$TDDFT NSTATE=10 $END
```

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Basis_Sets]]
- [[Calculation_Types]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - 完整的关键词数据库
- `raw/assets/examples/` - 各种方法示例
