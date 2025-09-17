import os

class VMTranslator:
    arithTable = {
        "not":"!", "neg":"-", "add":"+",
        "sub":"-", "and":"&", "or":"|",
        "eq":"JEQ", "lt":"JLT", "gt":"JGT"
    }
    segTable = {
        "local":"LCL", "argument":"ARG", "this":"THIS",
        "that":"THAT", "temp":"5", "pointer":"3"
    }

    def __init__(self, path):
        super().__init__() # for possible inheritance
        self.vmFileName, self.ext = os.path.splitext(os.path.basename(path))
        self.relativePath = path[:-len(self.vmFileName) - len(self.ext)]
        self.vmCmds = []
        self.asmCmds = []
        self.symbolIdx = 0
        with open(path, "r") as file:
            for line in file:
                _line = line.strip()
                if _line.startswith("//") or len(_line) == 0: continue
                if _line.find("/") != -1: _line = _line[: _line.find("//")].strip()
                self.vmCmds.append(_line)

    # parsing input .vm files into list of commands (removing whitespaces & comments)
    def parse(self):
        for cmd in self.vmCmds:
            parts = cmd.split()
            if len(parts) == 1:
                self.writeArithmetic(parts[0])
            elif parts[0] == "push" or parts[0] == "pop":
                self.writePushPop(cmd)

    # translate arithmetic commands
    def writeArithmetic(self, command: str):
        op = VMTranslator.arithTable[command]
        if command in ("add", "and", "or"):
            # For add/and/or: pop two values, operate
            self.asmCmds.extend(["@SP","AM=M-1", "D=M", "A=A-1", f"M=D{op}M"])
        elif command == "sub":
            # For sub: x - y where y is top of stack
            # M=M-D means M = M - D
            self.asmCmds.extend(["@SP","AM=M-1", "D=M", "A=A-1", "M=M-D"])
        elif command in ("not", "neg"):
            self.asmCmds.extend(["@SP", "A=M-1", f"M={op}M"])
        elif command in ("eq", "gt", "lt"):
            label1 = command + "_TRUE_" + str(self.symbolIdx)
            label2 = "END_" + str(self.symbolIdx)
            self.symbolIdx += 1
            # Pop two values and compare: D = x - y
            cmds = [
                "@SP", "AM=M-1", "D=M",    # D = y (top of stack)
                "A=A-1", "D=M-D",           # D = x - y (x is second on stack)
                f"@{label1}", f"D;{op}",    # If condition true, jump
                "@SP", "A=M-1", "M=0",      # Set false (0)
                f"@{label2}", "0;JMP",      # Jump to end
                f"({label1})",              # True label
                "@SP", "A=M-1", "M=-1",     # Set true (-1)
                f"({label2})"               # End label
            ]
            self.asmCmds.extend(cmds)

    def writePushPop(self, command):
        type, seg, i = command.split()

        # handling constant push/pop commands
        if seg == "constant": # push constant i
            cmds = [f"@{i}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1"]
            self.asmCmds.extend(cmds)

        # handling ("local", "argument", "this", "that") push/pop commands
        elif seg in ("local", "argument", "this", "that"):
            base = VMTranslator.segTable[seg]
            if type == "push":
                # Compute address = base + i, load value, push to stack
                cmds = [f"@{i}", "D=A", f"@{base}", "A=D+M", "D=M",
                       "@SP", "A=M", "M=D", "@SP", "M=M+1"]
            else:  # pop
                # Compute target address, pop value from stack, store it
                cmds = [f"@{i}", "D=A", f"@{base}", "D=D+M", "@addr", "M=D",
                       "@SP", "AM=M-1", "D=M", "@addr", "A=M", "M=D"]
            self.asmCmds.extend(cmds)

        # handling ("temp", "pointer") push/pop commands
        elif seg in ("temp", "pointer"):
            base = VMTranslator.segTable[seg]
            if type == "push":
                cmds = [f"@{i}", "D=A", f"@{base}", "A=D+A", "D=M",
                       "@SP", "A=M", "M=D", "@SP", "M=M+1"]
            else:  # pop
                cmds = [f"@{i}", "D=A", f"@{base}", "D=D+A", "@addr", "M=D",
                       "@SP", "AM=M-1", "D=M", "@addr", "A=M", "M=D"]
            self.asmCmds.extend(cmds)

        # handling static push/pop commands
        elif seg == "static":
            label = self.vmFileName
            if type == "push":
                cmds = [f"@{label}.{i}", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"]
            else:  # pop
                cmds = ["@SP", "AM=M-1", "D=M", f"@{label}.{i}", "M=D"]
            self.asmCmds.extend(cmds)

    def save(self):
        with open(f"{self.relativePath}{self.vmFileName}.asm", "w") as file:
            for cmd in self.asmCmds:
                file.write(cmd + "\n")

def main():
    translator = VMTranslator(r"./StackArithmetic/StackTest/StackTest.vm")
    translator.parse()
    translator.save()

if __name__ == "__main__":
    main()
