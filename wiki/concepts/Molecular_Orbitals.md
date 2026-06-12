# Molecular Orbitals (分子轨道)

> 类型：概念 / 量子化学
> 学科/领域：分子轨道理论

## 定义 / Definition

分子轨道 (MO) 是原子轨道的线性组合，描述分子中电子的空间分布和能量。GAMESS 提供多种分子轨道分析和可视化选项。

## LCAO-MO 理论 / LCAO-MO Theory

线性组合原子轨道-分子轨道 (LCAO-MO):

```
ψ_i = Σ c_μi φ_μ
```

其中 ψ_i 是分子轨道，φ_μ 是原子轨道基函数，c_μi 是展开系数。

## MO 计算 / MO Calculation

### SCF 过程

1. **初始猜测**: Hückel 或核心 Hamiltonian
2. **Fock 矩阵构建**: 包括电子相关
3. **对角化**: 获得 MO 能量和系数
4. **密度矩阵**: 由占据 MO 构建
5. **迭代**: 自洽场收敛

### GUESS 组

初始猜测类型：

```gamess
$GUESS GUESS=HUCKEL $END
```

**选项**:
- **HUCKEL**: Hückel 猜测（默认）
- **CORE**: 核心 Hamiltonian
- **MOREAD**: 从文件读取 MO
- **SKIP**: 跳过猜测，从现有开始

## MO 对称性 / MO Symmetry

### 不可约表示

MO 按分子点群的不可约表示分类：

**H2O (C2v)**:
- a1: σ 成键，孤对
- b1: p_x 轨道
- b2: σ 成键
- a2: 非键（通常空）

### 占据规则

**Aufbau 原理**:
1. 从最低能级开始填充
2. 每个轨道最多 2 电子
3. 遵循 Hund 规则

**RHF**:
- 所有轨道双占据
- 闭壳层

**UHF**:
- α 和 β 轨道不同
- 开壳层

## MO 分析 / MO Analysis

### 轨道能量

输出示例：

```
EIGENVECTORS AND EIGENVALUES
     1    -20.123456   2    -1.234567   3    -0.765432
...
```

### 轨道系数

展开系数 c_μi：

```
1          2          3          4
 0.987654  -0.123456   0.012345  -0.004321
...
```

### 布居分析

Mulliken 布居：

```
ATOMIC POPULATIONS
  O   6.234567  2.345678  0.123456
  H   0.543210  0.432109
```

## 高级 MO 方法 / Advanced MO Methods

### 自然轨道 (NBO)

自然键轨道分析：

```gamess
$NBO NBO=FULL NPA=.TRUE. $END
```

输出：
- 自然键轨道
- 自然布居分析
- Wiberg 键级

### 定域轨道 (Localized)

Pipek-Mezey 或 Boys 定域：

```gamess
$LOCAL $END
```

或：

```gamess
$PMO $END
```

### CASSCF 轨道

多组态 SCF 的活性空间：

```gamess
$CONTRL SCFTYP=MCSCF $END
$MCSCF CISTEP=ALDET $END
$DRT
...
 $END
```

## MO 可视化 / MO Visualization

### 轨道输出

```gamess
$GUESS PRTMO=.TRUE. $END
```

生成可用于可视化的文件：
- 轨道系数
- 轨道能量
- 对称性标记

### 外部可视化

GAMESS 输出可被：
- **Molden**: 读取 MO 并可视化
- **MacMolPlt**: GAMESS 官方可视化
- **GaussView**: 兼容部分格式

## 前线轨道理论 / Frontier Orbital Theory

### HOMO/LUMO

- **HOMO** (Highest Occupied MO): 最高占据分子轨道
- **LUMO** (Lowest Unoccupied MO): 最低未占据分子轨道

### 应用

1. **化学反应性**:
   - 亲核试剂攻击 LUMO
   - 亲电试剂攻击 HOMO

2. **光谱性质**:
   - HOMO-LUMO 间隙 ≈ 激发能
   - 电离势 ≈ -E_HOMO
   - 电子亲和势 ≈ -E_LUMO

3. **电荷转移**:
   - 给体 HOMO 能量高
   - 受体 LUMO 能量低

## MO 读取和写入 / MO I/O

### 读取 MO

```gamess
$GUESS GUESS=MOREAD $END
$VEC
... (MO coefficients)
 $END
```

### 写入 MO

自动在 $PUNCH 文件中保存 MO。

### MO 重启

用于：
- 几何优化重启
- 激发态计算
- 轨道分析

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Electronic_Structure_Methods]]
- [[Molecular_Symmetry]]
- [[Excited_States]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - GUESS, VEC 组关键词
