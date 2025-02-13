# --- Plot1_AllSky.py ---
# --- Author: C. Feltman ---
# DESCRIPTION: All Sky Imager data plot



# --- bookkeeping ---
# !/usr/bin/env python
__author__ = "Connor Feltman"
__date__ = "2022-08-22"
__version__ = "1.0.0"

import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
from src.my_imports import *
start_time = time.time()
# --- --- --- --- ---

# --- --- --- ---
# --- IMPORTS ---
# --- --- --- ---
import spaceToolsLib as stl
import matplotlib.gridspec as gridspec

# --- --- --- ---
# --- TOGGLES ---
# --- --- --- ---
timeTargetsUTC = [dt.datetime(2022,11,20,17,23,20,100000),
                      dt.datetime(2022,11,20,17,24,00,100000),
                      dt.datetime(2022,11,20,17,24,40,100000),
                      dt.datetime(2022,11,20,17,25,20,100000),
                      dt.datetime(2022,11,20,17,26,00,100000),
                      dt.datetime(2022,11,20,17,26,40,100000),
                      dt.datetime(2022,11,20,17,27,20,100000)] # find the UTC dates times of the specifically sampled labels

# --------------ALTvsLAT------------------
plot_height = 15
plot_Width = 20
plot_linewidth = 4
scatter_markersize = 800
label_fontsize = 30
label_labelpad = 15
text_size = 55
tick_labelsize = 20
tick_length = 10
tick_width = 3

legend_fontsize = 55
title_fontsize = 20
my_cmap = stl.apl_rainbow_black0_cmap()
my_cmap.set_bad(color=(0,0,0))
my_cmap.set_under('black')
# --------------------------------

# --- --- --- --- --- --- -
# --- LOAD ALL THE DATA ---
# --- --- --- --- --- --- -
stl.prgMsg('Loading Data')

# attitude
data_dict_attitude = stl.loadDictFromFile(glob(f'{DataPaths.TRICE_data_folder}\\attitude\\{TRICEII.fliers[0]}\\*_Attitude_*')[0])


# eepaa data
data_dict_eepaa = stl.loadDictFromFile(glob(f'{DataPaths.TRICE_data_folder}\\L2\\{TRICEII.fliers[0]}\\*_eepaa_cal*')[0])

# ion data
data_dict_ion = stl.loadDictFromFile(glob(f'{DataPaths.TRICE_data_folder}\\L2\\{TRICEII.fliers[0]}\\*_ACI_cal*')[0])
stl.Done(start_time)

# --- --- --- --- --- ---
# --- PROCESS THE DATA ---
# --- --- --- --- --- ---
stl.prgMsg('Proccessing Data')

# average the eepaa data over pitch angle
eepaa_avg = np.average(data_dict_eepaa['Differential_Number_Flux'][0], axis=1)
ion_avg = np.average(data_dict_ion['trice1_hplus_flux'][0][:, 3:15, :], axis=1)




stl.Done(start_time)

############################
# --- --- --- --- --- --- --
# --- START THE PLOTTING ---
# --- --- --- --- --- --- --
############################
stl.prgMsg('Making TRICE-II trajectory projection')

# Figure
fig = plt.figure()
fig.set_figheight(plot_height)
fig.set_figwidth(plot_Width)
gs0 = gridspec.GridSpec(nrows=3, ncols=2, figure=fig, height_ratios=[0.15, 0.15, 0.7], width_ratios=[2/3,1/3])

# --- --- --- --- --
# --- EEPAA DATA ---
# --- --- --- --- --
ax1 = fig.add_subplot(gs0[0,0])

ax1.pcolormesh(data_dict_eepaa['Epoch'][0],
               data_dict_eepaa['Energy'][0],
               eepaa_avg.T,
               cmap=my_cmap,
               vmin=1E3,
               vmax=1E8)

ax1.set_yscale('log')
ax1.set_ylabel('Electron\nEnergy [eV]', fontsize=label_fontsize-5)


# --- --- --- --- --
# --- ACI DATA ---
# --- --- --- --- --
ax2 = fig.add_subplot(gs0[1,0])

ax2.pcolormesh(data_dict_ion['Epoch'][0],
               data_dict_ion['trice1_ion_energy'][0],
               ion_avg.T,
               cmap=my_cmap,
               vmin=1E0,
               vmax=5E4
               )

ax2.set_yscale('log')
ax2.set_ylabel('Ion\n Energy [eV]', fontsize=label_fontsize-5)

