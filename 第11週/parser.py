"""Parser 模組：讀取 .vm 檔，把每道 VM 指令解析成 (type, arg1, arg2)。

對應課本第 7、8 章的 Parser 設計：
  - 自動忽略空白與 // 註解
  - command_type() 回傳 C_ARITHMETIC / C_PUSH / ... 等指令類型
  - arg1() / arg2() 取出運算元
"""

C_ARITHMETIC = "C_ARITHMETIC"
C_PUSH = "C_PUSH"
C_POP = "C_POP"
C_LABEL = "C_LABEL"
C_GOTO = "C_GOTO"
C_IF = "C_IF"
C_FUNCTION = "C_FUNCTION"
C_RETURN = "C_RETURN"
C_CALL = "C_CALL"

ARITHMETIC = {"add", "sub", "neg", "eq", "gt", "lt", "and", "or", "not"}
SEGMENTS = {
    "local", "argument", "this", "that",
    "constant", "pointer", "temp", "static",
}


class Parser:
    def __init__(self, path: str):
        self.commands = []  # [(type, arg1, arg2), ...]
        self.index = 0
        with open(path, "r", encoding="utf-8") as f:
            for lineno, raw in enumerate(f, 1):
                line = raw.split("//", 1)[0].strip()
                if line:
                    self.commands.append(self._parse(line, lineno))

    @property
    def has_more(self) -> bool:
        return self.index < len(self.commands)

    def advance(self):
        self.index += 1

    def command_type(self) -> str:
        return self.commands[self.index][0]

    def arg1(self):
        return self.commands[self.index][1]

    def arg2(self):
        return self.commands[self.index][2]

    @staticmethod
    def _parse(line: str, lineno: int):
        parts = line.split()
        op = parts[0]

        def fail(message: str):
            raise SyntaxError(f"第 {lineno} 列：{message}（{line!r}）")

        if op in ARITHMETIC:
            if len(parts) != 1:
                fail("算術指令不接受運算元")
            return (C_ARITHMETIC, op, None)

        if op == "return":
            if len(parts) != 1:
                fail("return 不接受運算元")
            return (C_RETURN, None, None)

        if op in ("push", "pop"):
            if len(parts) != 3:
                fail(f"{op} 需要兩個運算元（區段與索引）")
            segment = parts[1]
            if segment not in SEGMENTS:
                fail(f"未知的記憶體區段 {segment!r}")
            try:
                index = int(parts[2])
            except ValueError:
                fail(f"索引必須是整數：{parts[2]!r}")
            if index < 0:
                fail("索引不可為負數")
            if op == "pop" and segment == "constant":
                fail("constant 區段不能 pop")
            if segment == "pointer" and index not in (0, 1):
                fail("pointer 索引只能是 0（THIS）或 1（THAT）")
            return (C_PUSH if op == "push" else C_POP, segment, index)

        if op in ("label", "goto", "if-goto"):
            if len(parts) != 2:
                fail(f"{op} 需要一個標籤名稱")
            ctype = {"label": C_LABEL, "goto": C_GOTO, "if-goto": C_IF}[op]
            return (ctype, parts[1], None)

        if op in ("function", "call"):
            if len(parts) != 3:
                fail(f"{op} 需要函式名稱與參數個數")
            try:
                count = int(parts[2])
            except ValueError:
                fail(f"參數個數必須是整數：{parts[2]!r}")
            if count < 0:
                fail("參數個數不可為負數")
            ctype = C_FUNCTION if op == "function" else C_CALL
            return (ctype, parts[1], count)

        fail(f"未知的 VM 指令 {op!r}")
