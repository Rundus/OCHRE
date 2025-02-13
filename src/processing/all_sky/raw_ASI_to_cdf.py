# --- AllSkyTrajecMovie.py ---
# --- Author: C. Feltman ---
# DESCRIPTION: Loads in the AllSky data, uses the calibration file to determine position
# finally loads in traj data to determine rocket trajectory

# --- bookkeeping ---
# !/usr/bin/env python
__author__ = "Connor Feltman"
__date__ = "2022-08-22"
__version__ = "1.0.0"

import numpy as np

from src.my_imports import *
start_time = time.time()
# --- --- --- --- ---

# --- --- --- ---
# --- TOGGLES ---
# --- --- --- ---

# Just print the names of files
justPrintSiteNames = False

# --- Select the Site ---
# 0 -> longyearbyen
# 1 -> nyAlesund
# 2 -> skibotn
wSite = 1

# --- Select the Wavelength ---
# 0 -> 5570
# 1 -> 6300
wWaveLength = 1


# --- output ---
outputData = True

# --- --- --- ---
# --- IMPORTS ---
# --- --- --- ---
import spaceToolsLib as stl
from src.mission_attributes import TRICEII
from src.data_paths import DataPaths
from toggles import AllSky
from scipy.io import readsav
import matplotlib.pyplot as plt
import math

def raw_ASI_to_cdf(wSite, wWaveLength, justPrintSiteNames):

    # --- load data ---

    all_sky_folder_path = f'{DataPaths.TRICE_data_folder}\\{AllSky.inputPath_modifier_AllSky}'
    site_paths = glob(f'{all_sky_folder_path}\\{AllSky.wLengths[wWaveLength]}\\*')
    site_names = [path.replace(f'{all_sky_folder_path}\\{AllSky.wLengths[wWaveLength]}\\','') for path in site_paths]

    if justPrintSiteNames:
        for i, file in enumerate(site_names):
            print('[{:.0f}] {:80s}'.format(i, site_names[i]))
        return

    #############################
    # --- get the input files ---
    #############################

    path_to_data = all_sky_folder_path+ f'\\{AllSky.wLengths[wWaveLength]}\\{site_names[wSite]}\\'

    # --- get cal files and convert to python---
    cal_file = readsav(glob(path_to_data+'*.dat*')[0])

    # --- get All Sky photos ---
    photo_files = glob(path_to_data+'*.png')

    ############################################
    # --- COLLECT IMAGE FILES AND TIMESTAMPS ---
    ############################################

    # get the image time series and the data itself into single variables
    Epoch_allSky = []
    image_data = []
    stl.prgMsg('Collecting Image Data')

    site_modifier = ['','nya6_','']

    for imageStr in photo_files:

        # get the timestamp
        strTimeStamp = imageStr.replace(path_to_data,'').replace(site_modifier[wSite],'').replace(f'_{AllSky.wLengths[wWaveLength]}_cal.png','')
        year = int(strTimeStamp[0:4])
        month = int(strTimeStamp[4:6])
        day = int(strTimeStamp[6:8])
        hour = int(strTimeStamp[9:11])
        minute = int(strTimeStamp[11:13])
        second = int(strTimeStamp[13:15])
        dtTimeStamp = dt.datetime(year, month, day, hour, minute, second)
        Epoch_allSky.append(dtTimeStamp)

        # get the grayscale data
        image_data.append(plt.imread(imageStr))

    stl.Done(start_time)

    ###################################
    # --- prepare data for plotting ---
    ###################################
    lats = np.array(deepcopy(cal_file['glats']))
    longs = np.array(deepcopy(cal_file['glons']))
    elevs = np.array(deepcopy(cal_file['elevs']))

    # --- correct the calibration data ---
    for j in range(len(lats)):  # array rows
        for k in range(len(lats[j])):  # row values
            if math.isnan(lats[j][k]) or math.isnan(longs[j][k]) or elevs[j][k] <= 20 or math.isnan(elevs[j][k]):
                lats[j][k] = 70
                longs[j][k] = 20
                for a in range(len(image_data)):  # correct this j,k point in all auroral images
                    image_data[a][j][k] = np.nan

    stl.prgMsg('Collecting and processing/cleaning Image data')

    # -- collect and process all aurora image data ---
    # remove nan values from data and replace with garbage AND convert all Images into Rayleighs
    # description: the image data is a 16-bit counts value normalized by 65535.

    # If site is Skibotn:
    # Invert this and use the calibration factor of 1 R/count given in the cal file

    # if site is Ny Alesund, use the provided calibration equations
    # FOR 6300A: NyA4[kR] = 0.5 + NyA4[cnts]*0.19E-3
    # FOR 5577A: NyA4[kR] = 0.43 + NyA4[cnts]*0.25E-3

    # convert data to KRayleighs
    if wSite == 1:

        if AllSky.wLengths[wWaveLength] == '6300':
            image_data = [0.5*image*AllSky.architecture*0.19E-3 for image in image_data ]

        elif AllSky.wLengths[wWaveLength] == '5570':
            image_data = [0.43 * image*AllSky.architecture* 0.25E-3 for image in image_data]

    stl.Done(start_time)


    ################
    # --- OUTPUT ---
    ################

    if outputData:

        data_dict_output = {
            'Epoch' :[np.array(Epoch_allSky),{}],
            'Elev' : [np.array(elevs),{}],
            'lats' : [np.array(lats),{}],
            'longs': [np.array(longs), {}],
            'image_data': [np.array(image_data), {'DEPEND_0':'Epoch','var_type':'data','UNITS':'kR'}]
        }

        output_path = path_to_data+f'TRICEII_all_sky_{AllSky.wLengths[wWaveLength]}_{site_names[wSite]}.cdf'
        stl.outputCDFdata(data_dict=data_dict_output,
                          outputPath=output_path)


# --- --- --- ---
# --- EXECUTE ---
# --- --- --- ---
raw_ASI_to_cdf(wSite, wWaveLength,justPrintSiteNames)
