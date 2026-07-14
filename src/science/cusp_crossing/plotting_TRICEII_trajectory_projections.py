# --- Plot1_AllSky.py ---
# --- Author: C. Feltman ---
# DESCRIPTION: All Sky Imager data plot



# --- bookkeeping ---
# !/usr/bin/env python
__author__ = "Connor Feltman"
__date__ = "2022-08-22"
__version__ = "1.0.0"

import itertools

import aacgmv2
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
from toggles import TRICEII_traj
from itertools import cycle
import cartopy.crs as ccrs
from cartopy.feature.nightshade import Nightshade


# --- --- --- ---
# --- TOGGLES ---
# --- --- --- ---

plot_electrons = True
plot_ions = True
plot_altvslat = True
plot_MLT = True
plot_allsky = True

# --------------ALTvsLAT------------------
plot_height = 15
plot_Width = 20
plot_linewidth = 10
plot_markersize = 15
scatter_markersize = 800
label_fontsize = 30
label_labelpad = 15
text_fontsize = 20
tick_labelsize = 20
tick_length = 10
tick_width = 3

legend_fontsize = 20
title_fontsize = 40
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

# all sky data
data_dict_allSky = stl.loadDictFromFile(r'C:\Data\TRICEII\all_sky\6300\nyAlesund\TRICEII_all_sky_6300_nyAlesund.cdf')
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
fig.suptitle('TRICE-II 52.003', fontsize=title_fontsize, fontweight='bold')
gs0 = gridspec.GridSpec(nrows=3, ncols=2, figure=fig, height_ratios=[0.2, 0.2, 0.6], width_ratios=[0.6, 0.4])


if plot_electrons:
    # --- --- --- --- --
    # --- EEPAA DATA ---
    # --- --- --- --- --
    ax1 = fig.add_subplot(gs0[0,0])

    low_idx, high_idx = np.abs(data_dict_eepaa['Epoch'][0] - data_dict_attitude['Epoch'][0][0]).argmin(),np.abs(data_dict_eepaa['Epoch'][0] - data_dict_attitude['Epoch'][0][-1]).argmin()

    ax1.pcolormesh(data_dict_eepaa['Epoch'][0][low_idx:high_idx],
                   data_dict_eepaa['Energy'][0],
                   eepaa_avg[low_idx:high_idx].T,
                   cmap=my_cmap,
                   vmin=1E3,
                   vmax=1E8,
                   norm='log')

    ax1.set_yscale('log')
    ax1.set_ylabel('Electron\nEnergy [eV]', fontsize=label_fontsize-5)

if plot_ions:
    # --- --- --- --- --
    # --- ACI DATA ---
    # --- --- --- --- --
    ax2 = fig.add_subplot(gs0[1,0])

    low_idx, high_idx = np.abs(data_dict_ion['Epoch'][0] - data_dict_attitude['Epoch'][0][0]).argmin(), np.abs(
        data_dict_ion['Epoch'][0] - data_dict_attitude['Epoch'][0][-1]).argmin()

    ax2.pcolormesh(data_dict_ion['Epoch'][0][low_idx:high_idx],
                   data_dict_ion['trice1_ion_energy'][0],
                   ion_avg[low_idx:high_idx].T,
                   cmap=my_cmap,
                   vmin=1E2,
                   vmax=1E5,
                   shading='nearest',
                   norm='log'
                   )

    ax2.set_yscale('log')
    ax2.set_ylabel('Ion\n Energy [eV]', fontsize=label_fontsize-5)

