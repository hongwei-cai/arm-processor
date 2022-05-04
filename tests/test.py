#!/usr/bin/env python

import os
import os.path
import tempfile
import subprocess
import time
import signal
import re
import sys
import shutil
import decode_out as dec
import csv
import abc

#file_locations = os.path.expanduser(os.getcwd())
file_locations = '.'
#logisim_location = os.path.join(os.getcwd(),"logisim.jar")
logisim_location = "logisim.jar"


class TestCase():
  """
    Runs specified circuit file and compares output against the provided reference trace file.
  """

  def __init__(self, circfile, expected):
    self.circfile  = circfile
    self.expected = expected

  def __call__(self, typ):
    oformat = dec.get_test_format(typ)
    if not oformat:
        print("CANNOT format test type called [{}]".format(typ))
        return (False, "Error in the test")

    try:
        if not isinstance(self.expected, list):
            # it is a file so parse it
            self.expected = [x for x in ReferenceFileParser(oformat, self.expected).outputs()]
        else:
            [oformat.validate(x) for x in self.expected]
    except dec.OutputFormatException as e:
        print("Error in formatting of expected output (check test.py if this is a test you wrote):")
        print("\t", e)
        return (False, "Error in the test")

    output = tempfile.TemporaryFile(mode='r+')
    command = ["java","-jar",logisim_location,"-tty","table", self.circfile]
    proc = subprocess.Popen(command,
                            stdin=open(os.devnull),
                            stdout=subprocess.PIPE, text=True)
    try:
        debug_buffer = [] 
        passed = compare_unbounded(proc.stdout,self.expected, oformat, debug_buffer)
    except dec.OutputFormatException as e:
        print("Error in formatting of Logisim output (check {}):".format(self.circfile))
        print("\t", e)
        return (False, "Error in the test")
    finally:
        if os.name != 'nt':
            os.kill(proc.pid,signal.SIGTERM)
    if passed:
        return (True, "Matched expected output")
    else:
        print("Format is student then expected")
        wtr = csv.writer(sys.stdout, delimiter='\t')
        oformat.header(wtr)
        for row in debug_buffer:
            wtr.writerow(['{0:x}'.format(b) for b in row[0]])
            wtr.writerow(['{0:x}'.format(b) for b in row[1]])

        return (False, "Did not match expected output (check {}, also check test.py if this is a test you wrote)".format(self.circfile))

def compare_unbounded(student_out, expected, oformat, debug):
    parser = OutputProvider(oformat)
    for i in range(0, len(expected)):
        line1 = student_out.readline()
        values_student_parsed = parser.parse_line(line1.rstrip())

        debug.append((values_student_parsed, expected[i]))

    if values_student_parsed != expected[i]:
        return False

    return True

def run_tests(tests):
    # actual submission testing code
    print("Testing files...")
    tests_passed = 0
    tests_failed = 0

    for description,test,typ in tests:
        test_passed, reason = test(typ)
        if test_passed:
            print("\tPASSED test: %s" % description)
            tests_passed += 1
        else:
            print("\tFAILED test: %s (%s)" % (description, reason))
            tests_failed += 1
  
    print("Passed %d/%d tests" % (tests_passed, (tests_passed + tests_failed)))

class OutputProvider(object):
    def __init__(self, format):
        self.format = format

    @abc.abstractmethod
    def outputs(self):
        pass
    
    def parse_line(self, line):
        value_strs = line.split('\t')   
        values_bin = [''.join(v.split(' ')) for v in value_strs] 
        try:
            values = [int(v, 2) for v in values_bin]
        except ValueError as e:
            if values_bin == ['']:
                raise dec.OutputFormatException("you have a non-integer in this list: {}. If this is logisim output, are you sure you have a circ file for this test?".format(values_bin))
            else :
                raise dec.OutputFormatException("you have a non-integer in this list: {}".format(values_bin))
        self.format.validate(values)
        return values

class ReferenceFileParser(OutputProvider):
    def __init__(self, format, filename=None):
        self.f = filename
        super(ReferenceFileParser, self).__init__(format)

    def outputs(self):
        assert self.f is not None, "cannot use outputs if no filename given"
        with open(self.f, 'r') as inp:
            for line in inp.readlines():
                values = self.parse_line(line)
                yield values 

