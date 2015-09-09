import os
from os import sys, path
import subprocess
import argparse
import logging
import math
import os
import time
import traceback

# Import modules as if from the mapper directory
sys.path.append( path.dirname( path.dirname( path.abspath(__file__) ) ) )

# pipeline compile options
INGRESS_ONLY = 0
EGRESS_ONLY = 1
INGRESS_AND_EGRESS = 2

# default configuration file locations
mapper_dir = ".."
default_compiler_file = '%s/config/comp00.txt' % mapper_dir
default_program_file = '%s/config/prog00.txt' % mapper_dir
default_switch_file = '%s/config/switch00.txt' % mapper_dir
default_preprocessor_file = '%s/config/prep00.txt' % mapper_dir