if plot_altvslat:
    # --- --- --- --- --- --- --- -
    # --- ALT vs Ephemeris DATA ---
    # --- --- --- --- --- --- --- -

    ax3 = fig.add_subplot(gs0[2, 0])

    ax3.plot(data_dict_attitude['latg'][0],
             data_dict_attitude['alt'][0]/stl.m_to_km,
             color='tab:purple',
             linewidth=plot_linewidth,
             zorder=0,
             label='Launch')

    ax3.set_ylabel('Altitude [km]', fontsize=label_fontsize)
    ax3.set_xlim(68, 85)
    ax3.grid(True, alpha=0.7)

    # create the ephemeris data
    target_times = [
        dt.datetime(2018,12,8,8,28),
        dt.datetime(2018,12,8,8,31),
        dt.datetime(2018,12,8,8,34),
        dt.datetime(2018,12,8,8,37),
        dt.datetime(2018,12,8,8,40),
        dt.datetime(2018,12,8,8,43)
    ]

    target_times_idxs = np.array([np.abs(data_dict_attitude['Epoch'][0] - tme).argmin() for tme in target_times])
    time_labels = np.array([label.strftime("%H:%M") for label in target_times])
    alt_labels =[str(int(round(tick/stl.m_to_km, 0))) for tick in data_dict_attitude['alt'][0][target_times_idxs]]
    lat_ticks = [str(round(tick, 2)) for tick in data_dict_attitude['latg'][0][target_times_idxs]]
    emphemris_Labels = [f'{time_labels[k]}\n{alt_labels[k]}\n{lat_ticks[k]}' for k in range(len(target_times_idxs))]
    ax3.set_xticks(data_dict_attitude['latg'][0][target_times_idxs])
    ax3.set_xticklabels(emphemris_Labels)

    ax3.set_xlabel('time [UTC]\nAlt [km]\nLat [deg]', fontsize=15, fontweight='bold')
    ax3.xaxis.set_label_coords(-0.00, -0.03)

    # Plot the regions
    color_these_regions = [
        [TRICEII_traj.ACS1_align_to_target_B_HF, TRICEII_traj.ACS1_disable_nozzles_HF], # ACS1
        [TRICEII_traj.stacer_booms_deploy_HF,TRICEII_traj.EEPAA_deploy_HF], # instrument deployment
        [TRICEII_traj.ACS2_align_to_target_B_HF, TRICEII_traj.ACS2_complete_HF] # ACS2
    ]
    labels = ['ACS1', 'Instr. Deploy', 'ACS2']
    for idx, region in enumerate(color_these_regions):

        region_start_tme = data_dict_attitude['latg'][0][np.abs(data_dict_attitude['Epoch'][0] - region[0][0]).argmin()]
        region_end_tme = data_dict_attitude['latg'][0][np.abs(data_dict_attitude['Epoch'][0] - region[1][0]).argmin()]
        region_start_alt = data_dict_attitude['alt'][0][np.abs(data_dict_attitude['Epoch'][0] - region[0][0]).argmin()]/stl.m_to_km
        region_end_alt = data_dict_attitude['alt'][0][np.abs(data_dict_attitude['Epoch'][0] - region[1][0]).argmin()]/stl.m_to_km

        ax3.plot([region_start_tme, region_end_tme],
                 [region_start_alt, region_end_alt],
                 zorder=2,
                 linewidth=plot_linewidth,
                 label=labels[idx])

    # add the "science" region of the plot

    science_region_idx = np.abs(data_dict_attitude['Epoch'][0] - TRICEII_traj.ACS2_complete_HF[0]).argmin()
    ax3.plot( data_dict_attitude['latg'][0][science_region_idx:],
        data_dict_attitude['alt'][0][science_region_idx:]/stl.m_to_km,
        color='tab:red',
        zorder=2,
        label='Science',
        linewidth=plot_linewidth)

    # add the timeline
    show_these_points = [
        TRICEII_traj.nosecone_eject_HF,
        TRICEII_traj.ACS3_enable_deadband_7_to_10deg_HF,
        TRICEII_traj.Iowa_SwRI_HV_on_HF,
        TRICEII_traj.Apogee_HF
    ]

    alignments = cycle(['left', 'right'])
    adjustment = [0.5, -0.5, 0.5, -0.5]
    for idx, point in enumerate(show_these_points):

        # get the altitude in the REAL data of this time point
        timeline_idx = np.abs(data_dict_attitude['Epoch'][0] - point[0]).argmin()
        ax3.plot(data_dict_attitude['latg'][0][timeline_idx],
                 data_dict_attitude['alt'][0][timeline_idx]/stl.m_to_km,
                 color='black',
                 marker='o',
                 markersize=plot_markersize,
                 zorder=2)
        ax3.annotate( point[2],
                        xy=(data_dict_attitude['latg'][0][timeline_idx]+adjustment[idx],data_dict_attitude['alt'][0][timeline_idx]/stl.m_to_km),
                        va = 'center',
                        ha = next(alignments),
                        fontsize = text_fontsize,
                        color = 'black',
                        weight = 'bold',
                        zorder = 2
                      )

    ax3.legend(loc='upper right',fontsize=legend_fontsize)

    # get the B-Field
    target_time_alts = data_dict_attitude['alt'][0][target_times_idxs]/stl.m_to_km
    target_time_lats = data_dict_attitude['latg'][0][target_times_idxs]
    target_time_longs =data_dict_attitude['long'][0][target_times_idxs]
    B = stl.CHAOS(lat=target_time_lats,
              long=target_time_longs,
              alt=target_time_alts,
              times=target_times)

    inclination_angle = np.array([-1*np.degrees(np.arctan(arr[1]/arr[2])) for arr in B])

    # plot the pseudo geomagnetic field line
    slope = -1 * (111 / np.sin(np.radians(inclination_angle)))  # corresponds to line with -78.13deg inclination
    for i in range(len(target_times_idxs)):
        ax3.axline(xy1=(target_time_lats[i], target_time_alts[i]), slope=slope[i], color='tab:blue', linewidth=plot_linewidth-5, linestyle='-.', alpha=0.3)

    # denote the location of the cusp
    cusp_low_lat = data_dict_attitude['latg'][0][np.abs(data_dict_attitude['Epoch'][0] - TRICEII_traj.enter_cusp_HF).argmin()]
    cusp_high_lat = data_dict_attitude['latg'][0][np.abs(data_dict_attitude['Epoch'][0] - TRICEII_traj.leave_cusp_HF).argmin()]
    ax3.axvspan(cusp_low_lat,cusp_high_lat, color='gray', alpha=0.3)
    ax3.text(x=77.25,y=600,s='Cusp', fontsize=text_fontsize, fontweight='bold')

