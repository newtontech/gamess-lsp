# Code Snippets (代码片段)

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> 覆盖来源：2

## 核心论点 / Core Arguments

gamess-lsp 提供代码片段功能，快速插入常见计算模板，减少输入工作量。

## 可用代码片段 / Available Snippets

### 1. 水分子 (water)

完整的水分子 B3LYP/6-31G(d) 几何优化。

```gamess
! Water molecule DFT optimization
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END
 $SYSTEM MWORDS=100 $END
 $BASIS GBASIS=N31 NGAUSS=6 NDFUNC=1 $END
 $STATPT OPTTOL=0.0001 NSTEP=50 $END
 $DATA
Water molecule
Cnv 2

O     8.0   0.000000   0.000000   0.117489
H     1.0   0.000000   0.757210  -0.469957
 $END
```

**触发**: 输入 `water` 或 `h2o`

### 2. DFT 几何优化 (dft-opt)

标准 DFT 几何优化模板。

```gamess
! DFT geometry optimization
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END
 $BASIS GBASIS=CC-PVDZ $END
 $SCF CONV=1.0E-06 $END
 $STATPT OPTTOL=0.0001 NSTEP=50 $END
 $DATA
Title
C1

Atom  Z  x  y  z
 $END
```

**触发**: 输入 `dft-opt` 或 `opt`

### 3. HF 单点能 (hf-sp)

Hartree-Fock 单点能量计算。

```gamess
! HF single point energy
 $CONTRL SCFTYP=RHF RUNTYP=ENERGY $END
 $BASIS GBASIS=STO NGAUSS=3 $END
 $DATA
Title
C1

Atom  Z  x  y  z
 $END
```

**触发**: 输入 `hf-sp` 或 `hf`

### 4. MP2 能量 (mp2)

MP2 相关能量计算。

```gamess
! MP2 correlation energy
 $CONTRL SCFTYP=RHF MPLEVL=2 RUNTYP=ENERGY $END
 $BASIS GBASIS=CC-PVDZ $END
 $MP2 $END
 $DATA
Title
C1

Atom  Z  x  y  z
 $END
```

**触发**: 输入 `mp2`

### 5. 频率计算 (freq)

振动频率和热力学性质计算。

```gamess
! Vibrational frequency calculation
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=HESSIAN $END
 $BASIS GBASIS=CC-PVDZ $END
 $FORCE METHOD=ANALYTIC VIBANL=.TRUE. TEMP=298.15 $END
 $DATA
Title
C1

Atom  Z  x  y  z
 $END
```

**触发**: 输入 `freq` 或 `frequency`

### 6. TD-DFT 激发态 (tddft)

时间依赖 DFT 激发态计算。

```gamess
! TD-DFT excited states
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP TDDFT=EXCITE $END
 $BASIS GBASIS=CC-PVDZ $END
 $TDDFT NSTATE=10 IROOT=1 $END
 $DATA
Title
C1

Atom  Z  x  y  z
 $END
```

**触发**: 输入 `tddft` 或 `excited`

### 7. 过渡态搜索 (ts)

SADDLE 点过渡态搜索。

```gamess
! Transition state search
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=SADPOINT $END
 $BASIS GBASIS=CC-PVDZ $END
 $STATPT METHOD=RFO IFOLOW=1 NSTEP=100 $END
 $DATA
Transition state guess
C1

Atom  Z  x  y  z
 $END
```

**触发**: 输入 `ts` 或 `saddle`

### 8. IRC 计算 (irc)

内禀反应坐标路径跟踪。

```gamess
! Intrinsic Reaction Coordinate
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=IRC $END
 $BASIS GBASIS=CC-PVDZ $END
 $IRC METHOD=RFO NPOINT=50 STRIDE=0.1 $END
 $DATA
Transition state
C1

Atom  Z  x  y  z
 $END
```

**触发**: 输入 `irc`

### 9. CCSD(T) 计算 (ccsdt)

耦合簇带三重微扰高精度计算。

```gamess
! CCSD(T) high-accuracy calculation
 $CONTRL SCFTYP=RHF CCTYP=CCSD(T) RUNTYP=ENERGY $END
 $BASIS GBASIS=CC-PVTZ $END
 $CC MAXCC=50 CCCONV=1.0E-06 $END
 $DATA
Title
C1

Atom  Z  x  y  z
 $END
```

**触发**: 输入 `ccsdt` 或 `ccsd(t)`

### 10. PCM 溶剂化 (pcm)

PCM 水溶剂化 DFT 计算。

```gamess
! DFT with PCM water solvation
 $CONTRL SCFTYP=RHF DFTTYP=B3LYP RUNTYP=OPTIMIZE $END
 $BASIS GBASIS=CC-PVDZ $END
 $PCM SOLVNT=WATER $END
 $STATPT OPTTOL=0.0001 NSTEP=50 $END
 $DATA
Title
C1

Atom  Z  x  y  z
 $END
```

**触发**: 输入 `pcm` 或 `solvation`

## 代码片段使用 / Using Snippets

### VS Code

1. 输入触发词（如 `water`）
2. 按 `Tab` 或 `Enter` 接受
3. 使用 `Tab` 在占位符间导航

### Neovim

1. 输入触发词
2. 触发完成（`Ctrl-X` `Ctrl-O` 或 LSP 完成）
3. 在占位符间跳转

## 自定义代码片段 / Custom Snippets

用户可添加自定义代码片段到编辑器配置：

### VS Code (settings.json)

```json
{
  "gamess.snippets": {
    "my-calc": {
      "prefix": "mycalc",
      "body": [
        "$CONTRL SCFTYP=RHF DFTTYP=${1|B3LYP,PBE,M06-2X|} RUNTYP=${2|ENERGY,OPTIMIZE|} $END",
        "$BASIS GBASIS=${3|CC-PVDZ,CC-PVTZ|} $END",
        "$DATA",
        "${4:Title}",
        "C1",
        "",
        "${5:Atom}  ${6:Z}  ${7:x}  ${8:y}  ${9:z}",
        " $END"
      ],
      "description": "My custom calculation"
    }
  }
}
```

## 占位符导航 / Placeholder Navigation

| 键 | 动作 |
|-----|------|
| Tab | 下一个占位符 |
| Shift+Tab | 上一个占位符 |
| Esc | 退出占位符模式 |

## 代码片段最佳实践

1. **从简单开始**: 使用水分子片段测试
2. **调整基组**: 修改 GBASIS 以适应精度需求
3. **验证频率**: 优化后添加频率计算
4. **保存模板**: 为常用系统保存自定义片段

## 来源列表 / Source List

- `raw/assets/README.md` - 代码片段概述
- `raw/assets/examples/` - 完整示例
