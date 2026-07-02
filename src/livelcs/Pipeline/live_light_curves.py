'''main file for pipeline'''

import sys
from livelcs.Util.util import (
    find_lsst_config,
    parse_arguments,
    prepare_butler,
    query_coords,
    make_temp_yaml_with_new_roi,
    load_light_curve, 
    clean_directory_structure_for_lightcurver,
    extract_ra_dec_target_string
)
#from astropy.time import Time as astro_time
#import astropy.units as u
from lsst.daf.butler import (
    Timespan,
    Butler
)
from lightcurver.structure.user_config import get_user_config
from lightcurver.structure.database import initialize_database
from lightcurver.pipeline.task_wrappers import read_convert_skysub_character_catalog
from lightcurver.pipeline.task_wrappers import plate_solve_all_frames, calc_common_and_total_footprint_and_save
from lightcurver.processes.star_querying import query_gaia_stars
from lightcurver.processes.cutout_making import extract_all_stamps
from lightcurver.processes.psf_modelling import model_all_psfs
from lightcurver.processes.normalization_calculation import calculate_coefficient
from lightcurver.processes.star_photometry import do_star_photometry
from lightcurver.processes.absolute_zeropoint_calculation import calculate_zeropoints
from lightcurver.processes.roi_file_preparation import prepare_roi_file
from lightcurver.processes.roi_modelling import do_modelling_of_roi
#import Starred
#import PYCS
#import pyvo
#import subprocess
#import argparse
#import CCE/HME detection
from numpy import linspace
from pandas import DataFrame
import tqdm

#import lsst.sphgeom as sphgeom
#import lsst.geom as geom

# We need access to the environmental variables because that's where the lightcurver config is stored
from os import environ
#from os import path



### read in file of coordinates
# the targets parameter holds a dictionary of all objects in the provided file
if len(sys.argv) == 1:
    print("please provide a file holding a list of objects when calling this script")
all_arguments = sys.argv[1:]
targets, other_args = parse_arguments(all_arguments)


# Include a string of the file path to the config_LSST file if not automatically detected.
# Note that it must be named "config_LSST.yaml"
known_config_path = other_args["known_lightcurver_config_path"] 
config_path = find_lsst_config(known_config_path)


# butler configuration, which needs to be updated as data releases come out
butler_config = other_args["butler_config"] # e.g. "dp1"
butler_collections = other_args["butler_collections"] # e.g. "LSSTComCam/DP1"


### set up the butler, store your RSP token as envirionment variable "ACCESS_TOKEN" 
butler = prepare_butler(
    configuration=butler_config, 
    collections=butler_collections
)


### query given coordinates
# this produces a list of visit images
all_data = []

if type(targets) != DataFrame:
    print("Warning: targets could not be read into a pandas dataframe.")

for jj in tqdm.tqdm(range((targets.shape[0]))):

    working_series = targets.iloc[jj]

    target_string, ra, dec = extract_ra_dec_target_string(working_series)
    if target_string is None:
        continue

    # this will be an input parameter
    lsst_bands = other_args["lsst_bands"]

    if other_args["verbose"]:
        print(target_string)

    light_curve = load_light_curve(target_string)

    if other_args["redo_light_curve"]:
        time_start = float(other_args["time_start"])
    else:
        if light_curve.data["time_last_updated"] is not None:
            time_start = float(light_curve.data["time_last_updated"])
        else:
            time_start = 40587
    time_stop = float(other_args["time_stop"])

    cutout_size = int(other_args["cutout_size"]) # in pixels, so 100 means 100x100 cutouts
    time_interval = float(other_args["time_interval"]) # check in batches of time

    time_endpoints = linspace(time_start, time_stop, int((time_stop-time_start)/time_interval))
    time_intervals = [(time_endpoints[ii], time_endpoints[ii+1]) for ii in range(len(time_endpoints)-1)]

    ### make temporary configuration file to place ROI at current objects 
    # Need new temp yaml file per target
    this_config_file, raw_dir = make_temp_yaml_with_new_roi(working_series, config_path)
    environ['LIGHTCURVER_CONFIG'] = this_config_file

    current_position = []

    for time_interval in tqdm.tqdm(time_intervals):
        for band in lsst_bands:
            # Get all frames within a given time interval from Butler
            written_files = query_coords(
                butler,
                band,
                ra,
                dec,
                raw_dir=raw_dir,
                time_start=time_interval[0],
                time_stop=time_interval[1],
                cutout_size=cutout_size,
                verbose=True
            )

            if len(written_files) > 0:

                # Lightcurver requires this main wrapper on some systems.
                # Add switch to use supersampled PSF from LSST pipeline
                if __name__ == '__main__':
                    get_user_config()
                    initialize_database()
                    read_convert_skysub_character_catalog()
                    plate_solve_all_frames()
                    calc_common_and_total_footprint_and_save()
                    query_gaia_stars()
                    extract_all_stamps()
                    model_all_psfs()
                    do_star_photometry()
                    calculate_coefficient()
                    calculate_zeropoints()
                    prepare_roi_file()
                    do_modelling_of_roi()

                    clean_directory_structure_for_lightcurver(
                        base_dir=other_args["base_working_directory"],
                        blacklist_dirs=other_args["blacklist_dirs"]
                    )


    
for item in all_data:
    print(item)
exit()




### Starred to get deconvolved sources (requires point source initial positions)
# deconvolve cutouts with computed PSF (this could just be done within the cutout object)
# Q: does this get all sources (e.g. plus stars, host galaxy), or just lensed point sources?


### Starred returns calibrated light curve data point
# load current object light curves and append the new data point



### When enough data is collected, run PYCS3 or SBI to get time delays
# if a source's light curve passes some critical threshold (e.g. in time), run PYCS



### While collecting, run RNN detection to test for imminent HMEs
# if a source's light curve passes a critical threshold, run caustic crossing detection software



### Send alerts when detected
# if an alert is triggered, send the alert



### Update HTML interface
# always send updated light curves to the web interface daily
# perhaps we could be inspired by some code here https://github.com/duxfrederic/lightcurver/blob/main/lightcurver/plotting/plot_curves_template.html













