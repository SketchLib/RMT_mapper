import sys
import os

from p4_hlir.main import HLIR
import hlirToProgram

from mapper.src.rmt.rmt_switch import RmtSwitch

from mapper.src.rmt.rmt_preprocess import RmtPreprocess
import logging

logging.basicConfig()

if (len(sys.argv) < 2):
    logging.error("Usage: quick_rmt_greedy.py ffl|ffd path_to_p4_program\n")
    exit()

numSramBlocksReserved = 16
preprocess = RmtPreprocess()
switch = RmtSwitch()

if (sys.argv[1] == 'ffl'):
    from mapper.src.rmt.rmt_ffl_compiler import RmtFflCompiler
    compiler = RmtFflCompiler(numSramBlocksReserved)
    pass
elif (sys.argv[1] == 'ffd'):
    from mapper.src.rmt.rmt_ffd_compiler import RmtFfdCompiler
    compiler = RmtFfdCompiler(numSramBlocksReserved)
    pass
else:
    logging.error("Unrecognized RMT greedy compiler: must be ffl or ffd.\n")
    exit()

h = HLIR(sys.argv[2])
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

    p4FileName = os.path.split(sys.argv[2])[-1]
    pictureName = "%s-rmtGreedy-%s-%s"%(p4FileName,sys.argv[1],k)
    logging.info("Picture at %s, filename %s.pdf" % (os.getcwd(), p4FileName))
    configs[k].showPic(prefix=os.getcwd()+"/",filename=pictureName)
    pass


