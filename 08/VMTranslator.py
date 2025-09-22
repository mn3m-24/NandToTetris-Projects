import os

class VMTranslator:
    def __init__(self, path):
        self.vmFiles = []
        self.asmCmds = []
        self.symbolIdx = 0
        self.retIdx = 0
        self.asmFileName=(os.path.splitext(os.path.basename(path))[0] or path.strip("/").split("/")[-1]) + ".asm"
        self.outPath = ""
        self.multi = False
        if os.path.isdir(path):
            self.multi = True
            for file in os.listdir(path):
                if file[-2:] == "vm":
                    self.vmFiles.append(os.path.join(path, file))
            self.outPath=path
        else:
            self.vmFiles = [path]
            self.outPath = os.path.dirname(path) or os.getcwd()

    def parse(self):
        if self.multi:
            self.asmCmds.extend(["@256","D=A","@SP","M=D"]) # set SP=256
            self.asmCmds.extend(["@1","D=A","@LCL","M=D"])
            self.asmCmds.extend(["@2","D=A","@ARG","M=D"])
            self.asmCmds.extend(["@3","D=A","@THIS","M=D"])
            self.asmCmds.extend(["@4","D=A","@THAT","M=D"])
            pushD=["@SP","A=M","M=D","@SP","M=M+1"]
            self.asmCmds.extend(["@bootstrap","D=A", *pushD]) # push retAddr

            for memSeg in ["LCL","ARG","THIS","THAT"]: # push LCL,ARG,THIS,THAT
                self.asmCmds.extend([f"@{memSeg}","D=M", *pushD])

            self.asmCmds.extend(["@5","D=A","@SP","D=M-D","@ARG","M=D"]) # ARG=SP-n-5
            self.asmCmds.extend(["@SP","D=M","@LCL","M=D"]) # LCL=SP
            self.asmCmds.extend(["@Sys.init","0;JMP","(bootstrap)"])

        for file in self.vmFiles:
            singleParse=SingleVMTranslator(file, self.symbolIdx, self.retIdx)
            singleParse.parse()
            self.asmCmds.extend(singleParse.asmCmds)
            self.symbolIdx=singleParse.symbolIdx
            self.retIdx=singleParse.retIdx

    def save(self):
        print(self.outPath)
        with open(os.path.join(self.outPath, self.asmFileName), "w") as file:
            for cmd in self.asmCmds:
                file.write(cmd + "\n")

