# Troubleshooting Guide (故障排除指南)

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> 覆盖来源：2

## 核心论点 / Core Approach

系统性诊断 GAMESS 计算问题，从输入验证到计算调整。

## SCF 收敛问题 / SCF Convergence

### 症状

```
CONVERGENCE NOT REACHED
```

### 原因和解决方案

#### 1. 初始猜测差

**症状**: 前几次迭代能量剧烈波动

**解决方案**:
```gamess
$GUESS GUESS=HUCKEL $END
```

或尝试:
```gamess
$GUESS GUESS=CORE $END
```

#### 2. 收敛标准太严

**症状**: 能量稳定但未达到标准

**解决方案**:
```gamess
$SCF CONV=1.0E-05 $END
```

放宽到 1.0E-05 或 1.0E-04

#### 3. 需要更激进的收敛加速

**解决方案**:
```gamess
$SCF DIIS=.TRUE. SOSCF=.TRUE. $END
```

或:
```gamess
$SCF DIRSCF=.TRUE. $END
```

#### 4. 开壳层系统

**症状**: RHF 不收敛

**解决方案**:
```gamess
$CONTRL SCFTYP=UHF MULT=2 $END
```

#### 5. 增加 SCF 迭代

**解决方案**:
```gamess
$CONTRL MAXIT=100 $END
```

### SCF 收敛层次

1. **DIIS**: 默认，适用于大多数情况
2. **SOSCF**: 更激进，适用于困难情况
3. **DIRSCF**: 直接 SCF，最慢但最稳定
4. **阻尼**: 通过 `GUESS=DAMP`

## 几何优化失败 / Geometry Optimization Failure

### 症状

```
OPTIMIZATION DID NOT CONVERGE
```

或 `NSTEP` 用尽

### 原因和解决方案

#### 1. 初始几何太差

**解决方案**:
- 用分子预优化器（如 Avogadro）
- 从简单基组开始

#### 2. 势能面复杂

**解决方案**:
```gamess
$STATPT METHOD=CONOPT $END
```

或:
```gamess
$STATPT TRMAX=0.15 TRMIN=0.02 $END
```

#### 3. 内存不足

**解决方案**:
```gamess
$SYSTEM MWORDS=1000 $END
```

#### 4. 对称性问题

**解决方案**:
```gamess
$CONTRL NOSYM=.TRUE. $END
```

#### 5. 最大步数不足

**解决方案**:
```gamess
$STATPT NSTEP=100 $END
```

### 优化策略

1. **预优化**: 小基组快速优化
2. **标准优化**: 中等基组
3. **精细优化**: 大基组，严格收敛

## 频率计算问题 / Frequency Issues

### 症状

多个虚频或意外的虚频

### 原因和解决方案

#### 1. 优化未收敛

**解决方案**: 重新优化，使用更严格标准
```gamess
$STATPT OPTTOL=0.00001 $END
```

#### 2. 不是真正的极小值

**解决方案**: 沿虚频模式位移并重新优化

#### 3. 数值精度问题

**解决方案**: 使用分析方法
```gamess
$FORCE METHOD=ANALYTIC $END
```

#### 4. 平面分子/低频模式

**解决方案**: 可能需要更高质量基组

## 内存问题 / Memory Issues

### 症状

```
INSUFFICIENT MEMORY
```

或分段错误

### 解决方案

#### 1. 增加内存分配

```gamess
$SYSTEM MWORDS=2000 $END
```

#### 2. 减少基组大小

从 cc-pVQZ 改为 cc-pVTZ

#### 3. 使用直接 SCF

```gamess
$SCF DIRSCF=.TRUE. $END
```

## 并行计算问题 / Parallel Issues

### 症状

并行效率低或崩溃

### 解决方案

#### 1. 调整并行设置

```gamess
$SYSTEM KDIAG=0 $END
```

#### 2. 检查 MPI 设置

确保正确设置进程数

## 输入文件错误 / Input File Errors

### 常见错误

#### 1. 未闭合的组

```
ERROR: GROUP $CONTRL NOT CLOSED
```

**解决方案**: 添加 `$END`

#### 2. 未知的组

```
WARNING: UNKNOWN GROUP $CONTROL
```

**解决方案**: 检查拼写，应为 `$CONTRL`

#### 3. 无效的值

```
ERROR: INVALID VALUE FOR SCFTYP
```

**解决方案**: 使用有效值列表中的值

#### 4. 缺少 $DATA

```
ERROR: NO $DATA GROUP
```

**解决方案**: 添加包含分子几何的 `$DATA` 组

## 结果解释问题 / Result Interpretation

### 1. 能量异常

**检查**:
- 单位（Hartree vs kcal/mol）
- 零点能是否包含
- 基组一致性

### 2. 几何异常

**检查**:
- 是否收敛到极小值（频率）
- 对称性是否合理
- 与实验/文献对比

### 3. 频率异常

**检查**:
- 是否需要标度因子
- 是否有虚频（过渡态）
- 低频模式是否合理

## 调试技巧 / Debugging Tips

### 1. 使用 EXETYP=CHECK

```gamess
$CONTRL EXETYP=CHECK $END
```

检查输入而不运行

### 2. 增加输出详细度

```gamess
$CONTRL ... $END
```

查看更多调试信息

### 3. 简化问题

- 减小分子
- 使用更小基组
- 降低理论级别

### 4. 逐步验证

1. 单点能
2. 几何优化
3. 频率
4. 更高级别计算

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Geometry_Optimization]]
- [[Frequency_Calculation]]
- [[Best_Practices]]

## 来源列表 / Source List

- `src/gamess_lsp/keywords.py` - 关键词参考
- `docs/DIAGNOSTIC_ENGINE_V1.md` - 诊断信息
## Raw evidence

- raw/assets/agent-verification-loop.md
