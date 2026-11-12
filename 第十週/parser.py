"""Parser 模組：讀取 .asm 檔，逐行解析出指令的各個欄位。"""
import re

C_COMMAND = re.compile(
    r"^(?P<dest>[AMD]{1,3})?"      # dest（可省略）
    r"=?"                          # '='（有 dest 時才出現）
    r"(?P<comp>[^;@/]+)"           # comp
    r"(?:;(?P<jump>\w{3}))?"       # jump（可省略）
)


class Parser:
    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()

        self.commands = []  # [(type, parts...), ...]
        for raw in lines:
            line = raw.split("//")[0].strip()  # 去除註解與空白
            if not line:
                continue
            self.commands.append(self._classify(line))

        self.current = 0
        self.has_more = bool(self.commands)

    @staticmethod
    def _classify(line: str):
        if line.startswith("@"):
            return ("A", line[1:])
        if line.startswith("(") and line.endswith(")"):
            return ("L", line[1:-1])
        m = C_COMMAND.match(line)
        if not m:
            raise SyntaxError(f"無法解析的指令: {line!r}")
        return ("C", m.group("dest") or "", m.group("comp").strip(),
                m.group("jump") or "")

    def advance(self):
        self.current += 1
        self.has_more = self.current < len(self.commands)

    def command_type(self) -> str:
        return self.commands[self.current][0]

    # -- A 指令 --
    def symbol(self) -> str:
        return self.commands[self.current][1]

    # -- C 指令 --
    def dest(self) -> str:
        return self.commands[self.current][1]

    def comp(self) -> str:
        return self.commands[self.current][2]

    def jump(self) -> str:
        return self.commands[self.current][3]
