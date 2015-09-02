import tp
from common import *
from programs.program import Program # mapper

def getProgram(input_hlir, loglevel, compile_option=INGRESS_ONLY):
    pi = tp.getProgramInfo(input_hlir, loglevel, compile_option)
    program = Program(logicalTables=pi["num_entries"],\
			logicalTableWidths=pi["widths"],\
			logicalMatchDependencyList=pi["matchDependencies"],\
			logicalSuccessorDependencyList=pi["successorDependencies"],\
			logicalActionDependencyList=pi["actionDependencies"],\
			matchType=pi["match_types"],\
			names=pi["table_names"])
    return program			
			
