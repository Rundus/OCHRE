# --- LP_cal_preFlight_current_expectation ---

#################
# --- IMPORTS ---
#################
# For given times, altitudes, lats, longs, export the IRI data to a  .cdf file
import datetime

import matplotlib.pyplot as plt
import numpy as np

import iri2020.times as time_profile
import iri2020.latitude as lat_profile
import iri2020.altitude as alt_profile
import numpy as np
import os
import datetime as dt
import spaceToolsLib as stl

#################
# --- TOGGLES ---
#################

# --- Altitude Profile ---
time_rez = 1 / 60  # in Hours
alt_start = 70
alt_end = 1000
alt_rez = 2  # in kilometers
alt_range = np.linspace(alt_start, alt_end, int((alt_end - alt_start) / alt_rez))

INPUTS = {'1': {'time': ('2026-2-1T11:00', '2026-2-1T11:01', time_rez), 'glat': 79.09, 'glon': 16.01,
                'alts': (alt_start, alt_end, alt_rez)},
          }


def LP_cal_preFlight_current_expectation():


    # --- GET THE IRI DATA ---
    for event in INPUTS.keys():

        # get the event data
        time = INPUTS[event]['time']
        glat = INPUTS[event]['glat']
        glon = INPUTS[event]['glon']
        alts = INPUTS[event]['alts']

        # --- Run the IRI data ---
        data = time_profile.main(time, alts, glat, glon)
        coords = data.coords
        attrs = data.attrs

        # --- Store Everything in a .cdf ---
        data_dict_output = {}

        # add the coordinates
        for key in coords.keys():

            outdata = np.array(coords[key])
            if key in ['alt_km']:
                unit = 'km'
            if key in ['time']:
                # convert numpy64 datetime to python datetime datetime
                outdata = np.array([time.astype(datetime.datetime) for time in outdata])
                unit = None
            else:
                outdata = np.array([coords[key]])
                unit = None

            data_dict_output = {**data_dict_output,
                                **{f'{key}': [outdata, {'UNITS': unit}]}
                                }
        # add the attributes
        for key in attrs.keys():
            unit = None
            data_dict_output = {**data_dict_output,
                                **{f'{key}': [np.array([attrs[key]]), {'UNITS': unit}]}
                                }

        # add the data to the data dict
        for key in data.keys():

            # get the data
            input_data = data[key]

            # get the metadaya info
            if key in ['ne', 'nO+', 'nH+', 'nNO+', 'nO2+', 'nN+', 'nCI', 'nHe+']:
                unit = 'm!A-3!N'
            elif key in ['Tn', 'Te', 'Ti']:
                unit = 'K'
            else:
                unit = None

            data_dict_output = {**data_dict_output,
                                **{
                                    f'{key}': [input_data.to_numpy(),
                                               {
                                                   'DEPEND_0': 'time',
                                                   'DEPEND_1': 'alt_km',
                                                   'UNITS': unit,
                                               }]
                                }
                                }

        # Calculate the Debeye Length
        density = np.sum([data_dict_output[key][0] for key in ['nO+', 'nHe+', 'nH+', 'nO2+', 'nNO+', 'nN+']], axis=0) # in m^-3
        debeye = np.sqrt(stl.ep0 * stl.kB * data_dict_output['Te'][0] / (stl.q0 * stl.q0 * density))


    # --- PLOT THE DATA ---

    fig, ax = plt.subplots(3,1)
    ax[0].plot(data_dict_output['Te'][0], data_dict_output['alt_km'][0][0], label='Te')
    ax[0].plot(data_dict_output['Ti'][0], data_dict_output['alt_km'][0][0], label='Ti')
    ax[0].legend()
    ax[0].set_xlabel('Temperature [K]')
    ax[0].set_xlabel('Altitude [km]')

    ax[1].plot(data_dict_output['ne'][0], data_dict_output['alt_km'][0][0], label='ne')
    ax[1].plot(density, data_dict_output['alt_km'][0][0], label='ni')
    ax[1].legend()
    ax[1].set_xlabel('Density [cm^-3]')
    ax[1].set_xlabel('Altitude [km]')

    ax[2].plot(debeye * stl.cm_to_m, data_dict_output['alt_km'][0][0])
    ax[2].axvline(x=2.54, color='red',linestyle='--')
    ax[2].set_ylabel('Altitude [km]')
    ax[2].set_xlabel('Debeye Length [cm]')
    plt.show()


LP_cal_preFlight_current_expectation()