class SingleVMTranslator:
    arithTable = {
        "not":"!", "neg":"-", "add":"+",
        "sub":"-", "and":"&", "or":"|",
        "eq":"JEQ", "lt":"JLT", "gt":"JGT"
    }
    segTable = {
        "local":"LCL", "argument":"ARG", "this":"THIS",
        "that":"THAT", "temp":"5", "pointer":"3"
    }
    def __init__(self, path, symbolIdx, retIdx):
        self.vmFileName, self.ext = os.path.splitext(os.path.basename(path))
        self.relativePath = path[:-len(self.vmFileName) - len(self.ext)]
        self.vmCmds = []
        self.asmCmds = []
        self.symbolIdx= symbolIdx
        self.retIdx= retIdx
        self.curFunc=""
        with open(path, "r") as file:
            for line in file:
                _line = line.strip()
                if _line.startswith("//") or len(_line) == 0: continue
                if "//" in _line:
                    _line = _line.split("//", 1)[0].strip()
                self.vmCmds.append(_line)

    # parsing input .vm files into list of commands (removing whitespaces & comments)
    def parse(self):
        for cmd in self.vmCmds:
            parts = cmd.split()
            self.asmCmds.extend(["// "+cmd]) # comment before the asm translation
            if len(parts) == 1:
                if parts[0] == "return":
                    self.writeReturn();
                else: # arithmetic command
                    self.writeArithmetic(parts[0])
            elif len(parts) == 2:
                if parts[0] == "label":
                    self.writeLable(parts[1]);
                elif parts[0] == "goto":
                    self.writeGoto(parts[1]);
                elif parts[0] == "if-goto":
                    self.writeIf(parts[1]);
            elif len(parts) == 3:
                if parts[0] == "push" or parts[0] == "pop":
                    self.writePushPop(cmd)
                elif parts[0] == "call":
                    self.writeCall(parts[1], parts[2]);
                elif parts[0] == "function":
                    self.writeFunction(parts[1], parts[2]);

    # translate arithmetic commands
    def writeArithmetic(self, command: str):
        op = SingleVMTranslator.arithTable[command]
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
            base = SingleVMTranslator.segTable[seg]
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
            base = SingleVMTranslator.segTable[seg]
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

    def writeLable(self, label):
        self.asmCmds.extend([f"({self.curFunc}${label})"]);

    def writeGoto(self, label):
        self.asmCmds.extend([f"@{self.curFunc}${label}", "0;JMP"]);

    def writeIf(self, label):
        # if the top element in the stack is non-zero, then jump to it, else continue
        self.asmCmds.extend(["@SP", "AM=M-1", "D=M", f"@{self.curFunc}${label}", "D;JNE"])

    def writeFunction(self, functionName, nVars):
        self.curFunc = functionName
        self.asmCmds.extend([f"({functionName})"])
        for var in range(int(nVars)):
            self.asmCmds.extend(["@SP", "A=M", "M=0", "@SP", "M=M+1"]);

    def writeCall(self, functionName, nArgs):
        label = f"End${functionName}${self.retIdx}"
        self.retIdx += 1
        pushD = ["@SP","A=M","M=D","@SP","M=M+1"]  # push D onto stack
        # push return address
        self.asmCmds.extend([f"@{label}", "D=A", *pushD])

        # push LCL, ARG, THIS, THAT (push their VALUES, not their addresses)
        for memSeg in ["LCL", "ARG", "THIS", "THAT"]:
            self.asmCmds.extend([f"@{memSeg}", "D=M", *pushD])

        # ARG = SP - nArgs - 5
        self.asmCmds.extend([f"@{int(nArgs) + 5}", "D=A", "@SP", "D=M-D", "@ARG", "M=D"])
        # LCL = SP
        self.asmCmds.extend(["@SP", "D=M", "@LCL", "M=D"])
        # goto function
        self.asmCmds.extend([f"@{functionName}", "0;JMP"])
        # return label
        self.asmCmds.extend([f"({label})"])

    def writeReturn(self):
        self.asmCmds.extend(["@LCL","D=M","@R15","M=D"]) # put LCL into R15
        self.asmCmds.extend(["@5","D=A","@R15","A=M-D","D=M","@R14","M=D"]) # put retAddr into R14
        self.asmCmds.extend(["@SP","AM=M-1","D=M","@ARG","A=M","M=D"]) # *ARG=pop()
        self.asmCmds.extend(["@ARG","D=M+1","@SP","M=D"]) # SP=ARG+1
        self.asmCmds.extend(["@R15","A=M-1","D=M","@THAT","M=D"]) # THAT=*(FRAME-1)
        self.asmCmds.extend(["@2","D=A","@R15","A=M-D","D=M","@THIS","M=D"]) #THIS=*(FRAME-2)
        self.asmCmds.extend(["@3","D=A","@R15","A=M-D","D=M","@ARG","M=D"]) # ARG=*(FRAME-3)
        self.asmCmds.extend(["@4","D=A","@R15","A=M-D","D=M","@LCL","M=D"]) # LCL=*(FRAME-4)
        self.asmCmds.extend(["@R14","A=M","0;JMP"]) # goto retAddr


def main():
    path = r"./StaticsTest/"
    translator = VMTranslator(path)
    translator.parse()
    translator.save()
    pass

if __name__ == "__main__":
    main()
