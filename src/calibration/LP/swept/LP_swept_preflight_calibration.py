# --- LP_swept_preflight_calibration.py ---
# --- Author: C. Feltman ---
# DESCRIPTION: Get the LP swept file and use it to create a calibration function


######################
# --- DATA TOGGLES ---
######################
just_print_file_names_bool = False
rocket_str = 'low'
wInstr = 'EEPAA'
dict_file_path ={ # FORMAT: Data Name: [Str modifier to ACESII Data Folder Path, Which Datafile Indices in directory [[High flyer], [Low flyer]]]
    f'{wInstr}':['L2', [[0],[0]]],
    'Lshell':['coordinates',[[0],[0]]]
}
outputData = True


#################
# --- IMPORTS ---
#################
import pandas as pd
import matplotlib.pyplot as plt


def LP_swept_preflight_calibration():

    #######################
    # --- LOAD THE DATA ---
    #######################
    file_path = '/home/connor/Data/ROCKETS/OCHRE/calibration/LangmuirProbe/swept/UIOWA_OCHRE_testing_4_23_26_resistance5Meg.csv'
    df = pd.read_csv(file_path)

    time = df['Relative (uS)']
    Vstep = df['LP_OCHRE_v_step']
    fig, ax = plt.subplots()
    ax.scatter(time,Vstep)
    plt.show()




#################
# --- EXECUTE ---
#################
LP_swept_preflight_calibration()
