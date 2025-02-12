# --- Plot1_AllSky.py ---
# --- Author: C. Feltman ---
# DESCRIPTION: All Sky Imager data plot



# --- bookkeeping ---
# !/usr/bin/env python
__author__ = "Connor Feltman"
__date__ = "2022-08-22"
__version__ = "1.0.0"
from myImports import *
start_time = time.time()
# --- --- --- --- ---

# --- --- --- ---
# --- IMPORTS ---
# --- --- --- ---
import cartopy.crs as ccrs
import spaceToolsLib as stl

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
altLatPlot = False
AltLat_Height = 10
AltLat_Width = 15
trajColors = ['tab:red', 'tab:orange']
altLat_labelFontSize = 15
altLat_textSize = 55
altLat_TickLabelSize = 65
altLat_TickLength = 30
altLat_TickWidth = 4
altLat_scatterSize = 800
altLat_lineThickness = 4
AltLat_LegendSize = 55
altLat_LabelPadding = 10
altLat_TitleFontSize = 20
# --------------------------------



# --- --- --- --- --- --- -
# --- LOAD ALL THE DATA ---
# --- --- --- --- --- --- -

# trajectory
attitudeFolderPath = f'{TRICE_data_folder}\\attitude'
inputFilesTraj = [glob(f'{attitudeFolderPath}\\{fliers[0]}\\*.cdf*')[0],
                  glob(f'{attitudeFolderPath}\\{fliers[1]}\\*.cdf*')[0]]

# --- GET TRAJECTORY DATA ---
prgMsg(f'Loading TRICEII traj data')
data_dicts_attitude = [loadDictFromFile(inputFilesTraj[0]), loadDictFromFile(inputFilesTraj[1])]

# define some variables
Epoch = [data_dicts_attitude[0]['Epoch'][0], data_dicts_attitude[1]['Epoch'][0]]
alt = [data_dicts_attitude[0]['alt'][0], data_dicts_attitude[1]['alt'][0]]
lat = [data_dicts_attitude[0]['latg'][0], data_dicts_attitude[1]['latg'][0]]
long = [data_dicts_attitude[0]['long'][0], data_dicts_attitude[1]['long'][0]]
Done(start_time)


# unique moments in High Flyer EEPAA data

terminatorUTC = dt.datetime(2018,12,8,8,28,54)
cuspUTC = [dt.datetime(2018, 12, 8, 8, 34, 30),
        dt.datetime(2018, 12, 8, 8, 37, 58)]

terminatorIdx = np.abs(Epoch[0] - terminatorUTC).argmin()
terminatorAlt = alt[0][terminatorIdx]
terminatorLat = lat[0][terminatorIdx]
cuspIdxes = [np.abs(Epoch[0] - thing).argmin() for thing in cuspUTC]


############################
# --- --- --- --- --- --- --
# --- START THE PLOTTING ---
# --- --- --- --- --- --- --
############################

# --- ALTITUDE VS LATITUDE PLOT ---
stl.prgMsg('Plotting AltLat')

# --- --- --- --- ---
# --- AltLat plot ---
# --- --- --- --- ---
fig, ax = plt.subplots()
figure_height = AltLat_Height
figure_width = AltLat_Width
fig.set_figwidth(figure_width)
fig.set_figheight(figure_height)

ax.set_title('TRICEII High Flyer Trajectory', fontsize=altLat_TitleFontSize)
ax.plot(lat[0], alt[0]/stl.m_to_km, linewidth=altLat_lineThickness)
ax.scatter(terminatorLat,terminatorAlt,label='Above Terminator (Start)')
ax.set_xlim(69, 86)
ax.set_ylim(0, 1200)
ax.set_ylabel('Altitude [km]', fontsize=altLat_labelFontSize,weight='bold', labelpad=altLat_LabelPadding)
ax.set_xlabel('Lattitude [deg]', fontsize=altLat_labelFontSize,weight='bold', labelpad=altLat_LabelPadding)
ax.axvspan(lat[0][cuspIdxes[0]],lat[0][cuspIdxes[1]], color='red',alpha=0.3)
ax.legend()
plt.savefig(r'C:\Users\cfelt\Desktop\OCHRE_AltLat.png')


