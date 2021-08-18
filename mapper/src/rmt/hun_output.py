def printFormat1D(self, f, obj, title, func, maxStage):
#         import sys
    print(" ")
    
    f.write("%45s" % title)
#         f.write("%12s" % "# of stages")
    for i in range(maxStage):
        if func == 'int':
            f.write("%3d" % (i+1))
        if func == 'real':
            f.write("%4d" % (i+1))
    f.write("\n")
    for i in range(45+maxStage*3):
        f.write("-")
    f.write("\n")
    f.write("%45s" % "total")
    for st in range(maxStage):
        if func == 'int':
            f.write("%3d" % int(round(obj[st])))
        if func == 'real':
            f.write(" %0.1f" % obj[st])
    f.write("\n")
    f.write("\n")

def printFormat1D_large(self, f, obj, title, func, maxStage):
#         import sys
    print(" ")
    
    f.write("%45s" % title)
#         f.write("%12s" % "# of stages")
    for i in range(maxStage):
        if func == 'int':
            f.write("%8d" % (i+1))
        if func == 'real':
            f.write("%8d" % (i+1))
    f.write("\n")
    for i in range(45+maxStage*8):
        f.write("-")
    f.write("\n")
    f.write("%45s" % "total")
    for st in range(maxStage):
        if func == 'int':
            f.write("%8d" % int(round(obj[st])))
        if func == 'real':
            f.write(" %0.1f" % obj[st])
    f.write("\n")
    f.write("\n")

def printFormat2D(self, f, obj, title, func, maxStage):
#         import sys
    print(" ")
    
    f.write("%45s" % title)
#         f.write("%12s" % "# of stages")
    for i in range(maxStage):
        if func == 'int':
            f.write("%3d" % (i+1))
        if func == 'real':
            f.write("%4d" % (i+1))
            
    f.write("\n")
    for i in range(45+maxStage*3):
        f.write("-")
    f.write("\n")
    
    name_list = []
    for log in range(self.logMax):
        name = self.program.names[log]
        name_list.append(name)
        
    index = [i for i in range(self.logMax)]

    for log in index:
        name = self.program.names[log]
        f.write("%45s" % name)
        for st in range(maxStage):
            if func == 'int':
                f.write("%3d" % int(round(obj[log, st])))
            if func == 'real':
                f.write(" %0.1f" % obj[log, st])
        f.write("\n")
    for i in range(45+maxStage*3):
        f.write("-")
    f.write("\n")
    f.write("%45s" % (title+" TOTAL SUM"))

    for st in range(maxStage):
        if func == 'int':
            total = 0
            for log in range(self.logMax):
                total += obj[log, st]
            f.write("%3d" % int(round(total)))
    
    f.write("\n")
    for i in range(45+maxStage*3):
        f.write("-")
    f.write("\n")
    f.write("\n")

def printFormat2D_large(self, f, obj, title, func, maxStage):
#         import sys
    print(" ")
    
    f.write("%45s" % title)
#         f.write("%12s" % "# of stages")
    for i in range(maxStage):
        if func == 'int':
            f.write("%8d" % (i+1))
        if func == 'real':
            f.write("%8d" % (i+1))
            
    f.write("\n")
    for i in range(45+maxStage*8):
        f.write("-")
    f.write("\n")
    
    name_list = []
    for log in range(self.logMax):
        name = self.program.names[log]
        name_list.append(name)
        
    index = [i for i in range(self.logMax)]

    for log in index:
        name = self.program.names[log]
        f.write("%45s" % name)
        for st in range(maxStage):
            if func == 'int':
                f.write("%8d" % int(round(obj[log, st])))
            if func == 'real':
                f.write(" %0.1f" % obj[log, st])
        f.write("\n")
    for i in range(45+maxStage*8):
        f.write("-")
    f.write("\n")
    f.write("%45s" % (title+" TOTAL SUM"))

    for st in range(maxStage):
        if func == 'int':
            total = 0
            for log in range(self.logMax):
                total += obj[log, st]
            f.write("%8d" % int(round(total)))
    
    f.write("\n")
    for i in range(45+maxStage*8):
        f.write("-")
    f.write("\n")
    f.write("\n")


def printFormat3D(self, f, obj, title, func, thing, maxStage):
    print(" ")
    print("pf max : ", self.pfMax[thing])
    f.write("%45s" % title)