if plot_MLT:
    # --- --- --- ---
    # --- MLT Plot ---
    # --- --- --- ---

    # create orthographic plot and make MLT 12 the bottom
    dtime = dt.datetime(2018,12,8,8,36)
    mlon = aacgmv2.convert_mlt(12,dtime,m2a=True)
    geo_lat, geo_long, out_r = aacgmv2.convert_latlon(-30, mlon,0,dtime,method_code='A2G')

    projTransform_1 = ccrs.Geodetic()
    ax4 = fig.add_subplot(gs0[0:2,1], projection=ccrs.Orthographic(geo_long, 90))
    ax4.coastlines(zorder=3)
    ax4.stock_img()
    ax4.gridlines(draw_labels=True)
    ax4.add_feature(Nightshade(dt.datetime(2018,12,8,8,36)))
    ax4.plot(data_dict_attitude['long'][0],
             data_dict_attitude['latg'][0],
             color='red',
             linewidth=3,
             transform=projTransform_1)

if plot_allsky:
    # --- --- --- --- --- ---
    # --- Lat vs Long DATA ---
    # --- --- --- --- --- ---
    # get the map of the norwegian coast
    projProjection = ccrs.Orthographic(central_longitude=15, central_latitude=70)
    projTransform_2 = ccrs.PlateCarree()

    # create the plot
    ax6 = fig.add_subplot(gs0[2, 1], projection=projProjection)

    # plot the all sky image - 6300 at 08:36:30 UTC
    target_time_all_sky = dt.datetime(2018,12,8,8,36,30,000000)
    target_all_sky_idx = np.abs(data_dict_allSky['Epoch'][0] - target_time_all_sky).argmin()
    all_sky_image = data_dict_allSky['image_data'][0][target_all_sky_idx]
    all_sky_lats = data_dict_allSky['lats'][0]
    all_sky_longs = data_dict_allSky['longs'][0]

    # get the attitude data for the specific UTC time
    target_time_attitude_idx = np.abs(data_dict_attitude['Epoch'][0] - target_time_all_sky).argmin()
    target_lat_attitude = data_dict_attitude['latg'][0][target_time_attitude_idx]
    target_long_attitude = data_dict_attitude['long'][0][target_time_attitude_idx]

    ax6.annotate(f'{target_time_all_sky.strftime("%H:%M:%S")} UTC',
                 xy=(target_long_attitude,target_lat_attitude),
                 va='bottom',
                 ha='left',
                 fontsize=text_fontsize,
                 color='red',
                 weight='bold',
                 transform=projTransform_2,
                 zorder=2)

    ax6.plot(target_long_attitude,target_lat_attitude,
             color='red',
             marker='o',
             markersize=plot_markersize,
             transform=projTransform_2,
             zorder=2)

    ax6.pcolormesh(all_sky_longs,
                   all_sky_lats,
                   all_sky_image.T,
                   vmin=0.070001,
                   vmax=0.42979,
                   cmap=stl.apl_rainbow_black0_cmap(),
                   transform=projTransform_2,
                   zorder=0)

    # plot the payload Trajectory
    ax6.plot(data_dict_attitude['long'][0],
             data_dict_attitude['latg'][0],
             color='tab:red',
             transform=projTransform_2,
             linewidth=plot_linewidth-5,
             zorder=1
             )
    ax6.set_ylabel('Latitude [deg]', fontsize=label_fontsize)
    ax6.set_xlabel('Longitude [deg]', fontsize=label_fontsize, labelpad=label_labelpad)


    # Adjust the map gridlines
    gl = ax6.gridlines(draw_labels=True,
                       linewidth=2,
                       alpha=0.3,
                       linestyle='--',
                       color='black')

    gl.xlabel_style = {'size': 20, 'color': 'black', 'weight': 'bold'}
    gl.ylabel_style = {'size': 20, 'color': 'black', 'weight': 'bold'}
    gl.top_labels = False
    gl.left_labels = False
    lonW = 2.5
    lonE = 27.5
    latS = 67
    latN = 85
    res = '50m'
    ax6.set_extent([lonW, lonE, latS, latN])  # controls lat/long axes display
    ax6.coastlines(resolution=res, color='black',  alpha=1,linewidth=2)  # adds coastlines with resolution

if plot_electrons and plot_ions and plot_MLT and plot_allsky and plot_altvslat:
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

        # if ax not in [ax6]:
        #     ax.set_xlim(data_dict_attitude['Epoch'][0][0], data_dict_attitude['Epoch'][0][-1])

plt.tight_layout()
plt.savefig(r'C:\Users\cfelt\Desktop\Research\OCHRE\plots\TRICE_trajectory_projection.png', dpi=300)
stl.Done(start_time)