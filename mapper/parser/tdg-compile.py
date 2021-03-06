#
# Copyright (c) 2015-2016 by The Board of Trustees of the Leland
# Stanford Junior University.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
#  Author: Lavanya Jose (lavanyaj@cs.stanford.edu)
#
#

from parse import *

cwd = os.getcwd() + "/"

# DEFAULT
default_log_directory = cwd
default_log_level = "INFO"

possible_compilers = getKeysInConfigFile(default_compiler_file)
possible_switches = getKeysInConfigFile(default_switch_file)
possible_programs = getKeysInConfigFile(default_program_file)
possible_preprocessors = getKeysInConfigFile(default_preprocessor_file)


description_string = "Compile a program to switch using preprocessor.\n"\
    + "Required arguments: compiler, switch, program, preprocess.\n"\
    + "e.g., python %s -c %s -p %s -s %s -r %s" %\
    ("tdg-compile.py", possible_compilers[0], possible_programs[0],\
         possible_switches[0], possible_preprocessors[0])

parser = argparse.ArgumentParser(description=description_string,
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)

# REQUIRED
parser.add_argument('-c','--compiler', required=True, type=str,
                    help='compiler name (examples from default config file: '\
                         + str(possible_compilers[:3]))
parser.add_argument('-p', '--program', required=True, type=str, help='program name (examples from default config file: '\
                        + str(possible_programs[:3]))                        
parser.add_argument('-s', '--switch', required=True, type=str, help='switch name (examples from default config file: '\
                        + str(possible_switches[:3]))
parser.add_argument('-r', '--preprocessor', required=True, type=str, help='preprocessor name (examples: '\
                        + str(possible_preprocessors[:3]))
                        
# CONFIG FILES
parser.add_argument('-C', '--compiler_file', type=str,\
                    default=default_compiler_file, required=False, help='compiler config file name')
parser.add_argument('-P', '--program_file', type=str,\
                    default=default_program_file, required=False,help='program config file name')
parser.add_argument('-S', '--switch_file', type=str,\
                    default=default_switch_file, required=False, help='switch config file name')
parser.add_argument('-R', '--preprocessor_file', type=str,\
                    default=default_preprocessor_file, required=False,help='preprocess config file name')

# OUTPUT CONFIG
parser.add_argument('-n', '--run', required=False, type=str, help='run id')
parser.add_argument('-F', '--picture_prefix', type=str,\
                    required=False,help='output directory for pictures (no pictures output if not specified)')
parser.add_argument('-d', '--log_directory', type=str,\
                    default=default_log_directory, required=False,help='output directory for log')
parser.add_argument('--log_level', required=False, default=default_log_level, type=str, help="DEBUG/INFO/WARN/ERROR/CRITICAL")

# FLEXPIPE ILP COMPILER SPECIFIC
parser.add_argument('-g', '--flexpipe_granularity', type=int, required=False,
                    help='e.g., each table in a block has at least as many rows, e.g., 1000 or 500 or 100')

# RMT ILP COMPILER SPECIFIC
parser.add_argument('--compiler_mipstartFile', required=False, type=str, help="starting solution for ILP compiler")
parser.add_argument('--compiler_objectiveStr', required=False, type=str, help="objectiveStr for ILP compiler")
parser.add_argument('--compiler_relativeGap', required=False, type=float, help="relative gap for ILP compiler")
parser.add_argument('--compiler_outputFileName', required=False, type=str, help="output file for MIP start etc.")

args = parser.parse_args()
print args
print args.picture_prefix

def getFile(path):
    return os.path.split(path)[-1]
    pass

# GENERATE LOG FILE NAME
try:
    jobId= "_".join([("%s" % (module[1])) for module in\
                         [(getFile(args.compiler_file), args.compiler),\
                              (getFile(args.program_file), args.program),\
                              (getFile(args.switch_file), args.switch)]])

#     jobId= "_".join(["%s-%s" % (module[0], module[1]) for module in\
#                          [(getFile(args.compiler_file), args.compiler),\
#                               (getFile(args.program_file), args.program),\
#                               (getFile(args.switch_file), args.switch),\
#                               (getFile(args.preprocessor_file), args.preprocessor)]])
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
except:
    print "Could not generate log file name "
    traceback.print_exc()
    print "Error! Exiting!"
    exit()
    pass

