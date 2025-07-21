// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Mult.asm

// Multiplies R0 and R1 and stores the result in R2.
// (R0, R1, R2 refer to RAM[0], RAM[1], and RAM[2], respectively.)
// The algorithm is based on repetitive addition.

// pseudocode
//i = 0
//for(i < R1){
//  R2=R2+R0 
//  i =i+1
//}

// hack asm

// initialize R2 with 0
@R2
M=0

// initialize i with 1
@i
M=1

// main loop
(LOOP)
@R0
D=M
@R2
M=D+M
@R1
D=M
@i
D=D-M
M=M+1
@LOOP
D;JNE

// infinit loop at the end
(END)
@END
0;JMP


// another approach (without a loop variable, and modifing R1)
// (LOOP)
// @R0
// D=M
// @R2
// M=D+M
// @R1
// M=M-1
// D=M
// @LOOP
// D;JNE
//
// (END)
// @END
// 0;JMP
