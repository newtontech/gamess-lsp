# GAMESS Calculation Best Practices (GAMESS 计算最佳实践)

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> 覆盖来源：3

## 核心论点 / Core Principles

遵循最佳实践可以确保计算效率、结果可靠性和可重现性。

## 计算设计 / Calculation Design

### 1. 明确目标

| 目标 | 推荐方法 | 基组 | 精度 |
|------|----------|------|------|
| 快速预研 | HF/3-21G | 3-21G | 低 |
| 标准几何优化 | DFT/B3LYP | 6-31G(d) | 中 |
| 高精度能量 | CCSD(T) | cc-pVTZ | 高 |
| 弱相互作用 | DFT-D3 | aug-cc-pVDZ | 中-高 |
| 激发态 | TD-DFT | cc-pVDZ | 中 |

### 2. 分层策略

```
低成本方法 + 小基组
    ↓
中等成本方法 + 中基组
    ↓
高成本方法 + 大基组
```

**示例**:
1. HF/3-21G 预优化
2. DFT/6-31G(d) 优化
3. DFT/cc-pVTZ 单点能
4. CCSD(T)/cc-pVTZ 校正（如需要）

## 几何优化 / Geometry Optimization

### 收敛标准

```gamess
$STATPT OPTTOL=0.0001 NSTEP=50 $END
```

- **预研**: OPTTOL=0.001
- **标准**: OPTTOL=0.0001
- **高精度**: OPTTOL=0.00001

### SCF 收敛

```gamess
$SCF DIIS=.TRUE. SOSCF=.TRUE. CONV=1.0E-06 $END
```

### 优化失败处理

1. **增加迭代**: `NSTEP=100`
2. **改变方法**: `METHOD=CONOPT`
3. **使用更好的初始猜测**
4. **降低对称性**: `NOSYM=.TRUE.`

## 基组选择 / Basis Set Selection

### 层级策略

1. **预研**: STO-3G, 3-21G
2. **标准**: 6-31G(d), cc-pVDZ
3. **高质量**: 6-311+G(d,p), cc-pVTZ
4. **基准**: cc-pVQZ, aug-cc-pVQZ

### 特殊情况

| 系统 | 推荐基组 | 原因 |
|------|----------|------|
| 阴离子 | aug-cc-pVDZ++ | 需要弥散函数 |
| 弱相互作用 | aug-cc-pVDZ | 色散需要弥散 |
| 过渡金属 | cc-pVTZ-PP + ECP | 相对论效应 |
| 大分子 | 6-31G(d) | 计算成本 |

## 方法选择 / Method Selection

### DFT 泛函选择

| 任务 | 泛函 | 原因 |
|------|------|------|
| 通用 | B3LYP | 平衡 |
| 热力学 | M06-2X | 高精度 |
| 电荷转移 | CAM-B3LYP | 长程校正 |
| 激发态 | ωB97X-D | 精确 |
| 固态 | PBE | 周期系统 |

### 后-HF 方法

| 精度 | 方法 | 成本 |
|------|------|------|
| 低-中 | MP2 | 中 |
| 中 | CCSD | 高 |
| 高 | CCSD(T) | 很高 |

## 频率计算 / Frequency Calculation

### 何时计算

**必须**:
- 几何优化后验证极小值
- 过渡态后验证鞍点
- 热力学量

**可选**:
- 光谱模拟
- 同位素效应

### 设置

```gamess
$CONTRL RUNTYP=HESSIAN $END
$FORCE METHOD=ANALYTIC VIBANL=.TRUE. TEMP=298.15 $END
```

### 标度因子

```gamess
$FORCE SCLFAC=0.967 $END
```

## 溶剂效应 / Solvent Effects

### 何时使用

- 溶液相反应
- 生物系统
- 极性环境

### 模型选择

| 溶剂 | 模型 | 原因 |
|------|------|------|
| 水 | PCM | 通用 |
| 有机 | SMD | 参数化广泛 |
| 界面 | COSMO | 介质 |

## 并行计算 / Parallel Computing

### 内存设置

```gamess
$SYSTEM MWORDS=1000 $END
```

- **小型**: 100-500 MWORDS
- **中型**: 500-2000 MWORDS
- **大型**: 2000+ MWORDS

### 时间限制

```gamess
$SYSTEM TIMLIM=10000 $END
```

## 输入文件组织 / Input File Organization

### 注释

```gamess
! Water molecule optimization
! Method: B3LYP/6-31G(d)
! Date: 2026-06-12
```

### 顺序

1. 控制组 ($CONTRL)
2. 系统组 ($SYSTEM)
3. 基组 ($BASIS)
4. SCF 组 ($SCF)
5. 方法组 (DFT, MP2, 等)
6. 任务组 (STATPT, FORCE, 等)
7. 数据组 ($DATA)

### 可读性

```gamess
! 推荐
$CONTRL
 SCFTYP=RHF
 DFTTYP=B3LYP
 RUNTYP=OPTIMIZE
$END

! 不推荐（单行）
$CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END
```

## 验证和测试 / Validation and Testing

### 已知系统

先用已知分子测试：
- 水: H2O 键长 ~0.96 Å
- 甲烷: C-H 键长 ~1.09 Å
- 苯: C-C 键长 ~1.40 Å

### 收敛性检验

增加基组大小直到能量收敛 < 1 kcal/mol。

### 方法比较

用更高精度方法验证 DFT 结果。

## 常见错误 / Common Mistakes

| 错误 | 后果 | 修正 |
|------|--------|------|
| 频率显示虚频 | 可能不是极小值 | 重新优化 |
| 忘记弥散函数 | 阴离子/弱相互作用差 | 添加 + 或 ++ |
| 错误的多重度 | 错误电子态 | 检查电子数 |
| 过高的收敛标准 | 不必要的时间 | 使用合理标准 |
| 跳过频率验证 | 未知结构类型 | 始终验证 |

## 计算记录 / Documentation

### 输入文件命名

```
molecule_method_basis.inp
water_b3lyp_6-31gd.inp
ts_saddle_b3lyp_ccpvdz.inp
```

### 实验记录

- 方法、基组、软件版本
- 计算日期
- 机器规格
- 收敛信息
- 关键结果

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Geometry_Optimization]]
- [[Frequency_Calculation]]
- [[Thermodynamics]]

## 来源列表 / Source List

- `raw/assets/README.md` - 功能概述
- `src/gamess_lsp/keywords.py` - 完整关键词参考
- `raw/assets/examples/` - 实践示例