p1_tests = [
  ("ALU and test",
    TestCase(os.path.join(file_locations,'alu-and.circ'),
        [[0, 0b0100, 0x00000000],
         [1, 0b0000, 0x20409004],
         [2, 0b0000, 0x7E02340C],
         [3, 0b0000, 0x20010100]]), "alu"),
  ("ALU or test",
    TestCase(os.path.join(file_locations,'alu-or.circ'),
        [[0, 0b1000, 0xFFFFFFFF],
         [1, 0b0000, 0x00000001],
         [2, 0b0000, 0x100000FF],
         [3, 0b0000, 0x567CBBDF],
         [4, 0b0100, 0x00000000]]), "alu"),
  ("ALU not test",
    TestCase(os.path.join(file_locations,'alu-not.circ'),
        [[0, 0b0000, 0x0000FFFF],
         [1, 0b1000, 0xCBF67DBF],
         [2, 0b1000, 0xFFFFF000],
         [3, 0b1000, 0xDBCA7685]]), "alu"),
  ("ALU logical left shift test",
    TestCase(os.path.join(file_locations,'alu-lsl.circ'),
        [[0, 0b0000, 0x13894F00],
         [1, 0b1000, 0xE0000000]]), "alu"),
  ("ALU logical right shift test",
    TestCase(os.path.join(file_locations,'alu-lsr.circ'),
        [[0, 0b0100, 0x00000000],
         [1, 0b0000, 0x00000EFF]]), "alu"),
  ("ALU arithmetic right shift test",
    TestCase(os.path.join(file_locations,'alu-asr.circ'),
        [[0, 0b1000, 0xF7AB6FBB],
         [1, 0b1000, 0xFFFFFC00],
         [2, 0b0100, 0x00000000],
         [3, 0b1000, 0xFEEDF00D],
         [4, 0b0100, 0x00000000]]), "alu"),
  ("ALU add (with overflow) test",
    TestCase(os.path.join(file_locations,'alu-add.circ'),
        [[0, 0b0000, 0x7659035D],
         [1, 0b1001, 0x87A08D79],
         [2, 0b1001, 0x80000000],
         [3, 0b0100, 0x00000000],
         [4, 0b0110, 0x00000000],
         [5, 0b0010, 0x00000227],
         [6, 0b0011, 0x70000203],
         [7, 0b1010, 0xFFFFFEFF],
         [8, 0b0100, 0x00000000]]), "alu"),
  ("ALU sub (with overflow) test",
    TestCase(os.path.join(file_locations,'alu-sub.circ'),
        [[0, 0b0110, 0x00000000],
         [1, 0b1000, 0xFFFFFFFF],
         [2, 0b1001, 0x80000000],
         [3, 0b0110, 0x00000000],
         [4, 0b0110, 0x00000000],
         [5, 0b0010, 0x00000001]]), "alu"),
  ("ALU Control Basic Data-processing Instructions Test",
    TestCase(os.path.join(file_locations, 'alu-control-basic-data-processing-test.circ'),
        [[0, 0],
         [1, 2],
         [2, 8],
         [3, 7],
         [4, 1],
         [5, 3]]), "alu-control"),
  ("ALU Control Shifts Test",
    TestCase(os.path.join(file_locations, 'alu-control-shifts-test.circ'),
        [[0, 4],
         [1, 5],
         [2, 6]]), "alu-control"),
  ("ALU Control CMP Test",
    TestCase(os.path.join(file_locations, 'alu-control-cmp-test.circ'),
        [[0, 8]]), "alu-control"),
  ("ALU Control B Test",
    TestCase(os.path.join(file_locations, 'alu-control-b-test.circ'),
        [[0, 7]]), "alu-control"),
  ("ALU Control ldr/str Test",
    TestCase(os.path.join(file_locations, 'alu-control-ldr-str-test.circ'),
        [[0, 7],
         [1, 7],
         [2, 7],
         [3, 7]]), "alu-control"),
  ("RegFile read/write test",
    TestCase(os.path.join(file_locations,'regfile-read_write.circ'),
        [[0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
         [1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
         [2, 0x0, 0x0, 0x0, 0x0, 0x0, 0xBAD00DAD, 0xBAD00DAD],
         [3, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
         [4, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
         [5, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x10101010],
         [6, 0x0, 0x0, 0x0, 0x0, 0x0, 0x10101010, 0x0],
         [7, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0]]), "regfile"),
  ("RegFile PC test",
    TestCase(os.path.join(file_locations,'regfile-pc.circ'),
        [[0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
         [1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
         [2, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0xBAD00DAD],
         [3, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0xFEEDF00D],
         [4, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x12345678],
         [5, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x10101010],
         [6, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0xDADADADA],
         [7, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0xBABABABA]]), "regfile"),
  ("RegFile debug outputs test",
    TestCase(os.path.join(file_locations,'regfile-debug_outputs.circ'),
        [[0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
         [1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
         [2, 0xBAD00DAD, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0],
         [3, 0xBAD00DAD, 0xFEEDF00D, 0x0, 0x0, 0x0, 0x0, 0x0],
         [4, 0xBAD00DAD, 0xFEEDF00D, 0x12345678, 0x0, 0x0, 0x0, 0x0],
         [5, 0xBAD00DAD, 0xFEEDF00D, 0x12345678, 0x10101010, 0x0, 0x0, 0x0],
         [6, 0xBAD00DAD, 0xFEEDF00D, 0x12345678, 0x10101010, 0xDADADADA, 0x0, 0x0],
         [7, 0xBAD00DAD, 0xFEEDF00D, 0xBABABABA, 0x10101010, 0xDADADADA, 0x0, 0x0]]), "regfile")
]

# Single-cycle (sc) tests
p2sc_tests = [
  ("MOV imm test",
    TestCase(os.path.join(file_locations,'mov-i.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a0000f],
         [15, 0, 0, 0x0, 0x0, 1, 0x4, 0x0]]), "cpu"),
  ("MOV ADD register test",
    TestCase(os.path.join(file_locations,'mov-add-reg.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a00001],
         [1, 0, 0, 0x0, 0x0, 1, 0x4, 0xe3a01002],
         [1, 2, 0, 0x0, 0x0, 2, 0x8, 0xe0802001],
         [1, 2, 3, 0x0, 0x0, 3, 0xC, 0x0]]), "cpu"),
  ("MOV ADD imm test",
    TestCase(os.path.join(file_locations,'mov-add-i.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a01003],
         [0, 3, 0, 0x0, 0x0, 1, 0x4, 0xe2812009],
         [0, 3, 12, 0x0, 0x0, 2, 0x8, 0x0]]), "cpu"),
  ("MOV SUB register test",
    TestCase(os.path.join(file_locations,'mov-sub-reg.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a00001],
         [1, 0, 0, 0x0, 0x0, 1, 0x4, 0xe3a01002],
         [1, 2, 0, 0x0, 0x0, 2, 0x8, 0xe0402001],
         [1, 2, 0xffffffff, 0x0, 0x0, 3, 0xC, 0x0]]), "cpu"),
  ("MOV SUB imm test",
    TestCase(os.path.join(file_locations,'mov-sub-i.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a00014],
         [20, 0, 0, 0x0, 0x0, 1, 0x4, 0xe2401010],
         [20, 4, 0, 0x0, 0x0, 2, 0x8, 0xe3a02040],
         [20, 4, 64, 0x0, 0x0, 3, 0xC, 0xe2422036],
         [20, 4, 10, 0x0, 0x0, 4, 0x10, 0x0]]), "cpu"),
  ("MOV LSL test",
    TestCase(os.path.join(file_locations,'mov-lsl.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a00001],
         [1, 0, 0, 0x0, 0x0, 1, 0x4, 0xe1a01180],
         [1, 8, 0, 0x0, 0x0, 2, 0x8, 0xe3a00004],
         [4, 8, 0, 0x0, 0x0, 3, 0xC, 0xe1a02380],
         [4, 8, 512, 0x0, 0x0, 4, 0x10, 0x0]]), "cpu"),
  ("MOV LSR test",
    TestCase(os.path.join(file_locations,'mov-lsr.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a00080],
         [128, 0, 0, 0x0, 0x0, 1, 0x4, 0xe1a011a0],
         [128, 16, 0, 0x0, 0x0, 2, 0x8, 0xe3a00008],
         [8, 16, 0, 0x0, 0x0, 3, 0xC, 0xe1a02220],
         [8, 16, 0, 0x0, 0x0, 4, 0x10, 0x0]]), "cpu"),
  ("MOV ASR test",
    TestCase(os.path.join(file_locations,'mov-asr.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a00080],
         [128, 0, 0, 0x0, 0x0, 1, 0x4, 0xe1a01140],
         [128, 32, 0, 0x0, 0x0, 2, 0x8, 0xe3a00040],
         [64, 32, 0, 0x0, 0x0, 3, 0xC, 0xe1a021c0],
         [64, 32, 8, 0x0, 0x0, 4, 0x10, 0x0]]), "cpu"),
  ("MOV AND imm test",
    TestCase(os.path.join(file_locations,'mov-and-i.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a00005],
         [5, 0, 0, 0x0, 0x0, 1, 0x4, 0xe200100b],
         [5, 1, 0, 0x0, 0x0, 2, 0x8, 0xe3a02007],
         [5, 1, 7, 0x0, 0x0, 3, 0xC, 0xe2020008],
         [0, 1, 7, 0x0, 0x0, 4, 0x10, 0x0]]), "cpu"),
  ("MOV ORR imm test",
    TestCase(os.path.join(file_locations,'mov-orr-i.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a000ef],
         [239, 0, 0, 0x0, 0x0, 1, 0x4, 0xe3801010],
         [239, 255, 0, 0x0, 0x0, 2, 0x8, 0xe3a00006],
         [6, 255, 0, 0x0, 0x0, 3, 0xC, 0xe3802009],
         [6, 255, 15, 0x0, 0x0, 4, 0x10, 0x0]]), "cpu"),
  ("MOV EOR imm test",
    TestCase(os.path.join(file_locations,'mov-eor-i.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a00000],
         [0, 0, 0, 0x0, 0x0, 1, 0x4, 0xe2201001],
         [0, 1, 0, 0x0, 0x0, 2, 0x8, 0xe3a00005],
         [5, 1, 0, 0x0, 0x0, 3, 0xC, 0xe2202003],
         [5, 1, 6, 0x0, 0x0, 4, 0x10, 0x0]]), "cpu"),
  ("MOV MVN test",
    TestCase(os.path.join(file_locations,'mov-mvn.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3e00000],
         [0xffffffff, 0, 0, 0x0, 0x0, 1, 0x4, 0xe1e01000],
         [0xffffffff, 0, 0, 0x0, 0x0, 2, 0x8, 0xe3a00008],
         [8, 0, 0, 0x0, 0x0, 3, 0xC, 0xe1e02000],
         [8, 0, 0xfffffff7, 0x0, 0x0, 4, 0x10, 0x0]]), "cpu"),
  ("CMP for conditional adds test",
    TestCase(os.path.join(file_locations,'cond-add.circ'),
        [[0, 0, 0, 0x0, 0x0, 0],
         [11, 0, 0, 0x0, 0x0, 1],
         [11, 22, 0, 0x0, 0x0, 2],
         [11, 22, 0, 0x0, 0x0, 3],
         [22, 22, 0, 0x0, 0x0, 4],
         [22, 22, 0, 0x0, 0x0, 5],
         [44, 22, 0, 0x0, 0x0, 6]]), "cpu-lite"),
  ("CMP for conditional adds-subs test",
    TestCase(os.path.join(file_locations,'cond-add-sub.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a00064],
         [100, 0, 0, 0x0, 0x0, 1, 0x4, 0xe3a01032],
         [100, 50, 0, 0x0, 0x0, 2, 0x8, 0xe1500001],
         [100, 50, 0, 0x0, 0x0, 3, 0xc, 0x00802001],
         [100, 50, 0, 0x0, 0x0, 4, 0x10, 0x10402001],
         [100, 50, 50, 0x0, 0x0, 5, 0x14, 0xe1510002],
         [100, 50, 50, 0x0, 0x0, 6, 0x18, 0x00410002],
         [0, 50, 50, 0x0, 0x0, 7, 0x1c, 0x10810002],
         [0, 50, 50, 0x0, 0x0, 8, 0x20, 0x0]]), "cpu"),
  ("CMP register test",
    TestCase(os.path.join(file_locations,'mov-cmp-reg.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a0000a],
         [10, 0, 0, 0x0, 0x0, 1, 0x4, 0xe3a01014],
         [10, 20, 0, 0x0, 0x0, 2, 0x8, 0xe1500001],
         [10, 20, 0, 0x0, 0x0, 3, 0xc, 0xe3a0200f],
         [10, 20, 15, 0x0, 0x0, 4, 0x10, 0xe1520001],
         [10, 20, 15, 0x0, 0x0, 5, 0x14, 0x0]]), "cpu"),
  ("CMP imm test",
    TestCase(os.path.join(file_locations,'mov-cmp-i.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a02032],
         [0, 0, 50, 0x0, 0x0, 1, 0x4, 0xe3520064],
         [0, 0, 50, 0x0, 0x0, 2, 0x8, 0xd2821032],
         [0, 100, 50, 0x0, 0x0, 3, 0xc, 0xd2821032],
         [0, 100, 50, 0x0, 0x0, 4, 0x10, 0xe1510002],
         [50, 100, 50, 0x0, 0x0, 5, 0x14, 0xa0410002],
         [50, 100, 50, 0x0, 0x0, 6, 0x18, 0x0]]), "cpu"),
  ("B forward test",
    TestCase(os.path.join(file_locations,'branch-forward.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xea000001],
         [0, 0, 0, 0x0, 0x0, 1, 0xC, 0xe3a0201e],
         [0, 0, 30, 0x0, 0x0, 2, 0x10, 0xe3a00028],
         [40, 0, 30, 0x0, 0x0, 3, 0x14, 0x0]]), "cpu"),
  ("B backward test",
    TestCase(os.path.join(file_locations,'branch-backward.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a00001],
         [1, 0, 0, 0x0, 0x0, 1, 0x4, 0xe3a01000],
         [1, 0, 0, 0x0, 0x0, 2, 0x8, 0xe1500001],
         [1, 0, 0, 0x0, 0x0, 3, 0xc, 0x0a000001],
         [1, 0, 0, 0x0, 0x0, 4, 0x10, 0xe2811001],
         [1, 1, 0, 0x0, 0x0, 5, 0x14, 0xeafffffb],
         [1, 1, 0, 0x0, 0x0, 6, 0x0c, 0x0a000001],
         [1, 1, 0, 0x0, 0x0, 7, 0x10, 0xe2811001]]), "cpu"),
  ("Load Register test",
    TestCase(os.path.join(file_locations,'mov-ldr.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0,   0xe3a00014],
         [20, 0, 0, 0x0, 0x0, 1, 0x4,   0xe5800008],
         [20, 20, 0, 0x0, 0x0, 2, 0x8, 0xe5901008],
         [20, 20, 0, 0x0, 0x0, 3, 0xc, 0x0]]), "cpu"),
  ("Store Register test",
    TestCase(os.path.join(file_locations,'mov-str.circ'),
        [[0, 0, 0, 0x0, 0x0, 0, 0x0, 0xe3a0000a],
         [10, 0, 0, 0x0, 0x0, 1, 0x4, 0xe5800004],
         [10, 0, 0, 0x0, 0x0, 2, 0x8, 0xe5901004],
         [10, 10, 0, 0x0, 0x0, 3, 0xc, 0xe281100a],
         [10, 20, 0, 0x0, 0x0, 4, 0x10, 0xe5801008],
         [10, 20, 0, 0x0, 0x0, 5, 0x14, 0xe5902008],         
         [10, 20, 20, 0x0, 0x0, 6, 0x18, 0x0]]), "cpu"),
         ]

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(("Usage: " + sys.argv[0] + " (p1|p2|p2sc)"))
        sys.exit(-1)
    if sys.argv[1] == 'p1':
        run_tests(p1_tests)
    elif sys.argv[1] == 'p2sc':
        run_tests(p2sc_tests)
    else:
        print(("Usage: " + sys.argv[0] + " (p1|p2sc)"))
        sys.exit(-1)
