import json

compTable, destTable, jumpTable = {}, {}, {}

with open("compTable.json", "r") as file:
    compTable = json.load(file)
with open("destTable.json", "r") as file:
    destTable = json.load(file)
with open("jumpTable.json", "r") as file:
    jumpTable = json.load(file)

result: str = ""

def instructionA(instruction: str):
    address = int(instruction[1:])
    binAddress = bin(address)[2:]
    return "0" + binAddress.zfill(15)

def instructionC(instruction: str):
    dest_compJump = instruction.split("=")
    compJump = dest_compJump[0].split(";")
    dest = "null"
    if not (len(dest_compJump) == 1):
        dest = dest_compJump[0]
        compJump = dest_compJump[1].split(";")

    comp = compJump[0]
    jump = "null" if len(compJump) == 1 else compJump[1]
    a = "1" if "M" in comp else "0"
    return "111" + a + compTable[a][comp] + destTable[dest] + jumpTable[jump]

with open("RectL.asm", "r") as asmFile:
    cleanLines = list(filter(lambda line: line and not line.startswith("//"), map(lambda line: line.strip(), asmFile.readlines())))
    with open("out.hack", "a") as outFile:
        for line in cleanLines:
            if line.startswith("@"):
                outFile.write(instructionA(line) + "\n")
            else:
                outFile.write(instructionC(line) + "\n")

# res = instructionC("D=M") # 1111110000010000
# res = instructionC("D=D-M") # 1111010011010000
# res = instructionC("0;JMP") # 1110101010000111
# res = instructionC("AM=M+1;JGE") # 1111110111101011
# compare = "1111110111101011"

# print(compare)
# print(res, res == compare)
