"""SymbolTable 模組：管理組譯過程中的符號位址。"""


class SymbolTable:
    # 開機預載的內建符號（課本 Table 6.4）
    PREDEFINED = {
        "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
        "SCREEN": 16384, "KBD": 24576,
        **{f"R{i}": i for i in range(16)},
    }

    def __init__(self):
        self.symbols = dict(self.PREDEFINED)

    def add_entry(self, symbol: str, address: int) -> None:
        self.symbols[symbol] = address

    def contains(self, symbol: str) -> bool:
        return symbol in self.symbols

    def get_address(self, symbol: str) -> int:
        return self.symbols[symbol]

    def next_free_address(self) -> int:
        return 16 + sum(1 for a in self.symbols.values() if 16 <= a < 16384)