# --- --- --- --- --- --- --- -
# --- ALT vs Ephemeris DATA ---
# --- --- --- --- --- --- --- -

ax3 = fig.add_subplot(gs0[2, 0])

ax3.plot(data_dict_attitude['Epoch'][0],
         data_dict_attitude['alt'][0]/stl.m_to_km,
         color='tab:blue',
         linewidth=plot_linewidth)

ax3.set_ylabel('Altitude [km]', fontsize=label_fontsize)
ax3.set_xlabel('Epoch [UTC]', fontsize=label_fontsize, labelpad=label_labelpad)
ax3.grid(True, alpha=0.7)

# create the ephemeris data
target_times = [
    dt.datetime(2018,12,8,8,25,45), # LABELS
    dt.datetime(2018,12,8,8,28),
    dt.datetime(2018,12,8,8,31),
    dt.datetime(2018,12,8,8,34),
    dt.datetime(2018,12,8,8,37),
    dt.datetime(2018,12,8,8,40),
    dt.datetime(2018,12,8,8,43),
]

target_times_idxs = np.array([np.abs(data_dict_attitude['Epoch'][0] - tme).argmin() for tme in target_times])
time_labels = np.array([label.strftime("%H:%M") for label in target_times])
alt_labels = [str(int(round(tick/stl.m_to_km, 0))) for tick in data_dict_attitude['alt'][0][target_times_idxs]]
lat_ticks =  [str(round(tick, 2)) for tick in data_dict_attitude['latg'][0][target_times_idxs]]
emphemris_Labels = [f'{time_labels[k]}\n{alt_labels[k]}\n{lat_ticks[k]}' for k in range(len(target_times_idxs))]
emphemris_Labels[0] = 'time [UTC]\nAlt [km]\nILat [deg]'
ax3.set_xticks(target_times)
ax3.set_xticklabels(emphemris_Labels)


# --- --- --- --- --- ---
# --- Lat vs Long DATA ---
# --- --- --- --- --- ---
# get the map of the norwegian coast
projProjection = ccrs.Orthographic(central_longitude=15, central_latitude=70)
projTransform = ccrs.PlateCarree()

ax6 = fig.add_subplot(gs0[:, 1],projection=projProjection)

ax6.plot(data_dict_attitude['long'][0],
         data_dict_attitude['latg'][0],
         color='tab:blue',
         transform=projTransform,
         linewidth=plot_linewidth
         )

ax6.set_ylabel('Latitude [deg]', fontsize=label_fontsize)
ax6.set_xlabel('Longitude [deg]', fontsize=label_fontsize, labelpad=label_labelpad)

gl = ax6.gridlines(draw_labels=True, linewidth=2,
                                   alpha=0.3,
                                   linestyle='--',
                                   color='black')

gl.xlabel_style = {'size': 20, 'color': 'black', 'weight': 'bold'}
gl.ylabel_style = {'size': 20, 'color': 'black', 'weight': 'bold'}
gl.top_labels = False
gl.left_labels = False

lonW = 7.5
lonE = 22.5
latS = 67
latN = 85
res = '50m'
ax6.set_extent([lonW, lonE, latS, latN])  # controls lat/long axes display
ax6.coastlines(resolution=res, color='black',  alpha=1,linewidth=2)  # adds coastlines with resolution


# --- --- --- --- --- ---
# --- PLOT ADJUSTMENTS ---
# --- --- --- --- --- ---
axes = [ax1,ax2,ax3,ax6]

fig.align_ylabels([ax1,ax2,ax3])

for idx,ax in enumerate(axes):

    ax.tick_params(axis='y', which='major', labelsize=tick_labelsize, width=tick_width, length=tick_length)
    ax.tick_params(axis='y', which='minor', labelsize=tick_labelsize, width=tick_width, length=tick_length / 2)
    ax.tick_params(axis='x', which='major', labelsize=tick_labelsize, width=tick_width, length=tick_length)
    ax.tick_params(axis='x', which='minor', labelsize=tick_labelsize, width=tick_width, length=tick_length / 2)

    if ax in [ax1, ax2]:
        ax.set_xticklabels([])

    if ax not in [ax6]:
        ax.set_xlim(data_dict_attitude['Epoch'][0][0], data_dict_attitude['Epoch'][0][-1])

plt.tight_layout()
plt.savefig(r'C:\Users\cfelt\Desktop\Research\OCHRE\plots\TRICE_trajectory_projection.png',dpi=300)
stl.Done(start_time)