# SETUP LOGGING
try:
    import logging
    numeric_level = getattr(logging, args.log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    print "Logging level is %d" % numeric_level
    logging.basicConfig(level=numeric_level, filename=logFile, filemode='w')

    logging.info("This log has several sections separated by ~~: Switch Info, JobId, Program Info, Compiler Log, Final switch configurations")
except:
    print "Could not setup logging "
    traceback.print_exc()
    print "Error! Exiting!"
    exit()
    pass

try:
    logging.info("~~")
    logging.info("Switch Info")
    query = makeQuery(args.compiler, args.switch, args.preprocessor, args.program)

    query['compiler']['configFile'] = args.compiler_file
    query['switch']['configFile'] = args.switch_file
    query['preprocess']['configFile'] = args.preprocessor_file
    query['program']['configFile'] = args.program_file
    query = getModules(query)
except:
    logging.error("ERROR!!! Could not get valid compiler, switch, preprocessor modules ")
    logging.error(traceback.format_exc())
    print "Error! Exiting! Check log file"
    exit()
    pass    

logging.info("~~")
logging.info("JobId: " + jobId)

try:
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
            compiler.writeLevel = numeric_level
            logging.info("UPDATED COMPILER WRITE LEVEL TO %d" % compiler.writeLevel)
            pass
        pass
except:
    logging.error("ERROR!!! Could not set up compiler module using command line options ")
    logging.error(traceback.format_exc())
    print "Error! Exiting! Check log file"
    exit()
    pass

switch = query['switch']['module']
preprocess =  query['preprocess']['module']
program = query['program']['module']

# DISPLAY PROGRAM INFO
try:
    logging.info("~~")
    logging.info("Program Info")
    program.showProgramInfo()
except:
    logging.error("ERROR!!! Could not output program info ")
    logging.error(traceback.format_exc())
    print "Error! Exiting! Check log file"
    exit()
    pass
    
# PREPROCESS
try:
    preprocess.preprocess(program=program, switch=switch)
except:
    logging.error("ERROR!!! Could not preprocess program and switch ")
    logging.error(traceback.format_exc())
    print "Error! Exiting! Check log file"
    exit()
    pass


# COMPILE
try:
    logging.info("")
    logging.info("~~")
    logging.info("Compiler Log")
    start = time.time()
    configs = compiler.solve(program=program, switch=switch, preprocess=preprocess)
    end = time.time()
    logging.info("Finished compiling")
except:
    exc_info = sys.exc_info()
    logging.error("ERROR!!! Compiler terminated unexpectedly ")
    logging.error(traceback.format_exc())
    print "Error! Exiting! Check log file"
    exit()
    pass

logging.info("")
logging.info("~~")
logging.info("Final switch configurations")
for k in configs.keys():
    logging.info("~~")
    logging.info("\nDisplaying config for %s" % k)
    config = configs[k]

    try:
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
        
        #logging.info("Setup")
        #config.displayInitialConditions()
    except:
        logging.error("ERROR!!! Error outputting compiler results")
        logging.error(traceback.format_exc())
        print "Error! Exiting! Check log file"
        exit()
        pass
    pass

if args.picture_prefix is not None:
    # GET PICTURE VERSION OF FINAL SWITCH MAPPING
    try:
        listKeys = sorted(configs.keys())
        for k in listKeys:
            logging.info("picture in %s-%s.pdf" % (args.picture_prefix, k+'-'+jobId))
            configs[k].showPic(prefix=args.picture_prefix, filename=k+'-'+jobId)
            pass
        pass
    except:
        logging.error("ERROR!!! Error converting compilers results to PDF picture")
        logging.error(traceback.format_exc())
        print "Error! Exiting! Check log file"
        exit()
    pass

sortedKeys = sorted(compiler.results.keys())
string = ""
for k in sortedKeys:
    string += str(k) +": " + str(compiler.results[k]) + ", "
    pass
string += "time: %f" % (end - start)
logging.critical("Summary: " + string)
pass


