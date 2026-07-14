# --- plotting_ACE_satellite_IMF.py ---
# Description: Read in the ACE satellite .txt file and
# get it's contents of IMF data. Plot it
import matplotlib.pyplot as plt

input_file_path = 'C:\Data\TRICEII\ACE_satellite\ACE_MAG16_2018-342_V3-3.txt'
preabmle_length =  23
import io
import datetime as dt

import spaceToolsLib as stl
stl.setupPYCDF()
from spacepy import pycdf


# --- PLOT PARAMS ---
label_fontsize = 20
title_fontsize = 25
legend_fontsize = 25
tick_fontsize = 20
tick_width  = 2
tick_length = 3


def plotting_ACE_satellite_IMF():

    IMF_data = []

    with io.open(input_file_path, mode='r') as f:

        for i in range(preabmle_length): # ignore all the preamble in the file
            next(f)

        for line in f:
            IMF_data.append(line.split())

    T0 = dt.datetime(1996,1,1)
    Epoch = [T0 + dt.timedelta(seconds=int(float(IMF_data[idx][1]))) for idx in range(len(IMF_data))]
    Bx = [float(IMF_data[idx][6]) for idx in range(len(IMF_data))]
    By = [float(IMF_data[idx][7]) for idx in range(len(IMF_data))]
    Bz = [float(IMF_data[idx][8]) for idx in range(len(IMF_data))]


    fig, ax = plt.subplots(2, sharex=True)
    fig.suptitle('Advanced Composition Explorer (ACE) at L1 Point', fontsize=title_fontsize)
    fig.set_size_inches(15,10)

    for i in range(2):
        ax[i].set_ylim(-10, 10)
        if i == 0:
            ax[i].plot(Epoch, Bx, label='Bx',color='tab:red')
            ax[i].plot(Epoch, By, label='By', color='tab:green')
        elif i ==1:
            ax[i].plot(Epoch, Bz, label='Bz', color='tab:blue')
            ax[i].set_xlabel('Dec 8$^{th}$, 2018 [UTC]', fontsize=label_fontsize)
            ax[i].axvspan(dt.datetime(2018,12,8,7,12),dt.datetime(2018,12,8,8,27), color='black',alpha=0.25)

        ax[i].set_ylabel('Magnetic Field [nT]', fontsize=label_fontsize)
        ax[i].axhline(y=0,linestyle='--',color='gray')
        ax[i].axvline(x=dt.datetime(2018,12,8,8,28), label='TRICE-II Launch', color='black')
        ax[i].axvspan(dt.datetime(2018,12,8,8,28),dt.datetime(2018,12,8,8,44), color='red',alpha=0.4)
        ax[i].set_xlim(dt.datetime(2018,12,8,5),dt.datetime(2018,12,8,11))
        ax[i].legend(loc='upper right', fontsize=legend_fontsize)
        import matplotlib.dates as mdates
        myFmt = mdates.DateFormatter('%H:%M')
        ax[i].xaxis.set_major_formatter(myFmt)

        ax[i].tick_params(axis='y', which='major', colors='black', labelsize=tick_fontsize - 3, length=tick_length, width=tick_width)
        ax[i].tick_params(axis='y', which='minor', colors='black', labelsize=tick_fontsize - 6, length=tick_length - 2, width=tick_width)
        ax[i].tick_params(axis='x', which='major', colors='black', labelsize=tick_fontsize, length=tick_length + 4, width=tick_width)
        ax[i].tick_params(axis='x', which='minor', colors='black', labelsize=tick_fontsize, length=tick_length,width=tick_width)

    plt.tight_layout()
    plt.savefig(r'C:\Users\cfelt\Desktop\Research\OCHRE\plots\ACE_satellite_TRICEII.png')


plotting_ACE_satellite_IMF()