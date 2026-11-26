# 第 12 週：nand2tetris Jack 編譯器（Project 11）

本週完成 nand2tetris 第 11 章 **Compiler II** 的 Jack 語言編譯器。程式將 `.jack` 原始碼轉換為可由 nand2tetris VM Emulator 執行的 `.vm` 指令。

## 功能

- 將單一 Jack 檔案或資料夾中的所有 `.jack` 檔案編譯成對應的 `.vm` 檔。
- 支援 Jack 的 class、constructor、function、method、static/field/local/argument 變數。
- 支援 `let`、`if/else`、`while`、`do`、`return`、運算式、遞迴子程序呼叫。
- 支援陣列讀寫、字串常數、布林值與 `this`，並正確產生 `Memory`、`String`、`Math` 等 OS 呼叫。
- 內建明確的語法錯誤位置提示（檔名、行、列）。

## 執行需求

僅需 Node.js，沒有任何第三方套件依賴。使用 Node.js 18 或更新版本。

## 使用方式

在本目錄執行：

```powershell
# 編譯一個 Jack 檔案
node .\JackCompiler.js .\tests\fixtures\ArrayTest\Main.jack

# 編譯某個資料夾中的所有 Jack 檔案
node .\JackCompiler.js .\tests\fixtures\Square
```

編譯後，VM 檔會放在來源檔的相同位置，例如 `Main.jack` 會產生 `Main.vm`。可將輸出的 VM 檔以 nand2tetris 的 VM Emulator 載入執行。

## 測試

測試採用 nand2tetris 第 11 章常見的測試程式：

| 測試 | 驗證內容 |
| --- | --- |
| Seven | 逐行比對基礎運算與 `do` 呼叫的 VM 輸出 |
| ArrayTest | 陣列配置、位址計算、陣列讀寫與迴圈 |
| Square | constructor 配置、method 的 `this` 設定及物件方法呼叫 |
| 語言邊界 | 字串、註解、一元運算與 `if/else` |

執行完整回歸測試：

```powershell
node --test .\tests\test_compiler.js
```

目前測試結果：**4/4 通過**。

## 目錄結構

```text
第12週/
├── JackCompiler.js       # Jack → VM 編譯器
├── README.md             # 本文件
└── tests/
    ├── test_compiler.js  # Node.js 內建測試
    └── fixtures/         # Seven、ArrayTest、Square 的 Jack 原始碼
```
