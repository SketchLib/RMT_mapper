import logging

def getRmtSwitch(d):
    from mapper.src.rmt.rmt_switch import RmtSwitch
    # try catch key not in dict
    matchType = {'sram':['exact'], 'tcam':['exact', 'lpm', 'ternary']}
    if 'matchType' in d:
        matchType = d['matchType']
        pass

    switch = RmtSwitch(numSlices = d['numSlices'], depth = d['depth'], width = d['width'],\
                           numStages = d['numStages'],\
                           inputCrossbarNumSubunits = d['inputCrossbarNumSubunits'],\
                           inputCrossbarWidthSubunit=d['inputCrossbarWidthSubunit'],\
                           actionCrossbarNumBits=d['actionCrossbarNumBits'],\
                           matchTablesPerStage=d['matchTablesPerStage'],\
                           unpackableMemTypes=d['unpackableMemTypes'],\
                           delays=d['delays'], matchType=matchType)
    
    return switch

def getProgramDcUnify(d):
    from mapper.programs.dc_unify import ProgramDcUnify
    program = ProgramDcUnify(numberOfEntriesDict=d['numberOfEntriesDict'])
    return program.program

def getProgramL2L3SimpleMtag(d):
    from mapper.programs.l2l3_simple_mtag import ProgramL2L3SimpleMtag
    program = ProgramL2L3SimpleMtag(numberOfEntriesDict=d['numberOfEntriesDict'])
    return program.program

def getProgramL2L3Simple(d):
    from mapper.programs.l2l3_simple import ProgramL2L3Simple
    program = ProgramL2L3Simple(numberOfEntriesDict=d['numberOfEntriesDict'])
    return program.program

def getProgramL2L3Complex(d):
    from mapper.programs.l2l3_complex import ProgramL2L3Complex
    program = ProgramL2L3Complex(numberOfEntriesDict=d['numberOfEntriesDict'])
    return program.program

def getProgramL3Dc(d):
    from mapper.programs.l3_dc import ProgramL3Dc
    program = ProgramL3Dc(numberOfEntriesDict=d['numberOfEntriesDict'])
    return program.program

def getRmtFflCompiler(d):
    from mapper.src.rmt.rmt_ffl_compiler import RmtFflCompiler
    numSramBlocksReserved = 0
    if 'numSramBlocksReserved' in d:
        numSramBlocksReserved = d['numSramBlocksReserved']
        pass
    compiler = RmtFflCompiler(numSramBlocksReserved)
    return compiler

def getRmtFflsCompiler(d):
    from mapper.src.rmt.rmt_ffls_compiler import RmtFflsCompiler
    numSramBlocksReserved = 0
    if 'numSramBlocksReserved' in d:
        numSramBlocksReserved = d['numSramBlocksReserved']
        pass
    compiler = RmtFflsCompiler(numSramBlocksReserved)
    return compiler

def getRmtFfdCompiler(d):
    from mapper.src.rmt.rmt_ffd_compiler import RmtFfdCompiler
    numSramBlocksReserved = 0
    if 'numSramBlocksReserved' in d:
        numSramBlocksReserved = d['numSramBlocksReserved']
        pass
    compiler = RmtFfdCompiler(numSramBlocksReserved)
    return compiler

def getRmtIlpCompiler(d):
    from mapper.src.rmt.orig_rmt_compiler import RmtIlpCompiler
    for k in ['timeLimit','treeLimit','emphasis','variableSelect',\
                  'workMem', 'nodeFileInd', 'workDir', 'ignoreConstraint',\
                   'relativeGap', 'epagap', 'solnpoolintensity',\
                    'populateLimit']:
        if k not in d:
            d[k] = None
            pass
        pass

    if 'greedyVersion' not in d:
        d['greedyVersion'] = ""
        pass
    compiler = RmtIlpCompiler(relativeGap=d['relativeGap'],\
                                  epagap = d['epagap'],\
                                  greedyVersion=d['greedyVersion'],\
                                  timeLimit=d['timeLimit'],\
                                  treeLimit=d['treeLimit'],\
                                  emphasis=d['emphasis'],\
                                  populateLimit = d['populateLimit'],\
                                  solnpoolintensity = d['solnpoolintensity'],\
                                  variableSelect=d['variableSelect'],\
                                  workMem=d['workMem'],\
                                  nodeFileInd=d['nodeFileInd'],\
                                  workDir=d['workDir'],\
                                  ignoreConstraint=d['ignoreConstraint'])
    return compiler

def getRmtLpCompiler(d):
    from mapper.src.rmt.rmt_lp_compiler import RmtLpCompiler
    if 'greedyVersion' not in d:
        d['greedyVersion'] = ""
        pass
    compiler = RmtLpCompiler(relativeGap=d['relativeGap'],\
                                  greedyVersion=d['greedyVersion'])
    return compiler

