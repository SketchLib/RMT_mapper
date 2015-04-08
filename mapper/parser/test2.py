import math
import argparse
import os
import time

parser = argparse.ArgumentParser(description='Compile program to switch.\
e.g., test2.py FlexpipeIlpCompilerLpt90 FlexpipeReal ProgramDdSmall FlexpipePreprocess --switch_file \'mapper/config/dd_small11.txt\' OR\
 test2.py RmtIlpCompilerFfd90 RmtReal ProgramDdLarge RmtPreprocess')
parser.add_argument('-c','--compiler', required=True, type=str, help='compiler name')
parser.add_argument('-s', '--switch', required=True, type=str, help='switch name')
parser.add_argument('-p', '--program', required=True, type=str, help='program name')
parser.add_argument('-r', '--preprocess', required=True, type=str, help='preprocess name') 
parser.add_argument('-n', '--run', required=False, type=str, help='run id')
parser.add_argument('-C', '--compiler_file', type=str,\
                    default='mapper/config/comp00.txt', required=False, help='compiler file name')
parser.add_argument('-S', '--switch_file', type=str,\
                    default='mapper/config/switch00.txt', required=False, help='switch file name')
parser.add_argument('-P', '--program_file', type=str,\
                    default='mapper/config/prog00.txt', required=False,help='program file name')
parser.add_argument('-R', '--preprocess_file', type=str,\
                    default='mapper/config/prep00.txt', required=False,help='preprocess file name')
parser.add_argument('-F', '--picture_prefix', type=str,\
                    required=False,help='output directory for pictures')
parser.add_argument('-d', '--log_directory', type=str,\
                    required=True,help='output directory for log')

parser.add_argument('-g', '--flexpipe_granularity', type=int, required=False,help='e.g., 1000 or 500 or 100')

parser.add_argument('--compiler_mipstartFile', required=False, type=str, help="starting solution for ILP compiler")

parser.add_argument('--compiler_objectiveStr', required=False, type=str, help="objectiveStr for ILP compiler")
parser.add_argument('--compiler_relativeGap', required=False, type=float, help="relative gap for ILP compiler")
parser.add_argument('--log_level', required=False, default="INFO", type=str, help="DEBUG/INFO/WARN/ERROR/CRITICAL")
parser.add_argument('--compiler_outputFileName', required=False, type=str, help="output file for MIP start etc.")

args = parser.parse_args()
print args
print args.picture_prefix

def getFile(path):
    return os.path.split(path)[-1]
    pass

jobId= "_".join(["%s-%s" % (module[0], module[1]) for module in\
                 [(getFile(args.compiler_file), args.compiler),\
                  (getFile(args.program_file), args.program),\
                  (getFile(args.switch_file), args.switch),\
                  (getFile(args.preprocess_file), args.preprocess)]])
if args.run is not None:
    jobId += "_%s" % args.run
    pass


addArgs = {'compiler_objectiveStr': args.compiler_objectiveStr,\
               'compiler_relativeGap': args.compiler_relativeGap,\
               'compiler_outputFileName': args.compiler_outputFileName}
addArgsStr = ""
for name in addArgs:
    if  addArgs[name] is not None:
        addArgsStr += "_%s=%s" % (name, addArgs[name])
        pass
    pass

if len(addArgsStr) > 0:
    jobId += addArgsStr
    pass

logFile = args.log_directory + jobId + ".log"
print "logFile: " + logFile
import logging
numeric_level = getattr(logging, args.log_level.upper(), None)
if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % loglevel)
print "Logging level is %d" % numeric_level
logging.basicConfig(level=numeric_level, filename=logFile, filemode='w')


from parse import *


#    things = getThings(makeThings('FlexpipeIlpCompilerLpt90','FlexpipeReal','ProgramDdSmall',\
#                                      'FlexpipePreprocess'))
#    query = makeQuery('RmtIlpCompilerFfl90','RmtReal32','ProgramL2L3Complex',\
#                'RmtPreprocess')

