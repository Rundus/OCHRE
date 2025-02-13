# --- toggles ---
# Description: Location to store many of the variables/data
# corresponding to the variable .\\science datafiles


import datetime as dt
from src.mission_attributes import TRICEII



class TRICEII_traj:

    # --- high flyer - Timeline---
    T0_HF = TRICEII.launch_T0_dt[0]

    nosecone_eject_HF = [T0_HF + dt.timedelta(seconds=74),70, 'Nosecone\nEject']  # time, nominal km
    despin_to_1p75_HF = [T0_HF+ dt.timedelta(seconds=110),170, 'Despin']
    ACS1_align_to_target_B_HF = [T0_HF+ dt.timedelta(seconds=113),182, 'ACS1 to Bgeo']
    ACS1_disable_nozzles_HF = [T0_HF+ dt.timedelta(seconds=133),254, 'ACS1\nend']
    stacer_booms_deploy_HF = [T0_HF+ dt.timedelta(seconds=144),257, 'Stacer\nDeploy']
    EEPAA_deploy_HF = [T0_HF+ dt.timedelta(seconds=152),320, 'EEPAA\nDeploy']
    ACS2_align_to_target_B_HF = [T0_HF+ dt.timedelta(seconds=153),323, 'ACS2 to Bgeo']
    ACS2_complete_HF = [T0_HF+ dt.timedelta(seconds=168),350, 'ACS2\nend']
    ACS3_enable_deadband_7_to_10deg_HF = [T0_HF+ dt.timedelta(seconds=168), 350, 'ACS3\ndeadband']
    Iowa_SwRI_HV_on_HF = [T0_HF+ dt.timedelta(seconds=170), 354, 'HV On']
    Apogee_HF = [T0_HF+ dt.timedelta(seconds=617), 1080, 'Apogee']

    # science
    enter_terminator_HF = dt.datetime(2018, 12, 8, 8, 28, 54)
    enter_cusp_HF = dt.datetime(2018, 12, 8, 8, 34, 30)
    leave_cusp_HF = dt.datetime(2018, 12, 8, 8, 37, 58)

