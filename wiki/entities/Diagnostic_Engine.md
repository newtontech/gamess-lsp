# Diagnostic Engine (诊断引擎)

> 类型：组件 / 诊断系统
> 创建日期：2026-06-12
> 来源数：2

## 简介 / Introduction

gamess-lsp 实现了受 python-lsp-server 提供者模型启发的共享科学 LSP 诊断契约，为编辑器提供原生提供者，同时为代理层暴露确定性 JSON。

## 严重性策略 / Severity Policy

### error (错误)
高置信度的语法、模式、类型/值或引用问题，应阻止自动提交，因为上游运行时可能拒绝输入：
- 未闭合的 `$` 组
- 关键词语法错误
- 必需关键词缺失

### warning (警告)
高风险或可疑输入，可能是有意的，应向代理显示但不自动阻止修复循环：
- 未知的 `$` 组名
- 可疑的关键词值

### information / hint (信息/提示)
样式、文档或可选优化事实

## 诊断类别 / Categories

1. **syntax** - 语法问题
2. **schema** - 模式/结构问题
3. **type/value** - 类型或值问题
4. **cross-file reference** - 跨文件引用
5. **semantic consistency** - 语义一致性
6. **preflight/runtime-risk** - 预检/运行时风险
7. **style/deprecation** - 样式/弃用

## 丰富诊断形状 / Rich Diagnostic Shape

```json
{
  "code": "STABLE_CODE",
  "severity": "error",
  "category": "schema",
  "confidence": 1.0,
  "source": "gamess-lsp",
  "range": {
    "start": {"line": 0, "character": 0},
    "end": {"line": 0, "character": 1}
  },
  "software": "gamess",
  "file_type": "input",
  "path": "input",
  "expected": null,
  "actual": null,
  "manual_ref": null,
  "fix_hints": [],
  "blocking": true
}
```

## 代理 CLI / Agent CLI

```bash
gamess-lsp-tool check path/to/input --format json
gamess-lsp-tool context path/to/input --format json
gamess-lsp-tool complete path/to/input --format json
gamess-lsp-tool hover path/to/input --format json
gamess-lsp-tool symbols path/to/input --format json
gamess-lsp-tool fix path/to/input --format json
```

## 相关来源 / Related Sources

- `docs/DIAGNOSTIC_ENGINE_V1.md` - 完整诊断引擎规范
- `src/gamess_lsp/rich_diagnostics.py` - 诊断实现

## 相关实体/概念 / Related Entities/Concepts

- [[LSP_Server]]
- [[GAMESS]]

## 历史更新 / History

- 2026-06-12: 创建诊断引擎实体页面
