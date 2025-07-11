print("DMux8Way (in=load, sel=address, a=load0, b=load1, c=load2, d=load3, e=load4, f=load5, g=load6, h=load7);")
print()
for i in range(8):
    print(f"Register (in=in, load=load{i}, out=reg{i});")
print()
print("Mux8Way16 (a=reg0, b=reg1, c=reg2, d=reg3, e=reg4, f=reg5, g=reg6, h=reg7, sel=address, out=out);")
