# --- data_paths.py ---
# --- Author: C. Feltman ---
# DESCRIPTION: Place to store the pathing information of the project

# --- bookkeeping ---
# !/usr/bin/env python
__author__ = "Connor Feltman"
__date__ = "2022-08-22"
__version__ = "1.0.0"
# -------------------

# --- imports ---
from glob import glob

class DataPaths:

    # --- --- --- --- --- --- ---
    # --- USER SPECIFIC DATA ---
    # --- --- --- --- --- --- ---
    user = 'cfelt'
    PATH_TO_DATA_FOLDER = r'C:\Data\\'
    HOMEDRIVE = 'C:'
    HOMEPATH = 'C:\\'

    # --- --- --- --- --- ---
    # --- TRICE II PATHS ---
    # --- --- --- --- --- ---
    TRICE_data_folder = fr'{PATH_TO_DATA_FOLDER}TRICEII\\'