# test.py FlexpipeIlpCompilerLpt90 FlexpipeReal ProgramDdSmall FlexpipePreprocess --switch_file 'mapper/config/dd_small11.txt'
query = makeQuery(args.compiler, args.switch, args.program, args.preprocess)

query['compiler']['configFile'] = args.compiler_file
query['switch']['configFile'] = args.switch_file
query['preprocess']['configFile'] = args.preprocess_file
query['program']['configFile'] = args.program_file
query = getModules(query)
    
logging.info(jobId)
logging.debug("This is in file?")
# Gives you a compiler, switch, preprocess and program
compiler = query['compiler']['module']
# jugaad to enter objective in command line
if not args.compiler_objectiveStr == None:
    compiler.objectiveStr = args.compiler_objectiveStr
    logging.info("UPDATED COMPILER OBJECTIVE STR TO %s" % args.compiler_objectiveStr)
    pass
if not args.compiler_mipstartFile == None:
    compiler.mipstartFile = args.compiler_mipstartFile
    logging.info("UPDATED COMPILER MIP START FILE TO %s" % args.compiler_mipstartFile)
    pass
if not args.compiler_relativeGap == None:
    compiler.relativeGap = args.compiler_relativeGap
    logging.info("UPDATED COMPILER RELATIVE GAP TO %s" % args.compiler_relativeGap)
    pass

if 'outputFileName' in vars(compiler):
    compiler.outputFileName = args.log_directory + jobId
    logging.info("UPDATED COMPILER OUTPUT FILE TO %s" % compiler.outputFileName)
    if 'writeLevel' in vars(compiler):
        compiler.writeLevel = 1
        logging.info("UPDATED COMPILER WRITE LEVEL TO %d" % compiler.writeLevel)
        pass
    pass

switch = query['switch']['module']
preprocess =  query['preprocess']['module']
program = query['program']['module']

if args.flexpipe_granularity is not None:
    g = args.flexpipe_granularity
    for mem in switch.memoryTypes:
        if switch.depth[mem] >= g:
            switch.depth[mem] = int(math.floor(switch.depth[mem]/float(g)))
            pass
        else:
            switch.depth[mem] = 1
            logging.info("UPDATED SWITCH %s DEPTH TO 1!!" % mem)
            pass

        pass

    for log in range(program.MaximumLogicalTables):
        #program.logicalTables[log] = int(math.ceil(program.logicalTables[log]/float(g)))
        program.logicalTables[log] = round(program.logicalTables[log]/float(g), 3)
        print program.logicalTables[log] 
        if program.logicalTables[log] < 1.0:
            program.logicalTables[log] = 1.0
        pass

    newSizes = ["%s: %.3f" % (program.names[log], program.logicalTables[log]) for log in range(program.MaximumLogicalTables)]
    logging.info("UPDATED SWITCH MEM DEPTHS to floor( . / %.1f) (or 1): %s" % (args.flexpipe_granularity, switch.depth))
    logging.info("UPDATED PROGRAM TABLE SIZES to ceil( . / %.1f) (or 1): %s" % (args.flexpipe_granularity, newSizes))
    pass

preprocess.preprocess(program=program, switch=switch)
start = time.time()
configs = compiler.solve(program=program, switch=switch, preprocess=preprocess)
end = time.time()

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
    pass

if args.picture_prefix is not None:
    listKeys = sorted(configs.keys())
    for k in listKeys:
        logging.info("picture in %s%s.pdf" % (args.picture_prefix, k+'-'+jobId))
        configs[k].showPic(prefix=args.picture_prefix, filename=k+'-'+jobId)
        pass
    pass

sortedKeys = sorted(compiler.results.keys())
string = ""
for k in sortedKeys:
    string += str(k) +": " + str(compiler.results[k]) + ", "
    pass
string += "time: %f" % (end - start)
logging.critical(string)
pass


