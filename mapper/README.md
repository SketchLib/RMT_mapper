for P4 programs, install p4-hlir

for dependency analysis, download python-graph

 - git clone https://github.com/pmatiello/python-graph.git

 - cd python-graph

 - sudo make install-core

You may also need

sudo apt-get install python-matplotlib

sudo apt-get install python-pygraph


make symbolic link to mapper directory in mapper/parser, call it mapper

 e.g., ln -s path_to_mapper_directory mapper

COMPILING PROGRAMS

To compile a P4 program

cd mapper/parser

python p4-compile.py -h   

To compile a TDG version of program (e.g., those in mapper/tdg_programs)

cd mapper/parser

python tdg-compile.py -h


Some examples:

Compiling L2L3Simple to RMT using FFD heuristic-

python tdg-compile.py -c RmtFfdCompiler-16 -p ProgramL2L3Simple -s RmtReal32 -r RmtPreprocess --log_level INFO

Compiling DdSmall (smaller version of L2L3Simple) to FlexPipe using heuristic-

python tdg-compile.py -c FlexpipeLptCompiler -p ProgramDdSmall -s FlexpipeReal -r FlexpipePreprocess --log_level INFO


USING ILP

You need to install CPLEX and pycpx (see ilp_setup.txt) first.