def getRmtLpOnlyCompiler(d):
    from mapper.src.rmt.rmt_lp_only_compiler import RmtLpOnlyCompiler
    if 'greedyVersion' not in d:
        d['greedyVersion'] = ""
        pass
    compiler = RmtLpOnlyCompiler(relativeGap=d['relativeGap'],\
                                  greedyVersion=d['greedyVersion'])
    return compiler


def getRmtPreprocess(d):
    from mapper.src.rmt.rmt_preprocess import RmtPreprocess
    preprocess = RmtPreprocess()
    return preprocess

def getFlexpipeSwitch(d):
    from mapper.src.flexpipe.flexpipe_switch import FlexpipeSwitch
    # try catch key not in dict
    switch = FlexpipeSwitch(numSlices = d['numSlices'], depth = d['depth'], width = d['width'], order = d['order'], maxTablesPerSlice = d['maxTablesPerSlice'])
    return switch

def getProgramDdSmall(d):
    from mapper.programs.dd_small import ProgramDdSmall
    program = ProgramDdSmall(numberOfEntriesDict=d['numberOfEntriesDict'])
    return program.program

def getProgramDdMtag(d):
    from mapper.programs.dd_mtag import ProgramDdMtag
    program = ProgramDdMtag(numberOfEntriesDict=d['numberOfEntriesDict'])
    return program.program

def getProgramDdMtagSmall(d):
    from mapper.programs.dd_mtag_small import ProgramDdMtagSmall
    program = ProgramDdMtagSmall(numberOfEntriesDict=d['numberOfEntriesDict'])
    return program.program

def getRealOkayFlexpipeIlpCompiler(d):
    from mapper.src.flexpipe.realOkay_ilp import RealOkayFlexpipeIlpCompiler
    for k in ['timeLimit','treeLimit','emphasis','variableSelect',\
                  'workMem', 'nodeFileInd', 'workDir', 'outputFileName', 'writeLevel','relativeGap', 'epagap', 'solnpoolintensity','populateLimit', 'granMem',\
                  'granLb']:
        if k not in d:
            d[k] = None
            pass
        pass

    if 'greedyVersion' not in d:
        d['greedyVersion'] = ""
        pass
    compiler = RealOkayFlexpipeIlpCompiler(relativeGap=d['relativeGap'],\
                                  epagap = d['epagap'],\
                                       greedyVersion=d['greedyVersion'],\
                                       timeLimit=d['timeLimit'],\
                                       treeLimit=d['treeLimit'],\
                                       emphasis=d['emphasis'],\
                                       populateLimit = d['populateLimit'],\
                                  solnpoolintensity = d['solnpoolintensity'],\
                                       variableSelect=d['variableSelect'],\
                                       workMem=d['workMem'],\
                                       nodeFileInd=d['nodeFileInd'],\
                                       workDir=d['workDir'],\
                                       outputFileName=d['outputFileName'],\
                                       writeLevel=d['writeLevel'],\
                                       granMem=d['granMem'],\
                                               granLb=d['granLb'])
    return compiler

def getFlexpipeIlpCompiler(d):
    from mapper.src.flexpipe.orig_flexpipe_compiler import FlexpipeIlpCompiler
    for k in ['timeLimit','treeLimit','emphasis','variableSelect',\
                  'workMem', 'nodeFileInd', 'workDir', 'outputFileName', 'writeLevel','relativeGap', 'epagap', 'solnpoolintensity','populateLimit', 'granMem']:
        if k not in d:
            d[k] = None
            pass
        pass

    if 'greedyVersion' not in d:
        d['greedyVersion'] = ""
        pass
    compiler = FlexpipeIlpCompiler(relativeGap=d['relativeGap'],\
                                  epagap = d['epagap'],\
                                       greedyVersion=d['greedyVersion'],\
                                       timeLimit=d['timeLimit'],\
                                       treeLimit=d['treeLimit'],\
                                       emphasis=d['emphasis'],\
                                       populateLimit = d['populateLimit'],\
                                  solnpoolintensity = d['solnpoolintensity'],\
                                       variableSelect=d['variableSelect'],\
                                       workMem=d['workMem'],\
                                       nodeFileInd=d['nodeFileInd'],\
                                       workDir=d['workDir'],\
                                       outputFileName=d['outputFileName'],\
                                       writeLevel=d['writeLevel'],\
                                       granMem=d['granMem'])
    return compiler

def getFlexpipeLptCompiler(d):
    from mapper.src.flexpipe.flexpipe_lpt_compiler import FlexpipeLptCompiler
    compiler = FlexpipeLptCompiler()
    return compiler

def getFlexpipePreprocess(d):
    from mapper.src.flexpipe.flexpipe_preprocess import FlexpipePreprocess
    preprocess = FlexpipePreprocess()
    return preprocess

