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
                if _line.find("/") != -1: _line = _line[: _line.find("/")]
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
        if command in ("add", "sub", "and", "or"):
            self.asmCmds.extend(["@SP","AM=M-1", "D=M", "A=A-1", f"M=M{op}D"])
        elif command in ("not", "neg"):
            self.asmCmds.extend(["@SP", "A=M-1", f"M={op}M"])
        elif command in ("eq", "gt", "lt"):
            label1, label2 = command + "_" + str(self.symbolIdx), f"END_{self.symbolIdx}"
            condition = [
            f"@{label1}", f"D;{op}",
            "@SP", "M=0",
            f"@{label2}", "0;JMP",
            f"({label1})", "@SP",
            "M=-1", f"({label2})"
            ]
            self.symbolIdx += 1
            cmds = ["@SP", "AM=M-1", "D=-M", "A=A-1", "D=D+M", *condition]
            self.asmCmds.extend(cmds)

    def writePushPop(self, command):
        type, seg, i = command.split()

        # handling constant push/pop commands
        if seg == "constant": # push constant i
            cmds = [f"@{i}", "D=A", "@SP", "A=M", "M=D", "@SP", "M=M+1"]
            self.asmCmds.extend(cmds)

        # handling ("local", "argument", "this", "that") push/pop commands
        elif seg in ("local", "argument", "this", "that"):
            cmds = [f"@{i}", "D=A", f"@{VMTranslator.segTable[seg]}", "D=D+M", "@addr", "M=D", "@SP"]
            if type == "push":
                cmds = cmds + ["A=M", "M=D", "@SP", "M=M+1"]
            else:
                cmds = cmds + ["M=M-1", "A=M", "D=M", "@addr", "A=M", "M=D"]
                self.asmCmds.extend(cmds)

        # handling ("temp", "pointer") push/pop commands
        elif seg in ("temp", "pointer"):
            cmds = [f"@{i}", "D=A", f"@{VMTranslator.segTable[seg]}"]
            if type == "push":
                cmds = cmds + ["A=A+D", "D=M", "@SP", "A=M", "M=D", "@SP", "M=M+1"]
            else:
                cmds = cmds + ["D=D+A", "@addr", "M=D", "@SP", "AM=M-1", "D=M", "@addr" ,"A=M" ,"M=D"]
                self.asmCmds.extend(cmds)

        # handling static push/pop commands
        elif seg == "static":
            label = self.vmFileName
            cmds = [f"@{label}.{i}", "D=M"]
            if type == "push":
                cmds = cmds + ["@SP", "A=M", "M=D", "@SP", "M=M+1"]
            else:
                cmds = ["@SP", "AM=M-1", "D=M", f"@{label}.{i}", "M=D"] ########## i might need to return to this line #########
            self.asmCmds.extend(cmds)


    def save(self):
        with open(f"{self.relativePath}{self.vmFileName}.asm", "w") as file:
            for cmd in self.asmCmds:
                file.write(cmd + "\n")

def main():
    translator = VMTranslator(r"./BasicTest/BasicTest.vm")
    translator.parse()
    translator.save()

if __name__ == "__main__":
    main()
