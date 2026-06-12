# Calculation Types (计算类型)

> 类型：概念 / GAMESS 输入
> 学科/领域：量子化学计算

## 定义 / Definition

GAMESS 中的 RUNTYP 关键词指定要执行的 calculations 类型，决定了程序要完成的任务。

## 主要计算类型 / Main Calculation Types

### ENERGY (单点能计算)
默认类型，计算给定几何构型下的电子能量。

```gamess
$CONTRL RUNTYP=ENERGY $END
```

用途：
- 获得精确单点能（在高水平方法下）
- 势能面扫描
- 作为后续计算的基础

### OPTIMIZE (几何优化)
寻找能量最小值对应的几何构型。

```gamess
$CONTRL RUNTYP=OPTIMIZE $END
$STATPT OPTTOL=0.0001 NSTEP=50 $END
```

用途：
- 获得稳定分子几何
- 反应物和产物优化
- 配合物构型搜索

### GRADIENT (能量梯度)
计算一阶导数（力）。

```gamess
$CONTRL RUNTYP=GRADIENT $END
```

用途：
- 验证优化收敛
- 分子动力学输入
- IRC/DRC 计算准备

### HESSIAN (二阶导数)
计算力常数矩阵。

```gamess
$CONTRL RUNTYP=HESSIAN $END
$HESSIAN METHOD=ANALYTIC $END
```

用途：
- 频率分析准备
- 优化算法输入
- 反应路径研究

### SADPOINT (过渡态搜索)
寻找一阶鞍点（过渡态）。

```gamess
$CONTRL RUNTYP=SADPOINT $END
$STATPT METHOD=RFO $END
```

用途：
- 反应机理研究
- 活化能计算
- 反应路径验证

### IRC (内禀反应坐标)
从过渡态向反应物和产物方向跟踪反应路径。

```gamess
$CONTRL RUNTYP=IRC $END
$IRC METHOD=RFO NPOINT=100 $END
```

用途：
- 验证过渡态连接
- 获得反应路径细节
- 研究反应动力学

### DRC (动力学反应坐标)
经典轨迹模拟，研究分子在势能面上的运动。

```gamess
$CONTRL RUNTYP=DRC $END
$DRC TINIT=298.15 NSTEP=1000 $END
```

用途：
- 反应动力学研究
- 能量弛豫过程
- 碰撞动力学

### SURFACE (势能面扫描)
沿坐标扫描势能面。

```gamess
$CONTRL RUNTYP=SURFACE $END
$SURFACE NVIB=1 NSURF=10 $END
```

用途：
- 构象搜索
- 势能面探索
- 反应路径初步研究

## 频率计算 / Frequency Calculations

频率计算验证优化是极小值（全部实频）还是过渡态（一个虚频）：

```gamess
$CONTRL RUNTYP=HESIAN $END
$FORCE METHOD=ANALYTIC VIBANL=.TRUE. $END
```

或结合优化自动计算：

```gamess
$CONTRL RUNTYP=OPTIMIZE $END
$STATPT HSSEND=.TRUE. $END
```

## 计算类型选择流程

```
需要研究？
├─ 静态性质 → ENERGY
├─ 稳定几何 → OPTIMIZE → FREQUENCY
├─ 过渡态 → SADPOINT → IRC + FREQUENCY
├─ 反应路径 → IRC
└─ 动力学 → DRC
```

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Electronic_Structure_Methods]]
- [[Geometry_Optimization]]
- [[Excited_States]]

## 来源 / Sources

- `src/gamess_lsp/keywords.py` - RUNTYP 定义
- `raw/assets/examples/` - 各种计算类型示例
