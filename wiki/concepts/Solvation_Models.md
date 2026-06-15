# Solvation Models (溶剂化模型)

> 类型：概念 / 量子化学
> 学科/领域：溶液化学

## 定义 / Definition

溶剂化模型用于模拟溶剂对溶质分子的影响，避免昂贵的显式溶剂分子模拟。GAMESS 支持多种隐式溶剂模型。

## PCM (Polarizable Continuum Model)

极化连续介质模型，最常用的隐式溶剂模型。

### 基本用法

```gamess
$PCM SOLVNT=WATER $END
```

### 支持的溶剂

- WATER (水)
- CH2CL2 (二氯甲烷)
- THF (四氢呋喃)
- ACETONE (丙酮)
- DMSO (二甲基亚砜)
- DMF (二甲基甲酰胺)
- ACETONITRILE (乙腈)
- METHANOL (甲醇)
- ETHANOL (乙醇)

### 高级选项

```gamess
$PCM SOLVNT=WATER ICAV=0 EPS=78.4 RSOLV=1.0 $END
```

- **ICAV**: 空腔类型 (0=GePol, 1=UFF, 2=Pierotti)
- **EPS**: 介电常数（覆盖溶剂默认值）
- **RSOLV**: 探针半径 (Å)

## COSMO (Conductor-like Screening Model)

导体类屏蔽模型，适用于高介电常数溶剂。

```gamess
$COSM EPS=1.0 RSOLV=1.3 DISPT=1 $END
```

- **EPS**: 介电常数（默认无穷大）
- **RSOLV**: 探针半径 (Å)
- **DISPT**: 色散校正 (0=无, 1=DFT-D3)

## SMD (Solvation Model based on Density)

基于密度的溶剂化模型，包含非静电贡献。

```gamess
$SMD SOLVNT=WATER ICAV=0 $END
```

### 支持的溶剂

- WATER, ETHANOL, HEXANE, BENZENE
- TOLUENE, CH2CL2, THF, ACETONE
- 以及更多有机溶剂

## 溶剂模型选择

| 模型 | 适用场景 | 优点 | 缺点 |
|------|----------|------|------|
| PCM | 通用溶液计算 | 广泛验证 | 对非极性溶剂可能过度极化 |
| COSMO | 高介电常数溶剂 | 快速 | 对低介电常数溶剂不准确 |
| SMD | 有机溶剂/中性分子 | 包含非静电项 | 参数化较新 |

## 溶剂模型结合计算

### 几何优化
```gamess
$CONTRL DFTTYP=B3LYP RUNTYP=OPTIMIZE $END
$PCM SOLVNT=WATER $END
$STATPT OPTTOL=0.0001 $END
```

### 频率计算
```gamess
$CONTRL RUNTYP=HESSIAN $END
$FORCE METHOD=ANALYTIC $END
$PCM SOLVNT=WATER $END
```

### 激发态
```gamess
$CONTRL TDDFT=EXCITE $END
$TDDFT NSTATE=5 $END
$PCM SOLVNT=WATER $END
```

## 溶剂化能计算

计算溶剂化自由能：

```
ΔG_sol = G_solution - G_gas

1. 气相几何优化和频率 → G_gas
2. 溶剂相单点能 → G_solution
```

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Electronic_Structure_Methods]]
- [[Calculation_Types]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - PCM, COSMO, SMD 关键词
## Raw evidence

- raw/assets/examples/water_dft.inp