def parseSilently(line):
    line.rstrip("\n")
    keyValuePairs = [[k.lstrip().rstrip().replace(';',',') for k in pair.split("=")] for pair in line.split(",")]
    stringDict = {}
    for (k,v) in keyValuePairs:
        stringDict[k] = v
        pass
    return stringDict

def parse(line):
    line.rstrip("\n")
    keyValuePairs = [[k.lstrip().rstrip().replace(';',',') for k in pair.split("=")] for pair in line.split(",")]
    stringDict = {}
    logging.debug(keyValuePairs)
    for (k,v) in keyValuePairs:
        stringDict[k] = v
        pass
    return stringDict

def getModuleFromStringDict(sd):
    string_list = []
    for key in sd.keys():
        if not sd[key]:
            string_list.append("'%s':''" % key)
        else:
            string_list.append("'%s':%s" % (key,sd[key]))
    s = '{%s}' % ",".join(string_list)
    # s= '{'+ ",".join("'%s' : %s" % (key, sd[key]) for key in sd.keys())+'}'
    # try catch not python

    try:
        d = eval(s)
    except:
        logging.warn("Couldn't eval %s to valid python expression" % s)
        raise

    getModule = {'RmtSwitch':getRmtSwitch,\
                    'ProgramL2L3Simple':getProgramL2L3Simple,\
                    'ProgramL2L3SimpleMtag':getProgramL2L3SimpleMtag,\
                    'ProgramL2L3Complex':getProgramL2L3Complex,\
                     'ProgramL3Dc':getProgramL3Dc,\
                     'ProgramDcUnify':getProgramDcUnify,\
                    'RmtFflCompiler':getRmtFflCompiler,\
                     'RmtFflsCompiler':getRmtFflsCompiler,\
                    'RmtFfdCompiler':getRmtFfdCompiler,\
                    'RmtIlpCompiler':getRmtIlpCompiler,\
                    'RmtLpCompiler':getRmtLpCompiler,\
                    'RmtLpOnlyCompiler':getRmtLpOnlyCompiler,\
                    'RmtPreprocess':getRmtPreprocess,\
                    'FlexpipeLptCompiler':getFlexpipeLptCompiler,\
                    'FlexpipeIlpCompiler':getFlexpipeIlpCompiler,\
                    'RealOkayFlexpipeIlpCompiler':getRealOkayFlexpipeIlpCompiler,\
                    'FlexpipePreprocess':getFlexpipePreprocess,
                    'FlexpipeSwitch':getFlexpipeSwitch,\
                    'ProgramDdSmall':getProgramDdSmall,\
                    'ProgramDdMtag':getProgramDdMtag,\
                    'ProgramDdMtagSmall':getProgramDdMtagSmall\
                }
    if 'type' not in d:
        logging.warn('No type given in config')
        pass
    else:
        if d['type'] not in getModule:
            logging.warn('No function to parse type %s' % d['type'])
            pass
        else:
            module = getModule[d['type']](d)
            return module
            pass
        pass
    
    pass
        
def getKeysInConfigFile(qConfigFile):
    names = []
    f = open(qConfigFile, "r")
    for line in f.xreadlines():
        sd = parseSilently(line)
        unquoteSdKey = sd['key'].lstrip('\'').rstrip('\'')
        names.append(unquoteSdKey)
        pass
    return names

def getModules(query):
    for q in query.keys():
        qKey = query[q]['key']
        qConfigFile = query[q]['configFile']
    
        f = open(qConfigFile, "r")
        found = False
        for line in f.xreadlines():
            sd = parse(line)
            unquoteSdKey = sd['key'].lstrip('\'').rstrip('\'')
            if (unquoteSdKey == qKey):
                found = True
                break
            pass

        if found:
            query[q]['module'] = getModuleFromStringDict(sd)
            pass
        else:
            logging.warn("not found %s with key %s" % (q, qKey))
            logging.warn(" in file %s " % qConfigFile)
            pass
        
        if found and query[q]['module'] is not None:
            logging.info("got %s: %s " % (q, sd['type']))
            pass
        else:
            logging.warn("query[%s][module] is None " % q)
            pass
        f.close()
        pass

    logging.info(query)
    return query

def makeQuery(compKey, switchKey, prepKey, progKey=None):
    query = {'compiler': {'key':'001', 'configFile':'mapper/config/comp00.txt', 'module':None},\
                  'switch': {'key':'001', 'configFile':'mapper/config/switch00.txt', 'module':None},\
                  'preprocess': {'key':'001', 'configFile':'mapper/config/prep00.txt', 'module': None},\
                 'program': {'key':'001', 'configFile':'mapper/config/prog00.txt', 'module': None}}


    query['compiler']['key'] = compKey
    query['switch']['key'] = switchKey
    query['preprocess']['key'] = prepKey
    query['program']['key'] = progKey
    return query