#         sys.stdout.write("%12s" % "# of stages")
    for i in range(maxStage):
        for pf in range(self.pfMax[thing]):
            f.write("%3d" % (i+1))
            
    f.write("\n")
    for i in range(45+maxStage*3):
        f.write("-")
    f.write("\n")
    for log in range(self.logMax):
        # print()
        for pf in range(self.pfMax[thing]):
            # print(pf)
            name = self.program.names[log]
            f.write("%45s" % name)
            for st in range(maxStage):
                f.write("%3d" % int(round(obj[log*self.stMax+st, pf])))
            f.write("\n")

    for i in range(45+maxStage*3):
        f.write("-")
    f.write("\n")
    f.write("%45s" % (title+" TOTAL SUM"))

    for st in range(maxStage):
        for pf in range(self.pfMax[thing]):
            total = 0
            for log in range(self.logMax):
                total += obj[log*self.stMax+st, pf]
            f.write("%3d" % int(round(total)))

    f.write("\n")
    for i in range(45+maxStage*3):
        f.write("-")
    f.write("\n")
    f.write("\n")

#                 break
#             sys.stdout.write("\n")


# def printOutConstraints(self, output_path):
#     import os
#     dir = os.path.dirname(output_path)
#     if not os.path.isdir(dir):
#         os.makedirs(dir)
#     f = open(output_path, 'w+')

# #         f.write("print out consts!\n")
#     print("print out consts!")

