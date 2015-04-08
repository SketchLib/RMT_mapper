import sys
import os

from p4_hlir.main import HLIR
import hlirToProgram

from mapper.src.flexpipe.flexpipe_switch import FlexpipeSwitch

from mapper.src.flexpipe.flexpipe_preprocess import FlexpipePreprocess
import logging

logging.basicConfig()

if (len(sys.argv) < 2):
    logging.error("Usage: quick_flexpipe_greedy.py path_to_p4_program\n")
    exit()


preprocess = FlexpipePreprocess()
switch = FlexpipeSwitch()


from mapper.src.flexpipe.flexpipe_lpt_compiler import FlexpipeLptCompiler
compiler = FlexpipeLptCompiler()

h = HLIR(sys.argv[1])
h.build()
program = hlirToProgram.getProgram(h)

preprocess.preprocess(program=program, switch=switch)
configs = compiler.solve(program=program, switch=switch, preprocess=preprocess)

for k in configs.keys():
    logging.info("\ndisplaying config for %s" % k)
    config = configs[k]

    da = config.da
    criticalPath = da.showCriticalPath()
    progInfo = da.getPerLogProgramInfo()
    assignInfo = config.getPerLogAssignInfo()

    config.display()
    logging.info("\nCritical path: %s" % (da.showPath(criticalPath, assignInfo)))

    index = 1
    logging.info("Tables that start later than expected")
    for table in program.names:
        canStart = progInfo[table]['earliestStage']
        startsIn = assignInfo[table]['start']
        if startsIn > canStart:
            longestPath = progInfo[table]['longestPathFromStart']
            pathStr = da.showPath(longestPath, assignInfo)
            msg = "%d) %s can start in %d, but starts in %d. " % (index, table, canStart, startsIn)
            logging.info(msg)
            index += 1
            pass
        pass
    config.displayInitialConditions()

    p4FileName = os.path.split(sys.argv[1])[-1]
    pictureName = "%s-flexpipeGreedy-%s"%(p4FileName,k)
    logging.info("Picture at %s, filename %s.pdf" % (os.getcwd(), p4FileName))
    configs[k].showPic(prefix=os.getcwd()+"/",filename=pictureName)
    pass


