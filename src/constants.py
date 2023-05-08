import os 

# Temporary hack until we have a setup.py file
SRC_PATH = os.path.dirname(os.path.realpath(__file__))
ROOT_PATH = os.path.abspath(os.path.join(SRC_PATH, "../"))
ABI_PATH = os.path.join(SRC_PATH, "abi/")
CONFIG_PATH = os.path.join(ROOT_PATH, "config/")
