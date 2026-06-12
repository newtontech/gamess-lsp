# LSP_Server (Language Server Protocol)

> 类型：协议 / 服务器
> 创建日期：2026-06-12
> 来源数：2

## 简介 / Introduction

Language Server Protocol (LSP) 是一种协议，允许开发工具和语言服务器之间通信，提供智能编辑功能如自动完成、跳转到定义、诊断等。`gamess-lsp` 是 GAMESS 输入文件的 LSP 实现。

## LSP 核心功能 / Core LSP Features

### 1. 诊断 (Diagnostics)
实时验证 GAMESS 输入文件，检测：
- 未知的 `$` 组
- 未闭合的组（缺少 `$END`）
- 缺失必需的关键词

### 2. 自动完成 (Completion)
- `$` 组名称完成
- 组内关键词完成
- 关键词值建议（在 `=` 后）
- 代码片段模板（如水分子、DFT 优化等）

### 3. 悬停文档 (Hover)
鼠标悬停在关键词或组名上时显示文档

### 4. 转到定义 (Go to Definition)
导航到组或关键词的定义位置

### 5. 查找引用 (Find References)
查找组或关键词的所有使用位置

### 6. 代码操作 (Code Actions)
快速修复常见问题：
- 添加缺失的 `$END`
- 建议未知组的修正
- 添加必需关键词（如 `$CONTRL` 的 `RUNTYP`）

### 7. 重命名 (Rename)
跨文档重命名组和关键词

## GAMESS-LSP 架构 / Architecture

```
gamess-lsp/
├── src/gamess_lsp/
│   ├── parser.py          # GAMESS 输入文件解析器
│   ├── keywords.py        # GAMESS 关键词数据库
│   ├── tokenizer.py       # 词法分析
│   ├── validator.py      # 输入验证
│   ├── server.py         # LSP 服务器实现
│   └── features/         # LSP 功能实现
├── examples/             # 示例输入文件
└── docs/                # 文档
```

## 编辑器集成 / Editor Integration

### VS Code
```json
{
  "languageserver": {
    "gamess": {
      "command": "gamess-lsp",
      "filetypes": ["gamess"],
      "rootPatterns": ["*.inp"]
    }
  }
}
```

### Neovim
```lua
lspconfig.gamess.setup {
  cmd = {"gamess-lsp"},
  filetypes = {"gamess"},
  root_dir = lspconfig.util.root_pattern("*.inp"),
}
```

## 相关来源 / Related Sources

- `raw/assets/README.md` - LSP 功能概述
- `src/gamess_lsp/server.py` - LSP 服务器实现
- `docs/DIAGNOSTIC_ENGINE_V1.md` - 诊断引擎规范

## 相关实体/概念 / Related Entities/Concepts

- [[GAMESS]]
- [[Diagnostic_Engine]]
- [[OpenQC]]

## 历史更新 / History

- 2026-06-12: 创建 LSP 服务器实体页面
