# Molecular Symmetry (分子对称性)

> 类型：概念 / 理论化学
> 学科/领域：群论、量子化学

## 定义 / Definition

分子对称性描述分子在某些操作（旋转、反射等）下保持不变的性质。利用对称性可显著减少计算成本。

## 对称操作 / Symmetry Operations

1. **E**: 恒等操作 (Identity)
2. **C_n**: n 重旋转 (Rotation)
3. **σ**: 镜面反射 (Reflection)
4. **i**: 反演 (Inversion)
5. **S_n**: 旋转反射 (Improper rotation)

## 点群 / Point Groups

### GAMESS 支持的常见点群

| 点群 | 对称性 | 典型分子 |
|------|--------|----------|
| C1 | 无对称 | CHFClBr, 手性分子 |
| Cs | 一个镜面 | HCl, CH2ClF |
| C2 | 2 重轴 | H2O2 (扭曲构型) |
| C2v | 2 重轴 + 2 垂直镜面 | H2O, SO2 |
| C3v | 3 重轴 + 3 垂直镜面 | NH3, CH3Cl |
| D2h | 3 个垂直 2 重轴 | 乙烯, C2H4 |
| D3h | 3 重轴 + 水平镜面 | BF3, CO3²⁻ |
| Td | 四面体 | CH4, CCl4 |
| Oh | 八面体 | SF6, [Fe(CN)6]³⁻ |

## $DATA 组中的对称性指定 / Symmetry in $DATA

### 基本格式

```gamess
 $DATA
Title
PointGroup

... (atoms)
 $END
```

### GAMESS 点群名称

| 标准 | GAMESS | 示例 |
|------|--------|------|
| C1 | C1 | 不对称分子 |
| Cs | CS | 平面分子 |
| C2v | CNV 2 | 水 |
| C3v | CNV 3 | 氨 |
| D2h | D2H | 乙烯 |
| Td | TD | 甲烷 |
| Oh | OH | SF6 |

### 无对称性计算

```gamess
 $DATA
Asymmetric molecule
C1

Atom1 Z x y z
Atom2 Z x y z
 $END
```

或使用 NOSYM:

```gamess
$CONTRL NOSYM=.TRUE. $END
```

## 对称性优势 / Symmetry Advantages

### 计算效率

利用对称性可减少：
- **积分计算**: 只计算独立积分
- **SCF 迭代**: 减少矩阵维度
- **频率计算**: 利用对称性块对角化

### 典型加速

| 分子 | 点群 | 加速比 |
|------|------|--------|
| H2O | C2v | ~2x |
| NH3 | C3v | ~3x |
| C6H6 | D2h | ~4x |
| CH4 | Td | ~12x |

## 对称性限制 / Symmetry Constraints

### 不可约表示

分子轨道按不可约表示分类：

- C2v: A1, A2, B1, B2
- C3v: A1, A2, E
- Td: A1, A2, E, T1, T2

### 态对称性

电子态由占据轨道的直积表示：

```
H2O 基态: ... (1a1)² (2a1)² (1b2)² (3a1)² (1b1)²
→ ¹A1
```

### 激发态对称性

激发态对称性由激发轨道决定：

```
b1 → a1 激发 → ¹B1 态
```

## 对称性破缺 / Symmetry Breaking

### Jahn-Teller 效应

简并电子态的几何畸变：

- **线性 Jahn-Teller**: e 态 → 畸变
- **二次 Jahn-Teller**: 近简并态畸变

### Peierls 畸变

共轭系统交替键长。

## 对称性与不可约表示 / Symmetry and IRRED

### 选择定则

跃迁允许性由直积决定：

```
Γ_initial ⊗ Γ_operator ⊗ Γ_final ⊃ A1
```

### 红外活性

偶极算子有 x, y, z 对称性。

### 拉曼活性

极化算子有 x², y², z², xy, xz, yz 对称性。

## 对称性匹配 / Symmetry Matching

### 反应对称性

反应物和产物的对称性应匹配：

```
A2 + B2 → C2v (保持)
```

### 轨道对称性

前线轨道理论中轨道对称性守恒。

## 常见问题 / Common Issues

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 对称性检测失败 | 几何不精确 | 优化几何，降低容差 |
| 错误的点群 | 错误指定 | 检查分子几何 |
| SCF 不收敛（高对称） | 简并轨道 | 降低对称性 |

## 计算示例 / Calculation Examples

### 高对称性分子

```gamess
! Methane (Td symmetry)
$CONTRL SCFTYP=RHF DFTTYP=B3LYP $END
$DATA
Methane
TD

C     6.0   0.000000   0.000000   0.000000
H     1.0   0.000000   0.000000   1.089000
H     1.0   1.026719   0.000000  -0.363000
H     1.0  -0.513360  -0.889165  -0.363000
H     1.0  -0.513360   0.889165  -0.363000
 $END
```

### 低对称性分子

```gamess
! Chlorofluoromethane (C1 symmetry)
$CONTRL SCFTYP=RHF DFTTYP=B3LYP NOSYM=.TRUE. $END
$DATA
CH2ClF
C1

C     6.0   0.000000   0.000000   0.000000
H     1.0   0.000000   0.000000   1.089000
H     1.0   1.026719   0.000000  -0.363000
Cl   17.0  -0.513360  -0.889165  -0.363000
F     9.0  -0.513360   0.889165  -0.363000
 $END
```

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Electronic_Structure_Methods]]
- [[Molecular_Orbitals]]

## 来源 / Sources

- `src/gamess_lsp/parser.py` - 对称性处理
- `raw/assets/examples/water_dft.inp` - 对称性示例
