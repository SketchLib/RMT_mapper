import tp
from common import *
from programs.program import Program

def getProgram(input_hlir, loglevel, pipeline_option=INGRESS_ONLY):
    pi = tp.getProgramInfo(input_hlir, loglevel, pipeline_option)
    program = Program(logicalTables=pi["num_entries"],\
			logicalTableWidths=pi["widths"],\
                        logicalTableActionWidths=pi["action_widths"],\
                        logicalMatchDependencyList=pi["matchDependencies"],\
			logicalSuccessorDependencyList=pi["successorDependencies"],\
			logicalActionDependencyList=pi["actionDependencies"],\
			matchType=pi["match_types"],\
			names=pi["table_names"],
            hashDistUnitList=pi['hash_dist_unit'],
			saluList=pi['salu'],
			registerSizeList=pi['register_size'],
			registerWidthList=pi['register_width'],)
    return program			
			
