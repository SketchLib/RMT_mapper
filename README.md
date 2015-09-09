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


# Compiling Programs #

## To compile a P4 program ##

cd mapper/parser

python p4-compile.py -h   

## To compile a TDG version of program (e.g., those in mapper/tdg_programs) ##

cd mapper/parser

python tdg-compile.py -h


## Some examples: ##

Compiling L2L3Simple to RMT using FFD heuristic-

python tdg-compile.py -c RmtFfdCompiler-16 -p ProgramL2L3Simple -s RmtReal32 -r RmtPreprocess --log_level INFO

Compiling DdSmall (smaller version of L2L3Simple) to FlexPipe using heuristic-

python tdg-compile.py -c FlexpipeLptCompiler -p ProgramDdSmall -s FlexpipeReal -r FlexpipePreprocess --log_level INFO

Compiling a P4 program /Users/lav/p4factory/targets/dc_example/p4src/dc_example.p4 to RMT using FFD heuristic

python p4-compile.py -p /Users/lav/p4factory/targets/dc_example/p4src/dc_example.p4 -c RmtFfdCompiler-16  -s RmtReal32 -r RmtPreprocess

Compiling example P4 program mapper/p4_programs/l2l3_nsdi/p4src/l2l3_nsdi.p4
python p4-compile.py -p mapper/p4_programs/l2l3_nsdi/p4src/l2l3_nsdi.p4 -c RmtFfdCompiler-16  -s RmtReal32 -r RmtPreprocess 

## Using ILP ##

You need to install CPLEX and pycpx (see ilp_setup.txt) first.
