#!/usr/bin/env python3
"""Nand2Tetris 組譯器（Hack 組合語言 -> Hack 機器碼）

用法:
    python assembler.py Prog.asm        # 輸出 Prog.hack
    python assembler.py Prog.asm -o out # 輸出 out.hack
"""
import argparse
import os
import sys

from parser import Parser
from code import dest, comp, jump
from symbol_table import SymbolTable


def assemble(path: str) -> str:
    table = SymbolTable()

    # Pass 1：掃描所有 (LABEL)，登記每一列指令的位址
    parser = Parser(path)
    rom_address = 0
    while parser.has_more:
        if parser.command_type() == "L":
            table.add_entry(parser.symbol(), rom_address)
        else:
            rom_address += 1
        parser.advance()

    # Pass 2：把每列指令轉成 16-bit 二進位
    out = []
    parser = Parser(path)
    while parser.has_more:
        ctype = parser.command_type()
        if ctype == "A":
            symbol = parser.symbol()
            if symbol.isdigit():
                address = int(symbol)
            elif table.contains(symbol):
                address = table.get_address(symbol)
            else:
                address = table.next_free_address()
                table.add_entry(symbol, address)
            out.append(f"0{address:015b}")
        elif ctype == "C":
            out.append(
                "111" + comp(parser.comp()) + dest(parser.dest()) + jump(parser.jump())
            )
        # L 指令不產生機器碼
        parser.advance()
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Hack 組合語言組譯器")
    ap.add_argument("asm", help="輸入的 .asm 檔")
    ap.add_argument("-o", "--output", help="輸出的 .hack 檔名（不含副檔名）")
    args = ap.parse_args()

    if not args.asm.endswith(".asm"):
        sys.exit("錯誤：輸入檔必須是 .asm")

    machine_code = assemble(args.asm)

    out_name = args.output or os.path.splitext(args.asm)[0]
    if not out_name.endswith(".hack"):
        out_name += ".hack"
    with open(out_name, "w", encoding="utf-8") as f:
        f.write(machine_code)

    print(f"組譯完成: {args.asm} -> {out_name} ({len(machine_code.splitlines())} 列)")


if __name__ == "__main__":
    main()
