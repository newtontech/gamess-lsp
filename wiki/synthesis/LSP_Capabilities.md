# LSP Capabilities (LSP 功能能力)

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> 覆盖来源：3

## 核心论点 / Core Capabilities

gamess-lsp 作为 GAMESS 输入文件的 Language Server，提供智能编辑功能，包括语法验证、自动完成、导航和代码操作。

## 核心功能 / Core Features

### 1. 诊断 (Diagnostics)

实时验证输入文件，检测问题：

**错误级别**:
- 未闭合的 `$` 组（缺少 `$END`）
- 必需关键词缺失
- 严重语法错误

**警告级别**:
- 未知的 `$` 组名
- 可疑的关键词值

```json
{
  "severity": "error",
  "message": "Group $CONTRL not properly closed with $END",
  "range": {...}
}
```

### 2. 自动完成 (Completion)

**三级完成**:

1. **组名完成**: 输入 `$` 显示所有可用组
2. **关键词完成**: 组内输入显示可用关键词
3. **值完成**: 输入 `=` 后显示允许的值

```gamess
$CONTRL SCFTYP=[RHF, UHF, ROHF, MCSCF, NONE]
        DFTTYP=[B3LYP, PBE, M06-2X, ...]
        RUNTYP=[ENERGY, OPTIMIZE, SADPOINT, ...]
 $END
```

**代码片段**:
- 水分子 DFT 优化
- HF 单点计算
- MP2 能量计算
- 频率计算
- TD-DFT 激发态
- 过渡态搜索
- IRC 计算
- CCSD(T) 计算
- PCM 溶剂化

### 3. 悬停文档 (Hover)

鼠标悬停显示文档：

```
SCFTYP
Type of SCF wavefunction.
Values: RHF, UHF, ROHF, MCSCF, NONE.
Default: RHF
```

### 4. 转到定义 (Go to Definition)

- 点击组名跳转到组定义
- 点击关键词跳转到关键词定义

### 5. 查找引用 (Find References)

查找组或关键词的所有使用位置。

### 6. 符号 (Symbols)

文档符号导航：
- 按 `$` 组分组
- 显示所有关键词

### 7. 代码操作 (Code Actions)

快速修复：

```gamess
! 原始
$CONTRL SCFTYP=RHF

! 操作: Add missing $END

! 结果
$CONTRL SCFTYP=RHF $END
```

可用操作：
1. 添加缺失的 `$END`
2. 建议未知组的修正
3. 添加必需关键词（如 `RUNTYP`）

### 8. 重命名 (Rename)

跨文档重命名：
- 重命名组名
- 重命名关键词
- 所有引用自动更新

### 9. 格式化 (Formatting)

自动格式化：
- 一致的 2 空格缩进
- `=` 周围标准化空格
- 正确的 `$END` 放置

### 10. 工作区符号 (Workspace Symbols)

跨所有打开的 GAMESS 文件搜索符号。

## 技术实现 / Technical Implementation

### 服务器架构

```
pygls (LSP framework)
    ↓
gamess-lsp server
    ↓
├── Parser (tokenizer + parser)
├── Validator (diagnostics)
├── Completer (completion provider)
├── Hover provider (documentation)
├── Code actions (quick fixes)
└── Symbol provider (navigation)
```

### 解析流程

```
Input file
    ↓
Tokenizer (line → tokens)
    ↓
Parser (tokens → AST)
    ↓
Validator (AST → diagnostics)
    ↓
Completion (cursor → suggestions)
```

### 关键词数据库

位于 `src/gamess_lsp/keywords.py`:
- `GAMESS_GROUPS`: 所有支持的组
- `GAMESS_KEYWORDS`: 每个组的关键词
- 值列表和文档

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
local lspconfig = require('lspconfig')
lspconfig.gamess.setup {
  cmd = {"gamess-lsp"},
  filetypes = {"gamess"},
  root_dir = lspconfig.util.root_pattern("*.inp"),
}
```

### Emacs

```elisp
(lsp-register-client
 (make-lsp-client :new-connection (lsp-stdio-connection "gamess-lsp")
                  :major-modes '(gamess-mode)
                  :server-id 'gamess-lsp))
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

## 功能路线图 / Feature Roadmap

- [ ] 无效值验证
- [ ] 跨文件引用
- [ ] 高级代码片段
- [ ] 单元测试模板生成
- [ ] 从输出文件导入结果

## 来源列表 / Source List

- `raw/assets/README.md` - 功能概述
- `src/gamess_lsp/server.py` - LSP 服务器实现
- `docs/DIAGNOSTIC_ENGINE_V1.md` - 诊断规范
- `docs/OPENQC_ALIGNMENT.md` - OpenQC 对齐
