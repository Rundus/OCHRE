


class AllSky:

    modifier = ''
    inputPath_modifier_AllSky = 'all_sky'  # e.g. 'L1' or 'L1'. It's the name of the broader input folder inside data\ACESII
    outputPath_modifier = 'all_sky'  # e.g. 'L2' or 'Langmuir'. It's the name of the broader output folder inside data\ACESII\ACESII_matlab

    wLengths = ['5577', '6300']
    architecture = 65535  # type of bit-architecture used for the allSky images. Nomially 16-bit
    elevlimits = [20, 20]  # value (in deg) of the cutoff elevation angle for the 5577A and 6300A line
