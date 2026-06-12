# Excited States (激发态)

> 类型：概念 / 量子化学
> 学科/领域：光化学、光谱学

## 定义 / Definition

激发态是分子吸收能量后电子占据更高能级的量子态。GAMESS 提供多种激发态计算方法。

## CIS (Configuration Interaction Singles)

最简单的激发态方法，适用于小分子和定性研究。

### 基本设置

```gamess
$CONTRL SCFTYP=RHF CITYP=CIS $END
$CIS NSTATE=5 IROOT=1 MULT=1 $END
```

### 关键词

- **NSTATE**: 计算的激发态数量
- **IROOT**: 目标态（用于性质计算）
- **MULT**: 多重度 (1=单态, 3=三态)
- **DIAG**: 对角化方法 (FULL, DAVIDSON)

### 优缺点

- **优点**: 快速，简单
- **缺点**: 低精度，忽略双激发，高估激发能

## TD-DFT (Time-Dependent DFT)

性价比高的激发态方法，适用于中等大小分子。

### 基本设置

```gamess
$CONTRL SCFTYP=RHF DFTTYP=B3LYP TDDFT=EXCITE $END
$TDDFT NSTATE=10 IROOT=1 MAXVEC=100 CVG=1.0E-05 $END
```

### 关键词

- **NSTATE**: 激发态数量
- **IROOT**: 性质计算目标态
- **MULT**: 多重度
- **MAXVEC**: 展开向量最大数
- **CVG**: 收敛标准

### 泛函选择

| 泛函 | 适用场景 |
|------|----------|
| B3LYP | 通用，价态激发 |
| CAM-B3LYP | 电荷转移激发 |
| ωB97X-D | 长程校正， Rydberg 态 |
| M06-2X | 精确能量 |

### 优缺点

- **优点**: 不错精度，可处理中等分子
- **缺点**: 传统泛函低估电荷转移能

## EOM-CCSD (Equation-of-Motion CC)

高精度激发态方法，适用于小分子精确计算。

```gamess
$CONTRL CCTYP=CCSD $END
$CIS NSTATE=5 $END
```

### 特点

- 高精度，包含电子相关
- 计算昂贵
- 适用于小分子基准计算

## 激发态性质

### 振子强度

表示跃迁强度，决定吸收光谱强度。

### 激发能

垂直激发能（Franck-Condon 原理）：

```
E_exc = E_excited - E_ground
```

### 态特性

- 单态 (Singlet): 总自旋 S=0
- 三态 (Triplet): 总自旋 S=1
- 允许跃迁: ΔS=0, Δl=±1
- 禁阻跃迁: ΔS≠0

## 激发态工作流程

### 1. 基态优化
```gamess
$CONTRL RUNTYP=OPTIMIZE SCFTYP=RHF DFTTYP=B3LYP $END
$BASIS GBASIS=CC-PVDZ $END
$STATPT NSTEP=50 $END
```

### 2. 基态频率验证
```gamess
$CONTRL RUNTYP=HESSIAN $END
$FORCE METHOD=ANALYTIC VIBANL=.TRUE. $END
```

### 3. 激发态计算
```gamess
$CONTRL SCFTYP=RHF DFTTYP=B3LYP TDDFT=EXCITE $END
$TDDFT NSTATE=10 $END
```

### 4. 激发态优化（可选）
```gamess
$CONTRL SCFTYP=RHF CITYP=CIS $END
$CIS NSTATE=5 IROOT=1 $END
$STATPT NSTEP=50 $END
```

## 应用场景

- **紫外-可见光谱**: 模拟吸收光谱
- **光化学反应**: 研究光解、异构化
- **荧光和磷光**: 辐射跃迁过程
- **电荷转移**: 给体-受体系统
- **材料科学**: 有机电子材料设计

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Electronic_Structure_Methods]]
- [[Calculation_Types]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - CIS, TDDFT 关键词
- `raw/assets/examples/tddft_excited.inp` - TD-DFT 示例
