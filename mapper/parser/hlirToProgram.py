import tp
from mapper.programs.program import Program

def getProgram(input_hlir, loglevel):
    pi = tp.getProgramInfo(input_hlir, loglevel)
    program = Program(logicalTables=pi["num_entries"],\
			logicalTableWidths=pi["widths"],\
			logicalMatchDependencyList=pi["matchDependencies"],\
			logicalSuccessorDependencyList=pi["successorDependencies"],\
			logicalActionDependencyList=pi["actionDependencies"],\
			matchType=pi["match_types"],\
			names=pi["table_names"])
    return program			
			
