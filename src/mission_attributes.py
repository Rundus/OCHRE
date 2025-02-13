# --- mission_attributes.py ---
# --- Author: C. Feltman ---
# DESCRIPTION: Place to store the attributes specific to certain rockets

import datetime as dt

class TRICEII:

    # --- General Mission Info---
    mission_name = 'TRICEII'
    payload_IDs = ['52003', '52004']
    fliers = ['high', 'low']
    instrument_names_full = ['EEPAA>Electron Energy Pitch Angle Analyzer'
                             ]

    # --- Launch Conditions ---
    launch_lat_long = [69.294167, 16.020833]  # andoya
    launch_magnetic_inclination = 78.1300  # in deg
    launch_T0_dt = [dt.datetime(2018,12,8,8,26,00,000000),
                    dt.datetime(2018,12,8,8,28,00,000000)]
    launch_T0_TT2000 = []  # TT2000 values corresponding to 17:20:00 and 17:21:40 for high/low flyer, respectively.


    # --- File I/O ---
    global_attributes = [
        {'Source_name': f'TRICEII_52003>TRICE II 52.003',
         'Data_type': 'K0>Key Parameter',
         'PI_name': 'Kletzing',
         'Logical_source': f'triceii_52003_',
         'Logical_file_id': f'triceii_52003_00000000_v01',
         'Logical_source_description': 'Raw Data from the TRICEII mission organized by minorframe.150 words per minor frame.40 minor frames to a major frame.',
         'TEXT': 'Raw Data from the TRICEII mission organized by minorframe.150 words per minor frame.40 minor frames to a major frame.'
         },
        {'Source_name': f'TRICEII_52004>TRICE II 52.004',
         'Data_type': 'K0>Key Parameter',
         'PI_name': 'Kletzing',
         'Logical_source': f'triceii_52004_',
         'Logical_file_id': f'triceii_52004_00000000_v01',
         'Logical_source_description': 'Raw Data from the TRICEII mission organized by minorframe.150 words per minor frame.40 minor frames to a major frame.',
         'TEXT': 'Raw Data from the TRICEII mission organized by minorframe.150 words per minor frame.40 minor frames to a major frame.'
         }]

    # --- De-Coming the Data --
    g_nWords = 150
    g_nNomRecLen = 150 * 2 + 12
    nNomDataLen = 150 - 2
    gSync = b'\x40\x28\x6b\xfe'  # g_sSync = "\xfe\x6b\x28\x40"  is the real frame sync but the data is little endian
    nDataLen = "74I"
