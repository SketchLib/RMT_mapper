Please e-mail Lavanya Jose (lavanyaj@cs.stanford.edu) for questions about the code.

# Dependencies #

Here are instructions to setup on Linux (you can also setup on Mac)

Here is what I needed to compile TDGs using greedy heuristics 

```
#!sh
sudo apt-get install python-numpy python-matplotlib python-pygraph
```

Now you should be able to to compile TDGs using greedy heuristics and also view the configurations in PDF-

```
#!sh

# Compiling L2L3Simple program to RMT using FFD heuristic-
python tdg-compile.py -c RmtFfdCompiler-16 -p ProgramL2L3Simple -s RmtReal32 -r RmtPreprocess --log_level INFO --picture_prefix ./

# Compiling DdSmall (smaller version of L2L3Simple) program to Flexpipe using its only greedy heuristic-
python tdg-compile.py -c FlexpipeLptCompiler -p ProgramDdSmall -s FlexpipeReal -r FlexpipePreprocess --log_level INFO --picture_prefix ./

```

To compile P4-programs using greedy heuristics you also need to install [p4-hlir](https://github.com/p4lang/p4-hlir)

```
#!sh
# cd to directory you want then
git clone https://github.com/p4lang/p4-hlir.git
cd p4-hlir
sudo apt-get install python-setuptools
sudo python setup.py install
# or if you don't have sudo permissions, python setup.py install --user
sudo apt-get install gcc
```

Now you should be able to to compile P4 programs in the mapper/p4_programs directory using greedy heuristics, and also view the configurations in PDF-

```
#!sh
# Compiling a P4 program /Users/lav/p4factory/targets/dc_example/p4src/dc_example.p4 to RMT using FFD heuristic
python p4-compile.py -p ../p4_programs/l2l3_nsdi/p4src/l2l3_nsdi.p4 -c RmtFfdCompiler-16  -s RmtReal32 -r RmtPreprocess --picture_prefix ./
```

To compile programs using the ILP compilers, you'll need to install 

1. The ILP solver CPLEX (a free version is available for academics, it's already installed on the Stanford farmshare cluster)

2. A Python wrapper for CPLEX called [pycpx](http://www.stat.washington.edu/~hoytak/code/pycpx/) developed by Hoyt Koepke at University of Washington, licensed under LGPL open source license. I modified this slightly and you should download pycpx from [here](https://github.com/lavanyaj/pycpx) instead.

Instructions to install CPLEX and pycpx in ilp_setup.txt

Once that is done, you can run commands like the following

```
#!sh
# Compiling DdSmall (smaller version of L2L3Simple) to FlexPipe using ILP-
python tdg-compile.py -c FlexpipeIlpCompiler -p ProgramDdSmall -s FlexpipeReal -r FlexpipePreprocess --log_level INFO
```

# Code overview #
The code is organized as follows-

For each target, we have a compiler, switch, preprocessor,
and configuration module. We also have a program module that defines the annotated TDG format
for a program, and different use cases based on this.
The compiler takes as in put an instance of the program, switch and preprocessor module
and returns a configuration module, populated with the switch configuration it found.

You can play around with different switch parameters by describing your own switch module in config / switch00.txt. 

You can also explore different compiler configurations by describing your compiler module in config / comp00.txt.


## Some more examples: ##

```
#!sh

# Compiling L2L3Simple to RMT using ILP-
python tdg-compile.py -c RmtIlpCompiler-020 -p ProgramL2L3Simple -s RmtReal32 -r RmtPreprocess --log_level INFO

# Compiling a P4 program ~/p4factory/targets/switch/p4src/switch.p4 to a 14-stage RMT using ILP, optimizing for power
python p4-compile.py -p /Users/lav/p4factory/targets/dc_example/p4src/dc_example.p4 -c RmtFfdCompiler-16  -s RmtReal32 -r RmtPreprocess
 python p4-compile.py -p ~/p4factory/targets/switch/p4src/switch.p4 -c RmtIlpCompiler-020 -s RmtReal14 -r RmtPreprocess --picture_prefix ./ --compiler_objectiveStr powerForRamsAndTcams
```