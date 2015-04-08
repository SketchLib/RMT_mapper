import sys
import os
import tp

from p4_hlir.main import HLIR
import hlirToProgram

import logging

logging.basicConfig()

if (len(sys.argv) < 2):
    logging.error("Usage: show_program_info.py path_to_p4_program\n")
    exit()


h = HLIR(sys.argv[1])
h.build()
program = tp.showProgramInfo(h)
