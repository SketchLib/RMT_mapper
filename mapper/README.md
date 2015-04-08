for P4 programs, install p4-hlir
for dependency analysis, download python-graph
 - git clone https://github.com/pmatiello/python-graph.git
 - cd python-graph
 - sudo make install-core
make symbolic link to mapper directory in backend/mapper/parser, call it mapper
 e.g., ln -s path_to_mapper_directory mapper

COMPILING PROGRAMS

to RMT using a greedy heuristic
 - in backend/mapper/parser
    python quick_rmt_greedy ffl|ffd path_to_p4_program

to FlexPipe using a greedy heuristic
 - in backend/mapper/parser
    python quick_flexpipe_greedy path_to_p4_program

