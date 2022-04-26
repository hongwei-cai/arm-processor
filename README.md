# ARM CPU

Description

## Assembling ARM assembly code into Logisim's plain text hexadecimal format

1. Download and unzip the [ARM Embedded Toolchain](https://developer.arm.com/tools-and-software/open-source-software/developer-tools/gnu-toolchain/gnu-rm/downloads)

Note that .tar.bz2 files can be unzipped with this command

tar xvf nameofmyfile.tar.bz2

2. inside that unzipped folder is a bin directory containing all the compiler programs. For your command line to see those programs, you need to put the path to the bin directory on your PATH environment variable. For example, on Linux, if the folder is called gcc-arm-none-eabi-10.3-2021.10 and it is in your home directory.

export PATH=$PATH:$HOME/gcc-arm-none-eabi-10.3-2021.10/bin

3. cd into the project2-arm-processor directory

./arm-assem.sh nameofyoursourcefile.s
