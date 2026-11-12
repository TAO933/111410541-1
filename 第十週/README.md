# Nand2Tetris 組譯器（Hack Assembler）

[nand2tetris.org](https://www.nand2tetris.org/) 課程 **Project 6** 的組譯器實作，
將 Hack 組合語言（`.asm`）翻譯成 Hack 機器碼（`.hack`，16-bit 二進位）。

使用 **Python 3**，無任何外部依賴，架構完全對應課本第 6 章的設計。

## 專案結構

| 檔案 | 說明 |
| --- | --- |
| `assembler.py` | 主程式：兩階段（Pass 1 / Pass 2）組譯流程 |
| `parser.py` | **Parser** 模組：解析每列指令，取出欄位 |
| `code.py` | **Code** 模組：mnemonic → 二進位轉換表 |
| `symbol_table.py` | **SymbolTable** 模組：符號位址管理 |
| `examples/Add.asm` | 課本範例：RAM[2] = RAM[0] + RAM[1] |
| `examples/Max.asm` | 課本範例：RAM[2] = max(RAM[0], RAM[1]) |

## 使用方法

```powershell
py assembler.py examples/Add.asm        # 產生 examples/Add.hack
py assembler.py Prog.asm -o MyOutput    # 指定輸出檔名（MyOutput.hack）
```

## Hack 組合語言快速回顧

### A 指令（Address）

```
@21          -> 0000000000010101
@R0          -> 0000000000000000（查符號表）
@LOOP        -> 位址取自標籤或變數
```

### C 指令（Compute）

```
111  a c1~c6  d1~d3  j1~j3
 ↑   comp     dest   jump
```

語法：`dest=comp;jump`，其中 `dest` 與 `jump` 可省略。

- **comp**：課本 Table 6.2，如 `0`、`D`、`M`、`D+M`、`D|M`…（含 `M` 時 a=1）
- **dest**：課本 Table 6.3，如 `M`、`D`、`MD`、`AMD`…（可省略）
- **jump**：課本 Table 6.3，如 `JGT`、`JEQ`、`JMP`…（可省略）

### Label

`(LOOP)` 定義標籤，指向**下一列指令**的 ROM 位址；組譯時不佔機器碼列。

## 組譯流程（兩個 Pass）

```
Pass 1（符號表建立）
  逐列掃描，遇到 (LABEL) 就登記 {標籤 -> 目前 ROM 位址}；
  只有 A / C 指令會遞增 ROM 位址。

Pass 2（產生機器碼）
  A 指令：
    @數字      -> 直接轉 15-bit 二進位
    @已定符號  -> 查符號表
    @新變數    -> 從 RAM 16, 17, 18 ... 依序配置
  C 指令：
    111 + comp(comp) + dest(dest) + jump(jump)
```

### 內建符號（開機預載）

| 符號 | 位址 | | 符號 | 位址 |
| --- | --- | --- | --- | --- |
| `SP` | 0 | | `R8` | 8 |
| `LCL` | 1 | | `R9` | 9 |
| `ARG` | 2 | | `R10` | 10 |
| `THIS` | 3 | | `R11` | 11 |
| `THAT` | 4 | | `R12` | 12 |
| `R0`~`R7` | 0~7 | | `R13`~`R15` | 13~15 |
| `SCREEN` | 16384 | | `KBD` | 24576 |

## 範例輸出

`examples/Add.asm`：

```
0000000000000000   @0
111110000010000    D=M
0000000000000001   @1
111000010010000    D=D+M
0000000000000010   @2
111001100001000    M=D
0000000000000110   @6
111101010000111    0;JMP
```

`examples/Max.asm` 已通過與課本標準答案比對，輸出完全一致。

## 設計細節

- **Parser**：用正則 `^([AMD]{1,3})?=([^;@/]+)(;...)?$` 拆解 C 指令，並自動
  去除 `//` 註解與空白行，所以原始檔可以任意排版。
- **Code**：以字典實作課本三張轉換表，查表即得 3-bit 欄位。
- **SymbolTable**：`add_entry` / `contains` / `get_address` / `next_free_address`
  四個方法，變數從 RAM 位址 16 起自動配置。
- 遇到無法解析的指令會丟出 `SyntaxError` 並附上原始內容方便除錯。

## 與官方工具比對

可用 Nand2Tetris 提供的 `tools/Assembler.sh` 開啟同一個 `.asm`，
或用 `TextComparer` 比對產出的 `.hack` 檔：

```powershell
py assembler.py examples/Max.asm
# 再用 tools 下的 TextComparer.bat 比對 Max.hack 與官方輸出
```
