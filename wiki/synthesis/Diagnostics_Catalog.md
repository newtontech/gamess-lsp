# Diagnostics Catalog (诊断目录)

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> 覆盖来源：3

## 核心论点 / Core Arguments

gamess-lsp 提供结构化的诊断系统，帮助用户在提交计算前发现输入文件错误。

## 诊断严重性 / Severity Levels

### Error (错误)
必须修复才能运行：
- 未闭合的 `$` 组
- 关键词语法错误
- 缺失必需关键词

### Warning (警告)
建议修复：
- 未知的 `$` 组名
- 可疑的关键词值

### Information
信息提示：
- 样式建议
- 优化建议

## 诊断类别 / Categories

### 1. Syntax (语法)

#### 未闭合的组
```json
{
  "code": "UNCLOSED_GROUP",
  "severity": "error",
  "category": "syntax",
  "message": "Group $CONTRL not properly closed with $END",
  "range": {...}
}
```

**示例**:
```gamess
! 错误
$CONTRL SCFTYP=RHF

! 正确
$CONTRL SCFTYP=RHF $END
```

### 2. Schema (模式)

#### 未知的组
```json
{
  "code": "UNKNOWN_GROUP",
  "severity": "warning",
  "category": "schema",
  "message": "Unknown group: $CONTROL (did you mean $CONTRL?)",
  "fix_hints": ["Change to $CONTRL"]
}
```

**示例**:
```gamess
! 警告
$CONTROL SCFTYP=RHF $END

! 建议
$CONTRL SCFTYP=RHF $END
```

#### 缺失必需关键词
```json
{
  "code": "MISSING_REQUIRED_KEYWORD",
  "severity": "error",
  "category": "schema",
  "message": "$CONTRL group missing RUNTYP keyword",
  "fix_hints": ["Add RUNTYP=ENERGY"]
}
```

### 3. Type/Value (类型/值)

#### 无效的关键词值
```json
{
  "code": "INVALID_KEYWORD_VALUE",
  "severity": "error",
  "category": "type/value",
  "message": "SCFTYP=XYZ is not a valid value. Valid: RHF, UHF, ROHF, MCSCF, NONE",
  "expected": ["RHF", "UHF", "ROHF", "MCSCF", "NONE"],
  "actual": "XYZ"
}
```

**示例**:
```gamess
! 错误
$CONTRL SCFTYP=XYZ $END

! 正确
$CONTRL SCFTYP=RHF $END
```

### 4. Semantic (语义)

#### 不兼容的方法组合
```json
{
  "code": "INCOMPATIBLE_METHODS",
  "severity": "error",
  "category": "semantic",
  "message": "CCTYP is incompatible with MPLEVL=2. Set MPLEVL=0 when using CCTYP"
}
```

#### 缺失必需组
```json
{
  "code": "MISSING_REQUIRED_GROUP",
  "severity": "error",
  "category": "semantic",
  "message": "RUNTYP=OPTIMIZE requires $STATPT group"
}
```

### 5. Preflight (预检)

#### 内存不足警告
```json
{
  "code": "INSUFFICIENT_MEMORY",
  "severity": "warning",
  "category": "preflight/runtime-risk",
  "message": "MWORDS=10 may be insufficient for this system. Consider increasing."
}
```

## 完整诊断代码 / Full Diagnostic Codes

| 代码 | 类别 | 严重性 | 描述 |
|------|------|--------|------|
| UNCLOSED_GROUP | syntax | error | 组缺少 $END |
| UNKNOWN_GROUP | schema | warning | 未知的组名 |
| MISSING_REQUIRED_KEYWORD | schema | error | 缺少必需关键词 |
| INVALID_KEYWORD_VALUE | type/value | error | 无效的值 |
| INCOMPATIBLE_METHODS | semantic | error | 不兼容的方法 |
| MISSING_REQUIRED_GROUP | semantic | error | 缺少必需组 |
| DUPLICATE_KEYWORD | schema | warning | 重复的关键词 |
| INSUFFICIENT_MEMORY | preflight | warning | 内存可能不足 |

## 诊断输出格式 / Diagnostic Output Format

### LSP 格式

```json
{
  "uri": "file:///path/to/input.inp",
  "diagnostics": [
    {
      "range": {
        "start": {"line": 0, "character": 0},
        "end": {"line": 0, "character": 10}
      },
      "severity": 1,
      "source": "gamess-lsp",
      "message": "Group $CONTRL not properly closed with $END",
      "code": "UNCLOSED_GROUP",
      "codeDescription": {
        "href": "https://..."
      }
    }
  ]
}
```

### 代理 CLI JSON 格式

```json
{
  "software": "gamess",
  "file_type": "input",
  "path": "input.inp",
  "diagnostics": [
    {
      "code": "UNCLOSED_GROUP",
      "severity": "error",
      "category": "syntax",
      "confidence": 1.0,
      "source": "gamess-lsp",
      "range": {...},
      "blocking": true,
      "fix_hints": ["Add $END at line X"]
    }
  ]
}
```

## 修复提示 / Fix Hints

### 自动修复

```json
{
  "fix_hints": [
    {
      "title": "Add missing $END",
      "edit": {
        "range": {...},
        "newText": "$CONTRL SCFTYP=RHF $END"
      }
    }
  ]
}
```

### 建议修复

```json
{
  "fix_hints": [
    "Change $CONTROL to $CONTRL",
    "Add RUNTYP=ENERGY to $CONTRL",
    "Remove duplicate SCFTYP keyword"
  ]
}
```

## 相关实体/概念 / Related Entities/Concepts

- [[Diagnostic_Engine]]
- [[LSP_Server]]
- [[GAMESS_Input_Syntax]]

## 来源列表 / Source List

- `docs/DIAGNOSTIC_ENGINE_V1.md` - 诊断引擎规范
- `src/gamess_lsp/validator.py` - 诊断实现
- `src/gamess_lsp/rich_diagnostics.py` - 丰富诊断格式
