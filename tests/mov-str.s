mov R0, #10
str R0, [R0, #4]
ldr R1, [R0, #4]
add R1, R1, #10
str R1, [R0, #8]
ldr R2, [R0, #8]
