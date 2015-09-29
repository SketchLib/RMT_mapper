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



import logging
import numpy as np

"""
Intel FlexPipe switch.
"""

numBlocks = {'mapper':[2,0,0,0],'ffu':[0,12,12,0], 'bst':[0,0,4,0],'hashtable':[0,0,0,4]}
order = [0,1,2,3]
maxTablesPerBlock = 4
depth = {'mapper':64, 'ffu':1000,'bst':16000, 'hashtable':16000}
width = {'mapper':48, 'ffu':36,'bst':36, 'hashtable':72}
class FlexpipeSwitch:
    def __init__(self, numBlocks=numBlocks,\
                     depth=depth,\
                     width=width,\
                     order=order,\
                     maxTablesPerBlock=maxTablesPerBlock):
        """ initialize with resources available in each stage
        The number of stages is implicit in the length of
         the numBlocks[mem] and order lists. 
         The FlexPipe chip as described here has 4 stages.
         Note we could also have represented it as having
          5 stages with the third and fourth stage
          executing simultaneously, see note below.

        Stages in FlexPipe are not uniform- different stages
        have different memory types, so for each memory
        type we specify the number of blocks available in
        each stage in @numBlocks.

        @depth and @width are mappings from memory types to the
        depth and width of inidividual blocks where-
         depth is the number of match entries the block can store
         width is the max. width of a match entry that can fit        

         @order is a list indexed by stage number where @order[i]
         is the topological order of stage i in the
         execution graph (where nodes correspond to stages
         and there is an edge from stage x to y if y executes
         after x). E.g., in a pipeline where stage 3 and 4 execute simultaneously
         order[3] = order[4] etc. 

         @maxTablesPerBlock is the maximum number of logical tables
         that can share a memory block
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("FLEXPIPE SWITCH")

        memoryTypes = numBlocks.keys()
        self.memoryTypes = memoryTypes
        self.logger.info("Memory types: %s" % self.memoryTypes)

        self.numBlocks = numBlocks
        self.logger.info("Number of blocks (per-stage): %s" %\
                             str([(mem, self.numBlocks[mem]) for mem in\
                                      self.memoryTypes]))

        # Order of execution of stages. Note that here we chose to
        #  represent the pipeline as 4 stages in sequence where
        #  the third stage has both FFU and BST memory types
        # (see numBlocks). Hence the order is [0, 1, 2, 3]
        # We could also have equivalently represented the pipeline
        #  as described in the paper- 5 stages where the second and
        #  third stages have FFU only, the fourth stage has BST only
        #  and the third and fourth stage execute
        #  simultaneously so that order = [0, 1, 2, 2, 3]. 
        self.order = order

        self.numStages = max([len(numBlocks[mem]) for mem in memoryTypes])
        self.logger.info("Number of stages: %s " % self.numStages)

        self.depth = depth
        self.width = width
        self.logger.info("Depth and width of memory: %s "\
                         % ["%dx%db %s" % (depth[mem], width[mem], mem)\
                                for mem in self.memoryTypes])

        self.maxTablesPerBlock = maxTablesPerBlock
        self.logger.info("Maximum number of tables that"\
                             + " can share a memory block: %d" %\
                             maxTablesPerBlock)

        if len(order)==0:
            self.order = range(self.numStages)
            pass

        # @matchType is a mapping from memory types to the match types
        # (exact, lpm etc.) that can be supported. E.g., hashtable
        # supports "exact" match type but not "lpm" (longest prefix
        # match).
        # Note that in FlexPipe, the first stage is less re-configurable
        #  than others and can match on a specific set of fields like
        #  VLAN, IP, MAC, Ethertype etc. For this behavior,
        #  we represent the first stage as having a "mapper"
        #  memory type and we expect the program/ preprocesser to
        #  specify a table's match type as "mapper" when it's clear
        #  that the table can be supported in the first stage of
        #  FlexPipe. E.g., a Routable table that matches on
        #  VLAN, port number, destination MAC and Ethertype
        #  can be (and typically is) in this stage.
        self.matchType = {}
        self.matchType['ffu'] = ['ternary','exact','lpm']
        self.matchType['hashtable'] = ['exact']
        self.matchType['bst'] = ['lpm','exact']
        self.matchType['mapper'] = ['mapper']
        self.logger.info("Match type: %s" % self.matchType)

        pass
