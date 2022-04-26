set -o nounset
file=$1

sed -i -e 's/file#.*[/\]alu.circ/file#alu.circ/' $file
sed -i -e 's/file#.*[/\]alu-control.circ/file#alu-control.circ/' $file
sed -i -e 's/file#.*[/\]mem.circ/file#mem.circ/' $file
sed -i -e 's/file#.*[/\]regfile.circ/file#regfile.circ/' $file
sed -i -e 's/file#.*[/\]control.circ/file#control.circ/' $file
sed -i -e 's/file#.*[/\]cpu.circ/file#cpu.circ/' $file
sed -i -e 's/file#.*[/\]iodevices.circ/file#iodevices.circ/' $file
