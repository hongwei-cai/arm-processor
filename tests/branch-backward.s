mov R0, #1
mov R1, #0
A: cmp R0, R1
beq B
add R1, R1, #1
b A
B:
