# --- LP_cal_preFlight_current_expectation ---

#################
# --- IMPORTS ---
#################
# For given times, altitudes, lats, longs, export the IRI data to a  .cdf file
import datetime

import matplotlib.pyplot as plt
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


    # --- Calculate the expected current ---
    ## 2. constants
    probe_radius = 0.0127  # meters
    A = 4 * np.pi * (probe_radius ** 2)

    kB = 1.380649e-23  # J/K
    qe = 1.602176634e-19  # C

    ion_names = ["O+", "H+", "N+", "He+", "O2+", "NO+"]
    masses = np.array([[stl.ion_dict[name]] for name in ion_names])
    densities = np.array([data_dict_output[f'n{key}'][0] for key in ion_names])

    me = 9.10938356e-31  # kg
    # weighted average for mass
    mi_avg = np.sum(masses * densities, axis=0) / np.sum(densities, axis=0)
    mi_av_norm = mi_avg / stl.ion_dict['proton']

    density_multiplier = 3
    Ti_multiplier = 3

    ni = np.sum(densities, axis=0)*density_multiplier
    ne = data_dict_output["ne"][0]*density_multiplier

    Ti = data_dict_output["Ti"][0]*Ti_multiplier
    Te = data_dict_output["Te"][0]
    phi_dif_ion = 7
    phi_dif_elec = 1

    # 4. CALCULATE CURRENTS
    I_e = (ne * qe * A * np.sqrt(kB * Te / (2 * np.pi * me))) / (1E-6)
    I_i = (ni * qe * A * np.sqrt(kB * Ti / (2 * np.pi * mi_avg))) / (1E-6)
    I_e_est = I_e * (1 + ((qe * (phi_dif_elec))) / (kB * Te))
    I_i_est = I_i * (1 + ((qe * (phi_dif_ion))) / (kB * Ti))

    # --- PLOT THE DATA ---
    fig, ax = plt.subplots(2,2)
    fig.set_figwidth(15)
    fig.set_figheight(15)
    ax[0, 0].plot(data_dict_output['Te'][0], data_dict_output['alt_km'][0][0], label='Te')
    ax[0, 0].plot(data_dict_output['Ti'][0], data_dict_output['alt_km'][0][0], label='Ti')
    ax[0, 0].legend()
    ax[0, 0].text(0.25, 0.9, s=f'T$_i$ multiplier (x{Ti_multiplier})', color='black', transform=ax[0, 0].transAxes, fontsize=20)
    ax[0, 0].set_xlabel('Temperature [K]')
    ax[0, 0].set_ylabel('Altitude [km]')

    ax[0, 1].plot(data_dict_output['ne'][0]/(stl.cm_to_m**3), data_dict_output['alt_km'][0][0], label='ne')
    ax[0, 1].plot(density/(stl.cm_to_m**3), data_dict_output['alt_km'][0][0], label='ni')
    ax[0, 1].legend()
    ax[0, 1].set_xlabel('Density [cm^-3]')
    ax[0,1].set_xscale('log')
    ax[0,1].text(0.25, 0.9, s=f'n$_e$ multiplier (x{density_multiplier})', color='black', transform=ax[0,1].transAxes, fontsize=20)
    ax[0, 1].set_ylabel('Altitude [km]')

    ax[1, 0].plot(debeye * stl.cm_to_m, data_dict_output['alt_km'][0][0])
    ax[1, 0].axvline(x=2.54, color='red',linestyle='--')
    ax[1, 0].set_ylabel('Altitude [km]')
    ax[1, 0].set_xlabel('Debeye Length [cm]')

    ax[1, 1].plot(I_e_est, data_dict_output['alt_km'][0][0],label='I$_{th,e}$')
    ax[1, 1].plot(I_i_est, data_dict_output['alt_km'][0][0], label='I$_{th,i}$')
    ax[1, 1].set_ylabel('Altitude [km]')
    ax[1, 1].set_xlabel('Current [uA]')
    ax[1, 1].set_xscale('log')
    ax[1, 1].text(0.5, 0.9, s='I$_{max}$$^{i}$='+f'{round(max(I_i_est),1)} uA', color='red', transform=ax[1, 1].transAxes, fontsize=20)
    ax[1, 1].text(0.5, 0.7, s='I$_{max}$$^{e}$=' + f'{round(max(I_e_est), 1)} uA', color='black',transform=ax[1, 1].transAxes, fontsize=20)

    plt.tight_layout()
    plt.show()


LP_cal_preFlight_current_expectation()