# # plot the pseudo geomagnetic field line
# slope = -1 * (111 / np.sin(np.radians(90 - 78.13)))  # corresponds to line with -78.13deg inclination
# for i in range(31):
#     axAltLat.axline(xy1=(69 + i * 0.25, 0), slope=slope, color='tab:blue', linewidth=altLat_lineThickness, linestyle='-.', alpha=0.3)
# axAltLat.legend(['B$_{Geo}$'], loc='upper right',fontsize=AltLat_LegendSize)
#
# # plot the UTC labels
# axGeomLat = axAltLat.twiny()
# axGeomLat.plot(geoMagLat[0], geoAlt[0]/1000, color=trajColors[0], alpha=0)  # High
# axGeomLat.plot(geoMagLat[1], geoAlt[1]/1000, color=trajColors[1], alpha=0)  # Low
# axGeomLat.set_xlabel('Geomagnetic Latitude [deg]',fontsize=altLat_labelFontSize,weight='bold',labelpad=altLat_LabelPadding)
# AltLat_vertical_Alignments = ['bottom' for tme in timeTargetsUTC]
# AltLat_horizontal_Alignments = ['right', 'right', 'right', 'center', 'left', 'left', 'left']
# # vertical_text_label_adjustments = [-0.04, -0.03, 0.02, 0.06, 0.02, -0.04, -0.04]
# vertical_text_label_adjustments = [-0.09, -0.06, -0.005, 0.04, -0.01, -0.06, -0.09]
# horizontal_text_label_adjustments = [-0.002, -0.0015, -0.001, 0.0, 0.001, 0.0015, 0.002]
#
# # plot the scatterpoint of each of the timeTargetUTC_labels. Plot the text itself only for the High Flyer and
# # create a connecting line between the scatterpoints between the flyers
# for i in range(2):  # for each rocket
#     for j, ttme in enumerate(timeTargetsUTC):
#         Index = np.abs(EpochRocket[i] - ttme).argmin()
#         xPos = geoLat[i][Index]
#         yPos = geoAlt[i][Index]/1000
#
#         if i == 0:
#             # plot the text itself
#             label = EpochRocket[i][Index]
#             deltaY = vertical_text_label_adjustments[j] * yPos
#             deltaX = horizontal_text_label_adjustments[j] * xPos
#             axAltLat.text(x=xPos + deltaX, y=yPos + deltaY, s=label.strftime("%H:%M:%S"), color='black',weight='bold',
#                           va=AltLat_vertical_Alignments[j], ha=AltLat_horizontal_Alignments[j], size=altLat_textSize)
#
#             # plot the connecting line
#             Index_LF = np.abs(EpochRocket[1] - ttme).argmin()
#             xPos_LF = geoLat[1][Index_LF]
#             yPos_LF = geoAlt[1][Index_LF]/1000
#             axAltLat.plot([xPos, xPos_LF], [yPos, yPos_LF], color='green', linestyle='--', alpha=0.5,linewidth=altLat_lineThickness)
#             # axAltLat.axline(xy1=(xPos, yPos), xy2=(xPos_LF, yPos_LF), color='green', linestyle='--', alpha=0.5)
#
#         # plot a dot at the text label
#         axAltLat.scatter(x=xPos, y=yPos, s=altLat_scatterSize, marker="o", color=trajColors[i])
#
# # adjust the tick label size
# axAltLat.tick_params(axis='both', labelsize=altLat_TickLabelSize, length=altLat_TickLength, width=altLat_TickWidth)
# axAltLat.tick_params(axis='both', which='minor', length=int(altLat_TickLength*0.65), width=altLat_TickWidth)
# axGeomLat.tick_params(axis='both', labelsize=altLat_TickLabelSize, length=altLat_TickLength, width=altLat_TickWidth)
# axGeomLat.tick_params(axis='both', which='minor', length=int(altLat_TickLength*0.65) , width=altLat_TickWidth)
# axAltLat.minorticks_on()
# axGeomLat.minorticks_on()
#
# # plot the trajectory over everything
# axAltLat.plot(geoLat[0], geoAlt[0]/1000, color=trajColors[0], label='High Flyer',linewidth=altLat_lineThickness)  # High
# axAltLat.plot(geoLat[1], geoAlt[1]/1000, color=trajColors[1], label='Low Flyer',linewidth=altLat_lineThickness)  # Low
#
# plt.tight_layout()
# plt.savefig(r'C:\Users\cfelt\OneDrive\Desktop\OCHRE_AltLat.png')
# Done(start_time)
# plt.show()
