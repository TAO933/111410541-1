# Nand2Tetris 虛擬機翻譯器（VM Translator）

[nand2tetris.org](https://www.nand2tetris.org/) 課程 **Project 7 + Project 8** 的完整實作，
把 VM 指令（`.vm`）翻譯成 Hack 組合語言（`.asm`）。

包含 Project 7 的堆疊運算與記憶體存取，以及 Project 8 的程式流程、函式呼叫與 bootstrap。
使用 **Python 3**，無任何外部依賴，輸出可直接交給同專案的
[`nand2tetris-assembler`](../nand2tetris-assembler/) 或官方 `Assembler` 組譯。

## 專案結構

| 檔案 | 說明 |
| --- | --- |
| `vm_translator.py` | 主程式：解析命令列、走訪 `.vm` 檔、產生 `.asm` |
| `gui.py` | **Tkinter 圖形介面**：選檔、設定 bootstrap、翻譯與顯示紀錄 |
| `run_gui.bat` | Windows 雙擊啟動圖形介面 |
| `parser.py` | **Parser**：解析每道 VM 指令，取出 type / arg1 / arg2 |
| `codewriter.py` | **CodeWriter**：把 VM 指令翻譯成 Hack 組合語言 |
| `examples/SimpleAdd.vm` | 範例：7 + 8 |
| `examples/SumToTen.vm` | 範例：以標籤與 temp 計算 1 + 2 + … + 10 |

## 使用方法

```powershell
# 單一檔案：產生 examples/SimpleAdd.asm
py vm_translator.py examples/SimpleAdd.vm

# 指定輸出檔名：產生 out.asm
py vm_translator.py examples/SimpleAdd.vm -o out

# 資料夾：翻譯資料夾內所有 .vm，輸出 <Folder>/<Folder>.asm
py vm_translator.py ..\somewhere\FibonacciElement

# 強制加入 bootstrap（SP = 256 並呼叫 Sys.init）
py vm_translator.py examples/SimpleAdd.vm --bootstrap

# 強制不加 bootstrap
py vm_translator.py ..\somewhere\FibonacciElement --no-bootstrap
```

## 圖形介面（Tkinter）

不想打指令時，可以直接開啟圖形介面：

```powershell
py gui.py
```

或在 Windows 上雙擊 `run_gui.bat`。

介面功能：

- 選擇單一 `.vm` 檔，或整個包含 `.vm` 的資料夾
- 自動帶出輸出 `.asm` 路徑，也可自行修改或另存
- Bootstrap 可選「自動 / 一律加入 / 一律不加」
- 翻譯完成後顯示檔案數、指令數與 bootstrap 狀態
- 執行紀錄會列出選擇的輸入檔案與錯誤訊息
- 可一鍵開啟輸出資料夾
- 快捷鍵：`Ctrl+O` 選檔案、`Ctrl+Shift+O` 選資料夾、`Ctrl+Enter` 翻譯

圖形介面與命令列共用同一套 `vm_translator.py` / `parser.py` / `codewriter.py`，
翻譯結果完全一致。

### Bootstrap 規則

| 輸入 | 預設 | 用途 |
| --- | --- | --- |
| 單一 `.vm` | 不加 bootstrap | Project 7 / 8 的單檔測試（測試腳本自行設定 SP） |
| 資料夾 | 加 bootstrap | 多檔程式，需從 `Sys.init` 開始執行 |

## 支援的 VM 指令

| 類別 | 指令 |
| --- | --- |
| 算術邏輯 | `add` `sub` `neg` `eq` `gt` `lt` `and` `or` `not` |
| 記憶體存取 | `push segment index`、`pop segment index` |
| 程式流程 | `label`、`goto`、`if-goto` |
| 函式 | `function f n`、`call f n`、`return` |

`segment` 支援：`constant`、`local`、`argument`、`this`、`that`、
`pointer`、`temp`、`static`。

## 記憶體配置

| VM 區段 | Hack 對應 |
| --- | --- |
| `local` | `LCL + index` |
| `argument` | `ARG + index` |
| `this` | `THIS + index` |
| `that` | `THAT + index` |
| `pointer 0/1` | `THIS` / `THAT` |
| `temp 0..7` | `RAM[5..12]` |
| `static i` | `RAM[16...]` 的 `檔名.i` 符號 |
| `constant n` | 直接載入常數 n（僅 push） |

## 翻譯方式

### 堆疊

`SP`（`RAM[0]`）指向堆疊頂端的下一個位置。

- push：把值寫入 `RAM[SP]`，再 `SP++`
- pop：先 `SP--`，再讀取 `RAM[SP]`

### 算術與比較

- `add` / `sub` / `and` / `or`：彈出兩個值運算後放回堆疊。
- `neg` / `not`：直接對堆疊頂端取負 / 取補數。
- `eq` / `gt` / `lt`：相減後以 `JEQ` / `JGT` / `JLT` 判斷，
  成立推入 `-1`（true），否則推入 `0`（false）。
  每個比較使用唯一的 `VM_CMP_*` 標籤，避免衝突。

### 標籤與函式

- VM 標籤 `label` 會翻成 `functionName$label`，因此不同函式可使用同名標籤。
- `call f n` 依序推入：返回位址、`LCL`、`ARG`、`THIS`、`THAT`，
  接著設定
  `ARG = SP - 5 - n`、`LCL = SP`，再跳到 `f`。
- `return` 依課本流程：
  取出返回位址、把返回值放到 `*ARG`、`SP = ARG + 1`，
  再依序還原 `THAT` / `THIS` / `ARG` / `LCL`，最後跳回呼叫端。
- `function f n` 會在進入函式時把 n 個 local 變數初始化為 0。

### Bootstrap

資料夾模式預設在程式開頭插入：

```
@256
D=A
@SP
M=D
call Sys.init 0
```

## 驗證

已使用官方 `CPUEmulator` 跑過下列測試，結果全部 `Comparison ended successfully`：

| Project | 測試 |
| --- | --- |
| 7 | `SimpleAdd`、`StackTest`、`BasicTest`、`PointerTest`、`StaticTest` |
| 8 | `BasicLoop`、`FibonacciSeries`、`SimpleFunction` |
| 8（多檔） | `NestedCall`、`FibonacciElement`、`StaticsTest` |

驗證方式（以 SimpleAdd 為例）：

```powershell
py vm_translator.py SimpleAdd.vm          # 產生 SimpleAdd.asm
# 用官方 CPUEmulator 執行 SimpleAdd.tst
& "路徑\tools\CPUEmulator.bat" "路徑\SimpleAdd.tst"
```

也可以搭配本專案的組譯器產生 `.hack`：

```powershell
py ..\nand2tetris-assembler\assembler.py examples\SimpleAdd.asm
```

## 錯誤處理

Parser 會檢查指令格式，遇到下列情況會丟出帶列號的 `SyntaxError`：

- 未知指令或未知記憶體區段
- `push` / `pop` 缺少索引，或索引不是非負整數
- `pop constant`
- `pointer` 索引不是 0 或 1
- `function` / `call` 的參數個數不是非負整數