def printOutConstraints(self, output_path):
    import sys

    print("print out consts!")
    print(output_path)

    import os
    dir = os.path.dirname(output_path)
    if not os.path.isdir(dir):
        os.makedirs(dir)
    f = open(output_path, 'w+')


    maxStage = 0
    # maxStage = 12
    obj=self.m[self.isMaximumStage] # this is wrong way to get maximum stage, pipeline stage do not allocate this
    for st in range(self.stMax):
        # print(int(obj[st]))
        # f.write("%d\n" % int(obj[st]))
        if round(obj[st]) == 1:
            maxStage = st+1

    # obj=self.m[self.endAllMem]
    # for log in range(self.logMax):
    #     for st in range(self.stMax):
    #         if int(obj[log, st]) == 1:
    #             if maxStage < st+1:
    #                 maxStage = st+1

    # maxStage = 12
    f.write("maximum_stage ")
    f.write(str(maxStage))
    f.write("\n")
    print("maximum_stage", maxStage)

    hash_dist_unit = 0
    obj=self.m[self.hashDistUnitVar]
    for log in range(self.logMax):
        for st in range(maxStage):
            hash_dist_unit += int(round(obj[log, st]))
    f.write("hash_dist_unit ")
    f.write(str(hash_dist_unit))
    f.write("\n")
    print("hash_dist_unit", hash_dist_unit)

    salu = 0
    obj=self.m[self.saluVar]
    for log in range(self.logMax):
        for st in range(maxStage):
            salu += int(round(obj[log, st]))
    f.write("salu ")
    f.write(str(salu))
    f.write("\n")
    print("salu", salu)

    map_ram = 0
    obj=self.m[self.saluVar]
    for log in range(self.logMax):
        for st in range(maxStage):
            register_bit_size = self.program.registerBitSizeList[log]
            size = 0
            if register_bit_size % (4096*32) == 0:
                size = int(register_bit_size / (4096*32)) + 1
            else:
                size = int(register_bit_size / (4096*32)) + 2
            map_ram += int(round(obj[log, st]) * size)
    f.write("map_ram ")
    f.write(str(map_ram))
    f.write("\n")
    print("map_ram", map_ram)

    sram = 0
    obj=self.m[self.block['sram']]
    for log in range(self.logMax):
        for st in range(maxStage):
            sram += int(round(obj[log, st]))
    f.write("sram ")
    f.write(str(sram))
    f.write("\n")
    print("sram", sram)

    tcam = 0
    obj=self.m[self.block['tcam']]
    for log in range(self.logMax):
        for st in range(maxStage):
            tcam += int(round(obj[log, st]))
    f.write("tcam ")
    f.write(str(tcam))
    f.write("\n")
    print("tcam", tcam)

    # return

    obj=self.m[self.hashDistUnitVar]
    printFormat2D(self, f, obj, "[hashDistUnitVar]", "int", maxStage)
    printFormat2D(self, sys.stdout, obj, "[hashDistUnitVar]", "int", maxStage)

    obj=self.m[self.saluVar]
    printFormat2D(self, f, obj, "[saluVar]", "int", maxStage)
    printFormat2D(self, sys.stdout, obj, "[saluVar]", "int", maxStage)

    for thing in self.switch.allTypes:
        # if thing == 'action':
        #     continue
        # if thing == 'tcam':
        #     continue
        print("\n\n****************************** [thing = %s] ******************************\n\n" % thing)

        obj=self.m[self.word[thing]]
        printFormat2D_large(self, f, obj, "[word [%s]]" % thing, "int", maxStage)
        printFormat2D_large(self, sys.stdout, obj, "[word [%s]]" % thing, "int", maxStage)

        obj=self.m[self.block[thing]]
        printFormat2D(self, f, obj, "[block [%s]]" % thing, "int", maxStage)
        printFormat2D(self, sys.stdout, obj, "[block [%s]]" % thing, "int", maxStage)

        obj=self.m[self.blockBin[thing]]
        printFormat2D(self, f, obj, "[blockBin [%s]]" % thing, "int", maxStage)
        printFormat2D(self, sys.stdout, obj, "[blockBin [%s]]" % thing, "int", maxStage)

        obj=self.m[self.layout[thing]]
        printFormat3D(self, f, obj, "[layout [%s]]" % thing, "int", thing, maxStage)
        printFormat3D(self, sys.stdout, obj, "[layout [%s]]" % thing, "int", thing, maxStage)

        obj=self.m[self.layoutBin[thing]]
        printFormat3D(self, f, obj, "[layoutBin [%s]]" % thing, "int", thing, maxStage)
        printFormat3D(self, sys.stdout, obj, "[layoutBin [%s]]" % thing, "int", thing, maxStage)

    obj=self.m[self.startAllMem]
    printFormat2D(self, f, obj, "[startAllMem]", "int", maxStage)
    printFormat2D(self, sys.stdout, obj, "[startAllMem]", "int", maxStage)

    obj=self.m[self.endAllMem]
    printFormat2D(self, f, obj, "[endAllMem]", "int", maxStage)
    printFormat2D(self, sys.stdout, obj, "[endAllMem]", "int", maxStage)

    obj=self.m[self.blockAllMemBin]
    printFormat2D(self, f, obj, "[blockAllMemBin]", "int", maxStage)
    printFormat2D(self, sys.stdout, obj, "[blockAllMemBin]", "int", maxStage)

    obj=self.m[self.startAllMemTimesBlockAllMemBin]
    printFormat2D(self, f, obj, "[startAllMemTimesBlockAllMemBin]", "int", maxStage)
    printFormat2D(self, sys.stdout, obj, "[startAllMemTimesBlockAllMemBin]", "int", maxStage)

    obj=self.m[self.endAllMemTimesBlockAllMemBin]
    printFormat2D(self, f, obj, "[endAllMemTimesBlockAllMemBin]", "int", maxStage)
    printFormat2D(self, sys.stdout, obj, "[endAllMemTimesBlockAllMemBin]", "int", maxStage)

    obj=self.m[self.totalBlocksForStBin]
    printFormat1D(self, f, obj, "[totalBlocksForStBin]", "int", maxStage)
    printFormat1D(self, sys.stdout, obj, "[totalBlocksForStBin]", "int", maxStage)

    obj=self.m[self.isMaximumStageTimesTotalBlocksForStBin]
    printFormat1D(self, f, obj, "[isMaximumStageTimesTotalBlocksForStBin]", "int", maxStage)
    printFormat1D(self, sys.stdout, obj, "[isMaximumStageTimesTotalBlocksForStBin]", "int", maxStage)

    obj=self.m[self.isMaximumStage]
    printFormat1D(self, f, obj, "[isMaximumStage]", "int", maxStage)
    printFormat1D(self, sys.stdout, obj, "[isMaximumStage]", "int", maxStage)

    obj=self.m[self.startTimeOfStage]
    printFormat1D_large(self, f, obj, "[startTimeOfStage]", "int", maxStage)
    printFormat1D_large(self, sys.stdout, obj, "[startTimeOfStage]", "int", maxStage)

    obj=self.m[self.startAllMemTimesStartTimeOfStage]
    printFormat2D_large(self, f, obj, "[startAllMemTimesStartTimeOfStage]", "int", maxStage)
    printFormat2D_large(self, sys.stdout, obj, "[startAllMemTimesStartTimeOfStage]", "int", maxStage)

    obj=self.m[self.endAllMemTimesStartTimeOfStage]
    printFormat2D_large(self, f, obj, "[endAllMemTimesStartTimeOfStage]", "int", maxStage)
    printFormat2D_large(self, sys.stdout, obj, "[endAllMemTimesStartTimeOfStage]", "int", maxStage)

    obj=self.m[self.logicalTableIDs]
    printFormat2D(self, f, obj, "[logicalTableIDs]", "int", maxStage)
    printFormat2D(self, sys.stdout, obj, "[logicalTableIDs]", "int", maxStage)
