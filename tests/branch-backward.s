mov R0, #0
A: cmp R0, #3
bge B
add R0, R0, #1
b A
B:
