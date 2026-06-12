# Basis Sets (基组)

> 类型：概念 / 量子化学
> 学科/领域：计算化学

## 定义 / Definition

基组是用于表示分子轨道的数学函数集合，通常是高斯函数的线性组合。基组的选择影响计算精度和成本。

## Pople 基组

### 最小基组
- **STO-3G**: Slater 型轨道用 3 个高斯拟合，最简单

### 分裂价键基组
- **3-21G**: 价键分为内层（2 个高斯）和外层（1 个高斯）
- **6-31G**: 6 个高斯用于内层，3 个用于内价键，1 个用于外价键
- **6-311G**: 三分裂价键，更精确

```gamess
$BASIS GBASIS=N31 NGAUSS=6 $END
```

### 极化基组
添加 d 轨道到非氢原子，f 轨道到重原子：
- **6-31G(d)** 或 **6-31G***
- **6-31G(d,p)** - 同时给氢加 p 轨道

```gamess
$BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
```

### 弥散基组
添加弥散函数，适用于阴离子、弱相互作用：
- **6-31+G(d)** - 对非氢加弥散
- **6-31++G(d,p)** - 对所有原子加弥散

```gamess
$BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 DIFFSP=.TRUE. DIFFS=.TRUE. $END
```

## Dunning 相关一致性基组

### cc-pVXZ 系列
- **cc-pVDZ** (双-zeta): 快速，初步研究
- **cc-pVTZ** (三-zeta): 平衡
- **cc-pVQZ** (四-zeta): 高精度
- **cc-pV5Z**: 接近完全基组极限

```gamess
$BASIS GBASIS=CC-PVDZ $END
```

### augmented 系列
添加弥散函数，适用于弱相互作用和激发态：
- **aug-cc-pVDZ**
- **aug-cc-pVTZ**

```gamess
$BASIS GBASIS=AUG-CC-PVDZ $END
```

## 有效核势 (ECP)

### 常见 ECP
- **LANL2DZ**: 对重原子使用 ECP，减少计算量
- **SBKJC**: Stevens-Basch-Krauss-Jasien-Cundari

```gamess
$ECP ECP=LANL2DZ $END
```

## 基组选择指南

| 系统 | 推荐基组 | 原因 |
|------|----------|------|
| 几何优化 | 6-31G(d) 或 cc-pVDZ | 平衡精度和速度 |
| 单点能 | cc-pVTZ 或更大 | 高精度 |
| 弱相互作用 | aug-cc-pVDZ++ | 需要弥散函数 |
| 过渡金属 | cc-pVTZ-PP + ECP | 处理相对论效应 |
| 大系统 | 6-31G(d) 或 3-21G | 计算成本限制 |

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Electronic_Structure_Methods]]
- [[Calculation_Types]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - BASIS 组关键词
- `raw/assets/examples/water_dft.inp` - 基组使用示例
