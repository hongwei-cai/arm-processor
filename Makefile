# Run MIPS single-cycle tests
p2sc:
	cp alu.circ alu-control.circ regfile.circ cs3410.jar mem.circ cpu.circ control.circ iodevices.circ tests
	cd tests && python3 ./test.py p2sc | tee ../TEST_LOG

# Run ALU + Regfile tests
p1:
	cp alu.circ alu-control.circ regfile.circ cs3410.jar tests
	cd tests && python3 ./test.py p1 | tee ../TEST_LOG
