# EDA 是什麼？IC 設計中的電子設計自動化

## 一、定義

**EDA（Electronic Design Automation，電子設計自動化）** 是指利用電腦軟體工具來輔助積體電路（IC）與電子系統的設計、模擬、驗證、佈局與製造準備的一整套技術與工具。

簡單來說：**EDA 就是把「畫電路、驗證電路、把電路做成晶片」的流程自動化、電腦化的軟體工具鏈。**

一顆現代晶片可能包含數百億個電晶體，若沒有 EDA，工程師根本不可能以人工完成設計與驗證。因此 EDA 被視為半導體產業的「上游關鍵軟體」，與晶圓代工、IP 並列為 IC 設計的三大支柱。

---

## 二、為什麼需要 EDA？

| 挑戰 | EDA 的角色 |
|------|-----------|
| 電晶體數量龐大（數十億級） | 自動合成、自動佈局佈線 |
| 設計錯誤成本極高（一次投片數百萬美元） | 在投片前完成模擬與驗證 |
| 製程節點不斷微縮（3nm、2nm） | 處理複雜的物理效應與設計規則 |
| 功耗、效能、面積（PPA）需最佳化 | 自動化最佳化與分析 |
| 產品上市時間壓力 | 縮短設計週期、提高重複使用性 |

---

## 三、IC 設計流程與對應的 EDA 工具

IC 設計大致可分為 **前端（Front-End）** 與 **後端（Back-End）** 兩大部分。

### 1. 系統規格與架構設計
- 定義晶片功能、效能目標、功耗預算
- 工具：系統層模擬、架構探索工具（如效能模型、Virtual Platform）

### 2. RTL 設計（Register Transfer Level）
- 使用 **Verilog / VHDL / SystemVerilog** 描述電路行為
- 工具：文字編輯器、IDE、Lint 工具（語法與風格檢查）

### 3. 功能模擬（Simulation）
- 驗證 RTL 行為是否符合規格
- 工具：Synopsys VCS、Cadence Xcelium、Siemens Questa/ModelSim
- 搭配驗證方法：UVM、Formal Verification、Coverage 分析

### 4. 邏輯合成（Logic Synthesis）
- 將 RTL 轉換成閘級電路（Gate-Level Netlist）
- 對應到特定製程的標準元件庫（Standard Cell Library）
- 工具：Synopsys Design Compiler、Cadence Genus

### 5. 時序分析（Static Timing Analysis, STA）
- 檢查電路在所有條件下能否在時脈週期內完成運算
- 工具：Synopsys PrimeTime、Cadence Tempus

### 6. 實體設計（Physical Design）
包含下列步驟：
- **Floorplanning**：規劃晶片區塊位置
- **Placement**：擺放標準元件
- **Clock Tree Synthesis（CTS）**：建立時脈樹
- **Routing**：繞線連接元件
- **DRC / LVS**：設計規則檢查與電路佈局比對

工具：Synopsys IC Compiler II、Cadence Innovus、Siemens Calibre（DRC/LVS）

### 7. 寄生參數萃取與簽核（Sign-off）
- 萃取佈局後的電阻、電容（RC Extraction）
- 重新做時序、功耗、IR Drop、EM 分析
- 工具：Synopsys StarRC、PrimeTime、Cadence Quantus、Voltus

### 8. 光罩製作與製造（Tape-out）
- 產出 GDSII 檔案交給晶圓代工廠
- 工具：EDA 流程最終輸出與格式轉換

---

## 四、EDA 的主要工具類別

| 類別 | 功能 | 代表工具 |
|------|------|---------|
| 模擬器（Simulator） | 驗證 RTL 功能 | VCS、Xcelium、Questa |
| 合成（Synthesis） | RTL → 閘級電路 | Design Compiler、Genus |
| 實體設計（P&R） | 擺放與繞線 | IC Compiler II、Innovus |
| 時序分析（STA） | 時序簽核 | PrimeTime、Tempus |
| 實體驗證（DRC/LVS） | 佈局正確性檢查 | Calibre、PVS |
| 形式驗證（Formal） | 數學證明等效性 | Formality、Conformal |
| 功耗分析 | 功耗估算與最佳化 | PrimePower、Voltus |
| PCB 設計 | 電路板佈局 | Altium Designer、KiCad、Cadence Allegro |

---

## 五、主要 EDA 廠商

- **Synopsys**：全球最大 EDA 廠商，涵蓋模擬、合成、實體設計、IP
- **Cadence**：第二大廠，類比/混合訊號與數位流程皆強
- **Siemens EDA（原 Mentor Graphics）**：Calibre 為 DRC/LVS 業界標準
- **Ansys**：電源完整性、熱分析、電磁模擬
- 開源工具：**KiCad**（PCB）、**OpenROAD**、**Yosys**（學術/開源 IC 流程）

---

## 六、EDA 與其他領域的關係

```
IC 設計 = 電路知識 + EDA 工具 + IP 智財 + 晶圓代工
```

- **IP（Intellectual Property）**：可重複使用的電路模組（如 CPU 核心、USB 控制器）
- **Foundry**：提供製程設計套件（PDK）與標準元件庫，EDA 需與其配合
- **EDA**：串接設計、驗證與製造的橋樑

三者形成半導體產業的核心生態系。

---

## 七、總結

- EDA 是 IC 設計不可或缺的軟體工具鏈，負責從 **概念 → RTL → 閘級 → 佈局 → 光罩** 的每一個環節。
- 沒有 EDA，就不可能設計出現代動輒數十億電晶體的晶片。
- 對學習者而言，建議先熟悉 **Verilog/SystemVerilog** 與基本數位邏輯，再接觸模擬器與合成工具，最後理解實體設計流程。
- 想入門可先使用開源工具（Yosys、OpenROAD、Verilator）建立完整觀念，再進到業界商用工具。

---
