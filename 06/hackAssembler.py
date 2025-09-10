import os
class Assembler:
    symTable = {
    "SP":0,"LCL":1,"ARG":2,"THIS":3,"THAT":4,
    "R0":0,"R1":1,"R2":2,"R3":3,"R4":4,"R5":5,
    "R6":6,"R7":7,"R8":8,"R9":9,"R10":10,"R11":11,
    "R12":12,"R13":13,"R14":14,"R15":15,
    "SCREEN":16384,"KBD":24576} # pre-defined label
    compTable = {
    "0":"0101010","1":"0111111","-1":"0111010",
    "D":"0001100","A":"0110000","!D":"0001101",
    "!A":"0110001","-D":"0001111","-A":"0110011",
    "D+1":"0011111","A+1":"0110111","D-1":"0001110",
    "A-1":"0110010","D+A":"0000010","D-A":"0010011",
    "A-D":"0000111","D&A":"0000000","D|A":"0010101",
    "M":"1110000","!M":"1110001","-M":"1110011",
    "M+1":"1110111","M-1":"1110010","D+M":"1000010",
    "D-M":"1010011","M-D":"1000111","D&M":"1000000",
    "D|M":"1010101"
    }
    destTable = {
    "null":"000","M":"001","D":"010","MD":"011",
    "A":"100","AM":"101","AD":"110","AMD":"111"
    }
    jumpTable = {
    "null":"000","JGT":"001","JEQ":"010","JGE":"011",
    "JLT":"100","JNE":"101","JLE":"110","JMP":"111"
    }

    def __init__(self, filePath):

        self.codes = []
        self.binCodes = []
        self.alloc_memory = 16
        self.fileName, self.ext = os.path.splitext(filePath)
        assert self.ext == ".asm", "Must be an assembly file"

        # reading the file
        with open(filePath,'r') as file:
            for line in file:
                _line=line.strip()
                if len(_line) == 0 or _line[0] == '/' :
                    continue
                if _line.find('/') != -1:
                    _line=_line[:_line.find('/')]
                self.codes.append(_line.strip())

    @staticmethod
    def dec2bin(decimal):
        binary = bin(int(decimal))[2:]  # bin(x) is like "0b010110"
        return binary.zfill(16) # "0000000000010110"

    def processLabel(self):
        noLableCodes = []
        currentLine = -1
        for line in self.codes:
            if line.startswith("("):
                self.symTable[line[1:-1]] = currentLine+1
            else:
                noLableCodes.append(line)
                currentLine += 1
        self.codes = noLableCodes



    def parse(self):
        for instruction in self.codes:
            if instruction.startswith("@"): # A-instruction
                self.binCodes.append(self.instructionA(instruction[1:]))
            else: # C-isntruction
                self.binCodes.append(self.instructionC(instruction))

    def instructionA(self, instruction):
        if instruction.isdecimal() :
            return Assembler.dec2bin(instruction)
        elif self.symTable.get(instruction) == None:
            self.symTable[instruction] = self.alloc_memory
            binary = Assembler.dec2bin(self.alloc_memory)
            self.alloc_memory += 1
            return binary
        else:
            return Assembler.dec2bin(self.symTable.get(instruction))

    def instructionC(self, instruction):
        dest_compJump = instruction.split("=")
        compJump = dest_compJump[0].split(";")
        dest = "null"
        if not (len(dest_compJump) == 1):
            dest = dest_compJump[0]
            compJump = dest_compJump[1].split(";")

        comp = compJump[0]
        jump = "null" if len(compJump) == 1 else compJump[1]
        return "111" + Assembler.compTable[comp] + Assembler.destTable[dest] + Assembler.jumpTable[jump]

    def saveBin(self):
        with open(f"{self.fileName}.hack", "w") as file:
            for line in self.binCodes:
                file.write(line + "\n");


def main():
    assem = Assembler("RectL.asm")
    assem.processLabel()
    assem.parse()
    assem.saveBin()

if __name__ == "__main__":
    main()
