Please e-mail Lavanya Jose (lavanyaj@cs.stanford.edu) for questions about the code.

# Dependencies #

For P4 programs, install p4-hlir

For dependency analysis, download python-graph

 - git clone https://github.com/pmatiello/python-graph.git

 - cd python-graph

 - sudo make install-core

You may also need

sudo apt-get install python-matplotlib

sudo apt-get install python-pygraph

# Code overview #
The code is organized as follows-

For each target, we have a compiler, switch, preprocessor,
and configuration module. We also have a program module that defines the annotated TDG format
for a program, and different use cases based on this.
The compiler takes as in put an instance of the program, switch and preprocessor module
and returns a configuration module, populated with the switch configuration it found.

You can play around with different switch parameters by describing your own switch module in config / switch00.txt. 

You can also explore different compiler configurations by describing your compiler module in config / comp00.txt.

# Compiling programs/ TDGs #

## To compile a P4 program ##

cd mapper/parser

python p4-compile.py -h   

## To compile a TDG version of program (e.g., those in mapper/tdg_programs) ##

cd mapper/parser

python tdg-compile.py -h


## Some examples: ##

Compiling L2L3Simple to RMT using FFD heuristic-

python tdg-compile.py -c RmtFfdCompiler-16 -p ProgramL2L3Simple -s RmtReal32 -r RmtPreprocess --log_level INFO

Compiling L2L3Simple to RMT using ILP-

python tdg-compile.py -c RmtIlpCompiler-020 -p ProgramL2L3Simple -s RmtReal32 -r RmtPreprocess --log_level INFO

Compiling DdSmall (smaller version of L2L3Simple) to FlexPipe using heuristic-

python tdg-compile.py -c FlexpipeLptCompiler -p ProgramDdSmall -s FlexpipeReal -r FlexpipePreprocess --log_level INFO

Compiling DdSmall (smaller version of L2L3Simple) to FlexPipe using ILP-

python tdg-compile.py -c FlexpipeIlpCompiler -p ProgramDdSmall -s FlexpipeReal -r FlexpipePreprocess --log_level INFO

Compiling a P4 program /Users/lav/p4factory/targets/dc_example/p4src/dc_example.p4 to RMT using FFD heuristic

python p4-compile.py -p /Users/lav/p4factory/targets/dc_example/p4src/dc_example.p4 -c RmtFfdCompiler-16  -s RmtReal32 -r RmtPreprocess

Compiling example P4 program mapper/p4_programs/l2l3_nsdi/p4src/l2l3_nsdi.p4
python p4-compile.py -p mapper/p4_programs/l2l3_nsdi/p4src/l2l3_nsdi.p4 -c RmtFfdCompiler-16  -s RmtReal32 -r RmtPreprocess 

## Using ILP ##

You need to install CPLEX and pycpx (see ilp_setup.txt) first.