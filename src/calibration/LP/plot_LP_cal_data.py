# --- plot_LP_cal_data.py ---
# Description: script to plot the calibration data of the OCHRE Langmuir Probe

# Imports
from glob import glob
import matplotlib.pyplot as plt
import pandas as pd

# toggles
wFile =0
wKey = 1



def plot_LP_cal_data():

    # Load the data file
    file_path = glob('/home/connor/Data/OCHRE/calibration/LangmuirProbe/*.csv*')[0]

    # load the data
    df = pd.read_csv(file_path, on_bad_lines='skip')
    keys = df.keys()

    # plot everything
    fig, ax = plt.subplots(len(keys))
    for idx in range(len(keys)):
        ax[idx].plot(df[keys[0]],df[keys[idx]],label=f'{keys[idx]}')
        ax[idx].legend()
    plt.show()


# --- EXECUTE ---
plot_LP_cal_data()