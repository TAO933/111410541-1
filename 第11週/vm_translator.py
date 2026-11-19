#!/usr/bin/env python3
"""Nand2Tetris 虛擬機翻譯器（VM code -> Hack 組合語言）

支援課本 Project 7 與 Project 8 的完整指令集。

用法:
    python vm_translator.py Prog.vm          # 輸出 Prog.asm
    python vm_translator.py Folder           # 翻譯資料夾所有 .vm -> Folder/Folder.asm
    python vm_translator.py Folder -o out    # 輸出 out.asm

單一 .vm 檔預設不加 bootstrap；資料夾輸入預設會加入 bootstrap
（SP = 256，呼叫 Sys.init）。可用 --bootstrap / --no-bootstrap 強制指定。
"""
import argparse
import glob
import os
import sys

from parser import Parser
from codewriter import CodeWriter


def collect_vm_files(source: str):
    """回傳 (檔案清單, 是否為資料夾)。"""
    if os.path.isdir(source):
        files = sorted(glob.glob(os.path.join(source, "*.vm")))
        if not files:
            sys.exit(f"錯誤：資料夾內沒有 .vm 檔：{source}")
        return files, True

    if not source.endswith(".vm"):
        sys.exit("錯誤：輸入檔必須是 .vm，或是一個包含 .vm 檔的資料夾")
    if not os.path.isfile(source):
        sys.exit(f"錯誤：找不到檔案：{source}")
    return [source], False


def default_output(source: str, is_dir: bool) -> str:
    if is_dir:
        folder = os.path.normpath(source)
        return os.path.join(folder, os.path.basename(folder) + ".asm")
    return os.path.splitext(source)[0] + ".asm"


def translate(files, output: str, bootstrap: bool) -> int:
    writer = CodeWriter(output)

    if bootstrap:
        writer.write_init()

    count = 0
    for path in files:
        writer.set_file_name(os.path.splitext(os.path.basename(path))[0])
        parser = Parser(path)
        while parser.has_more:
            writer.write_command(
                parser.command_type(), parser.arg1(), parser.arg2()
            )
            parser.advance()
            count += 1

    writer.save()
    return count


def main():
    ap = argparse.ArgumentParser(description="Nand2Tetris VM 翻譯器")
    ap.add_argument("source", help="輸入的 .vm 檔，或包含 .vm 檔的資料夾")
    ap.add_argument("-o", "--output", help="輸出的 .asm 檔名")
    boot = ap.add_mutually_exclusive_group()
    boot.add_argument("--bootstrap", action="store_true",
                      help="強制加入 bootstrap（呼叫 Sys.init）")
    boot.add_argument("--no-bootstrap", action="store_true",
                      help="強制不加入 bootstrap")
    args = ap.parse_args()

    files, is_dir = collect_vm_files(args.source)
    source = args.source

    if args.bootstrap:
        bootstrap = True
    elif args.no_bootstrap:
        bootstrap = False
    else:
        bootstrap = is_dir

    out_name = args.output or default_output(source, is_dir)
    if not out_name.lower().endswith(".asm"):
        out_name += ".asm"

    count = translate(files, out_name, bootstrap)

    target = os.path.normpath(source) if is_dir else source
    print(f"翻譯完成: {target} -> {out_name} "
          f"({len(files)} 個檔案, {count} 道指令, "
          f"bootstrap={'是' if bootstrap else '否'})")


if __name__ == "__main__":
    main()
