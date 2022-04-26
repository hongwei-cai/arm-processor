set -o nounset 

asmfile=$1
objectfile=`basename $asmfile .s`.o
hexfile=`basename $asmfile .s`.hex

# compile to machine code binary
arm-none-eabi-gcc -c -o $objectfile $asmfile

# logisim requires this to go at top of hex file
echo "v2.0 raw" > header.tmp

# disassemble the binary, skip the first 7 lines (tail),
# take only lines with machine code (skipping the label lines)
# and take only the machine code in hexadecimal plain text (cut)
# and then remove blank lines
arm-none-eabi-objdump -S $objectfile | tail -n +7 | grep ':.' | cut -f2 >hex.tmp

# concatenate the header and the plain text machine code into one file
cat header.tmp hex.tmp >$hexfile

# remote temporary files
rm $objectfile header.tmp hex.tmp
