// This file is part of www.nand2tetris.org
// and the book "The Elements of Computing Systems"
// by Nisan and Schocken, MIT Press.
// File name: projects/4/Fill.asm

// Runs an infinite loop that listens to the keyboard input. 
// When a key is pressed (any key), the program blackens the screen,
// i.e. writes "black" in every pixel. When no key is pressed, 
// the screen should be WHITENed.

(CHECK) // the main check loop of the program

  @KBD // taking the key input
  D=M

  @BLACKEN // if(input != 0) blacken the screen
  D;JNE

  @WHITEN // if(input == 0) whiten the screen
  0;JMP

  (WHITEN)
    @8192
    D=A
    @remaining_reg
    M=D
    @reg_pointer
    M=0

    (INNER_WHITEN_LOOP) // inner loop to iterate over all the screen registers and whiten them
      @reg_pointer
      D=M
      @SCREEN
      A=D+A
      M=0
      @reg_pointer
      M=M+1
      @remaining_reg
      M=M-1
      D=M
    @INNER_WHITEN_LOOP
    D;JNE

@CHECK // return to the check input after whiten the screen
0;JMP

  (BLACKEN)
    @8192
    D=A
    @remaining_reg
    M=D
    @reg_pointer
    M=0
    (INNER_BLACKEN_LOOP) // inner loop to iterate over all the screen registers and blacken them
      @reg_pointer
      D=M
      @SCREEN
      A=D+A
      M=-1
      @reg_pointer
      M=M+1
      @remaining_reg
      M=M-1
      D=M
    @INNER_BLACKEN_LOOP
    D;JNE

@CHECK // return to the check label after blacken the screen
0;JMP
