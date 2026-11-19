"""CodeWriter 模組：把 VM 指令翻譯成 Hack 組合語言。

翻譯策略與課本第 7、8 章一致：
  - 堆疊頂端由 RAM[0]（SP）指向
  - local/argument/this/that 的基底位址分別存在 LCL/ARG/THIS/THAT
  - temp 對應 RAM[5..12]
  - static 以「檔名.索引」配置到 RAM[16] 之後
  - 函式標籤使用 functionName$label，避免不同函式同名標籤衝突
"""
from parser import (
    C_ARITHMETIC, C_PUSH, C_POP, C_LABEL, C_GOTO, C_IF,
    C_FUNCTION, C_RETURN, C_CALL,
)

SEGMENT_BASE = {
    "local": "LCL",
    "argument": "ARG",
    "this": "THIS",
    "that": "THAT",
}

COMPARE_JUMP = {"eq": "JEQ", "gt": "JGT", "lt": "JLT"}


class CodeWriter:
    def __init__(self, path: str):
        self.path = path
        self.lines = []
        self.label_counter = 0
        self.file_name = "global"
        self.function_name = "global"

    # ------------------------------------------------------------------
    # 對外介面
    # ------------------------------------------------------------------
    def set_file_name(self, name: str):
        self.file_name = name

    def write_init(self):
        """插入 bootstrap 程式碼：SP = 256，然後呼叫 Sys.init。"""
        self._comment("bootstrap")
        self._emit("@256", "D=A", "@SP", "M=D")
        self.write_call("Sys.init", 0)

    def write_command(self, ctype: str, arg1=None, arg2=None):
        if ctype == C_ARITHMETIC:
            self.write_arithmetic(arg1)
        elif ctype in (C_PUSH, C_POP):
            self.write_push_pop(ctype, arg1, arg2)
        elif ctype == C_LABEL:
            self.write_label(arg1)
        elif ctype == C_GOTO:
            self.write_goto(arg1)
        elif ctype == C_IF:
            self.write_if(arg1)
        elif ctype == C_FUNCTION:
            self.write_function(arg1, arg2)
        elif ctype == C_RETURN:
            self.write_return()
        elif ctype == C_CALL:
            self.write_call(arg1, arg2)
        else:
            raise ValueError(f"未知的指令類型: {ctype!r}")

    def save(self):
        with open(self.path, "w", encoding="utf-8", newline="\n") as f:
            f.write("\n".join(self.lines) + "\n")

    # ------------------------------------------------------------------
    # 堆疊基本操作
    # ------------------------------------------------------------------
    def _emit(self, *instructions: str):
        self.lines.extend(instructions)

    def _comment(self, text: str):
        self.lines.append(f"// {text}")

    def _unique(self, prefix: str) -> str:
        self.label_counter += 1
        return f"{prefix}_{self.label_counter}"

    def _push_d(self):
        self._emit("@SP", "A=M", "M=D", "@SP", "M=M+1")

    def _pop_d(self):
        self._emit("@SP", "AM=M-1", "D=M")

    # ------------------------------------------------------------------
    # 記憶體存取
    # ------------------------------------------------------------------
    def write_push_pop(self, ctype: str, segment: str, index: int):
        action = "push" if ctype == C_PUSH else "pop"
        self._comment(f"{action} {segment} {index}")

        if ctype == C_PUSH:
            self._push_value(segment, index)
        else:
            self._pop_value(segment, index)

    def _push_value(self, segment: str, index: int):
        if segment == "constant":
            self._emit(f"@{index}", "D=A")
            self._push_d()
        elif segment in SEGMENT_BASE:
            self._push_segment(SEGMENT_BASE[segment], index)
        elif segment == "temp":
            self._emit(f"@{5 + index}", "D=M")
            self._push_d()
        elif segment == "pointer":
            self._emit("@" + ("THIS" if index == 0 else "THAT"), "D=M")
            self._push_d()
        elif segment == "static":
            self._emit(f"@{self.file_name}.{index}", "D=M")
            self._push_d()

    def _pop_value(self, segment: str, index: int):
        if segment in SEGMENT_BASE:
            self._pop_segment(SEGMENT_BASE[segment], index)
        elif segment == "temp":
            self._pop_d()
            self._emit(f"@{5 + index}", "M=D")
        elif segment == "pointer":
            self._pop_d()
            self._emit("@" + ("THIS" if index == 0 else "THAT"), "M=D")
        elif segment == "static":
            self._pop_d()
            self._emit(f"@{self.file_name}.{index}", "M=D")

    def _push_segment(self, base: str, index: int):
        self._emit(
            f"@{index}", "D=A",
            f"@{base}", "A=D+M", "D=M",
        )
        self._push_d()

    def _pop_segment(self, base: str, index: int):
        self._emit(
            f"@{index}", "D=A",
            f"@{base}", "D=D+M",
            "@R13", "M=D",
        )
        self._pop_d()
        self._emit("@R13", "A=M", "M=D")

    # ------------------------------------------------------------------
    # 算術與邏輯
    # ------------------------------------------------------------------
    def write_arithmetic(self, command: str):
        self._comment(command)

        if command in ("add", "sub", "and", "or"):
            op = {"add": "+", "sub": "-", "and": "&", "or": "|"}[command]
            self._emit(
                "@SP", "AM=M-1", "D=M",   # D = 堆疊頂端
                "A=A-1",                   # A = 第二個運算元
                f"M=D{op}M" if command != "sub" else "M=M-D",
            )
        elif command in ("neg", "not"):
            op = "-" if command == "neg" else "!"
            self._emit("@SP", "A=M-1", f"M={op}M")
        elif command in COMPARE_JUMP:
            self._write_compare(COMPARE_JUMP[command])
        else:
            raise ValueError(f"未知的算術指令: {command!r}")

    def _write_compare(self, jump: str):
        true_label = self._unique("VM_CMP_TRUE")
        end_label = self._unique("VM_CMP_END")
        self._emit(
            "@SP", "AM=M-1", "D=M",   # D = 堆疊頂端
            "A=A-1",                   # A = 第二個運算元
            "D=M-D",                   # D = 第二個 - 頂端
            f"@{true_label}", f"D;{jump}",
            "@SP", "A=M-1", "M=0",     # 條件不成立：推入 0
            f"@{end_label}", "0;JMP",
            f"({true_label})",
            "@SP", "A=M-1", "M=-1",    # 條件成立：推入 -1
            f"({end_label})",
        )

    # ------------------------------------------------------------------
    # 程式流程
    # ------------------------------------------------------------------
    def _scoped_label(self, label: str) -> str:
        return f"{self.function_name}${label}"

    def write_label(self, label: str):
        self._comment(f"label {label}")
        self._emit(f"({self._scoped_label(label)})")

    def write_goto(self, label: str):
        self._comment(f"goto {label}")
        self._emit(f"@{self._scoped_label(label)}", "0;JMP")

    def write_if(self, label: str):
        self._comment(f"if-goto {label}")
        self._pop_d()
        self._emit(f"@{self._scoped_label(label)}", "D;JNE")

    # ------------------------------------------------------------------
    # 函式呼叫
    # ------------------------------------------------------------------
    def write_function(self, name: str, n_locals: int):
        self._comment(f"function {name} {n_locals}")
        self.function_name = name
        self._emit(f"({name})")
        for _ in range(n_locals):
            self._emit("@0", "D=A")
            self._push_d()

    def write_call(self, name: str, n_args: int):
        self._comment(f"call {name} {n_args}")
        return_label = self._unique(f"VM_RETURN_{name}")

        # 推入返回位址
        self._emit(f"@{return_label}", "D=A")
        self._push_d()

        # 儲存呼叫端狀態：LCL、ARG、THIS、THAT
        for base in ("LCL", "ARG", "THIS", "THAT"):
            self._emit(f"@{base}", "D=M")
            self._push_d()

        # ARG = SP - 5 - nArgs；LCL = SP
        self._emit(
            "@SP", "D=M",
            "@5", "D=D-A",
            f"@{n_args}", "D=D-A",
            "@ARG", "M=D",
            "@SP", "D=M",
            "@LCL", "M=D",
        )

        # 跳到被呼叫的函式
        self._emit(f"@{name}", "0;JMP", f"({return_label})")

    def write_return(self):
        self._comment("return")

        # R13 = frame（舊的 LCL）
        self._emit("@LCL", "D=M", "@R13", "M=D")

        # R14 = return address = *(frame - 5)
        self._emit("@5", "A=D-A", "D=M", "@R14", "M=D")

        # *ARG = return value（堆疊頂端）
        self._emit("@SP", "AM=M-1", "D=M", "@ARG", "A=M", "M=D")

        # SP = ARG + 1
        self._emit("@ARG", "D=M+1", "@SP", "M=D")

        # 依序還原 THAT、THIS、ARG、LCL
        for base in ("THAT", "THIS", "ARG", "LCL"):
            self._emit("@R13", "AM=M-1", "D=M", f"@{base}", "M=D")

        # 跳回呼叫端
        self._emit("@R14", "A=M", "0;JMP")
