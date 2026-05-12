'''main file for pipeline'''

import sys
from livelcs.Util.util import (
    find_lsst_config,
    parse_arguments,
    open_tap_service,
    prepare_butler,
    query_coords,
    make_temp_yaml_with_new_roi
)
#from astropy.time import Time as astro_time
import astropy.units as u
from lsst.daf.butler import (
    Timespan,
    Butler
)
from lightcurver.structure.user_config import get_user_config
from lightcurver.processes.star_querying import query_gaia_stars
from lightcurver.processes.cutout_making import extract_all_stamps
from lightcurver.processes.psf_modelling import model_all_psfs
from lightcurver.processes.normalization_calculation import calculate_coefficient
from lightcurver.processes.star_photometry import do_star_photometry
#import Starred
#import PYCS
#import pyvo
#import os
#import subprocess
#import argparse
import sys
#import CCE/HME detection
import numpy as np

import lsst.sphgeom as sphgeom
#import lsst.geom as geom

# We need access to the environmental variables because that's where the lightcurver config is stored
from os import environ
from os import path


# Include a string of the file path to the config_LSST file if not automatically detected.
# Note that it must be named "config_LSST.yaml"
known_config_path = None 
config_path = find_lsst_config(known_config_path)


# butler configuration
butler_config = "dp1"
butler_collections = "LSSTComCam/DP1"



### read in file of coordinates
# the targets parameter holds a dictionary of all objects in the provided file
if len(sys.argv) == 0:
    print("please provide a file holding a list of objects when calling this script")
all_arguments = sys.argv[1:]
targets, other_args = parse_arguments(all_arguments)


### make temporary configuration file to place ROI at current objects
this_config_file, raw_dir = make_temp_yaml_with_new_roi(targets, config_path)
environ['LIGHTCURVER_CONFIG'] = this_config_file


### open up a tap service #######I think this is redundant
# requires token to be stored on the machine
#rsp_tap = open_tap_service() 


### set up the butler, store your RSP token as envirionment variable "ACCESS_TOKEN" 
butler = prepare_butler(butler_config, butler_collections)


### query given coordinates

# we now have the coordinates for object [ii] defined as
# (targets[ii]['ra'], targets[ii]['dec'])



## wrap this in a loop per object in monitoring list


# this produces a list of visit images
all_data = []

for jj in range(len(targets)):

    ra = targets[jj]['ra']
    dec = targets[jj]['dec']
    lsst_bands = ['u'] #list('ugrizy')

    time_start = None #40587
    time_stop = None
    cutout_size = 500


    current_position = []
    for band in lsst_bands:
            
        current_data = query_coords(
            butler,
            band,
            ra,
            dec,
            raw_dir=raw_dir,
            time_start=time_start,
            time_stop=time_stop,
            cutout_size=cutout_size,
            verbose=True
        )

        current_position.append(current_data)
    all_data.append(current_position)

    
for item in all_data:
    print(item)
exit()


# import sources from live_light_curves.source_list using some json interface
# for each observation:
    # check if any coordinates in sources lay within FOV
        # any which fall within the visit images will be selected
    




### run Lightcurver steps 4-6 to get PSF from nearby stars

# pass each newly generated cutout to Lightcurver stamp extraction and PSF modeling
# initialize live_light_curves.Classes.stellar_cutouts with the Lightcurver outputs



### have "Narrow PSF"

# initialize live_light_curves.Classes.narrow_psf so it works with this pipeline



### Lightcurver step 7 for stellar photometry (opt)
# initialize live_light_curves.Classes.stellar_photometry if we want to push stellar light curves


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













