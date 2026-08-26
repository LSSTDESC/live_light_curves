'''main file for pipeline'''

# We need access to the environmental variables because that's where the lightcurver config is stored
import os
import sys


# LSST specific imports 
from lsst.daf.butler import (
    Timespan,
    Butler
)
#import lsst.sphgeom as sphgeom
#import lsst.geom as geom


# Self imports 
from livelcs.Util.InternalUtil.FileManagementUtil import (
    find_lsst_config,
    make_temp_yaml_with_new_roi,
    clean_directory_structure_of_jpg_and_fits,
    find_h5_and_database
)

from livelcs.Util.InternalUtil.LiveLightCurvesUtil import (
    parse_arguments,
    load_light_curve
)

from livelcs.Util.ExternalUtil.ButlerUtil import (
    prepare_butler,
    query_coords,
    extract_image
)

from livelcs.Util.ExternalUtil.LightcurverUtil import (
    run_lightcurver
)

from livelcs.Util.ExternalUtil.StandardUtil import (
    extract_ra_dec_target_string_sources,
    extract_table_from_database,
    extract_frames_from_h5_file
)

from livelcs.Util.ExternalUtil.StarredUtil import (
    initialize_starred_variables, 
    identify_point_sources, 
    optimize_starred_fit, 
    process_fluxes,
    convert_mags_dataframe_to_light_curve
)

from livelcs.LightCurves.light_curve import LightCurve



'''
from livelcs.Util.util import (
    find_lsst_config,
    parse_arguments,
    prepare_butler,
    query_coords,
    make_temp_yaml_with_new_roi,
    load_light_curve, 
    clean_directory_structure_for_lightcurver,
    extract_ra_dec_target_string,
    extract_image, 
    extract_table_from_database,
    extract_frames_from_h5_file
)
from src.livelcs.LightCurves.light_curve import LightCurve
'''

### External imports 
import numpy as np
from pandas import DataFrame
import tqdm
from h5py import File
from copy import deepcopy 

### starred imports
from starred.deconvolution.deconvolution import (
    Deconv, 
    setup_model
)
from starred.deconvolution.loss import (
    Loss, 
    Prior
)
from starred.optim.optimization import Optimizer
from starred.utils.noise_utils import propagate_noise
from starred.deconvolution.parameters import ParametersDeconv
from starred.plots.plot_function import (
    view_deconv_model, 
    plot_loss,  # remove
    plot_deconvolution # remove
)
from starred.procedures.deconvolution_routines import multi_steps_deconvolution

# extra lightcurver imports 
from lightcurver.utilities.starred_utilities import get_flux_uncertainties
from lightcurver.utilities.lightcurves_postprocessing import group_observations, convert_flux_to_magnitude

### excess imports (for now)
#import Starred
#import PYCS
#import pyvo
#import subprocess
#import argparse
#import CCE/HME detection
#from astropy.time import Time as astro_time
#import astropy.units as u



### read in file of coordinates
# the targets parameter holds a dictionary of all objects in the provided file
if len(sys.argv) == 1:
    print("please provide a file holding a list of objects when calling this script")
all_arguments = sys.argv[1:]
targets, other_args = parse_arguments(all_arguments)
verbose = other_args["verbose"]


# Include a string of the file path to the config_LSST file if not automatically detected.
# Note that it must be named "config_LSST.yaml"
known_config_path = other_args["known_lightcurver_config_path"] 
config_path = find_lsst_config(lsst_config_path=known_config_path)


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

    # This is a "series" because it is a Pandas.Series object
    working_series = targets.iloc[jj]

    target_string, ra, dec, n_sources = extract_ra_dec_target_string_sources(working_series)
    if target_string is None:
        print("Warning, no extractable string detected. This is required for labeling this object.")
        continue

    if verbose:
        print(f"working on object {target_string} at {ra}, {dec} with {n_sources} sources expected")

    # load or initialize the light curve 
    light_curve = load_light_curve(target_string)

    if other_args["redo_light_curve"]:
        time_start = float(other_args["time_start"])
    else:
        # otherwise, we are not reconstructing the light curve and should 
        # start where we left off
        if light_curve.data["time_last_updated"] is not None:
            time_start = float(light_curve.data["time_last_updated"])
        else:
            # lastly, initialize time start to MJD 40587 = Jan 1, 1970
            time_start = 40587
    
    time_stop = float(other_args["time_stop"])

    # if we are generating cutouts, this is per edge in pixels and always square
    cutout_size = int(other_args["cutout_size"]) 

    # this time interval is for Butler
    time_interval = [time_start, time_stop]

    for band in other_args["lsst_bands"]:
        # Get all frames within a given time interval from Butler
        # make this a list of references, then afterwards fetch fits files 
        # within the next loop. This way Lightcurver or any other method can 
        # focus on a single visit image to get the psf, do the processing, and 
        # most importantly clean up before the next object. 

        ### make temporary configuration file to place ROI at current target location 
        this_config_file, raw_dir = make_temp_yaml_with_new_roi(working_series, config_path, band)
        os.environ['LIGHTCURVER_CONFIG'] = this_config_file

        reference_list = query_coords(
            butler,
            band,
            ra,
            dec,
            raw_dir=raw_dir,
            time_start=time_interval[0],
            time_stop=time_interval[1],
            cutout_size=cutout_size,
            verbose=verbose
        )

        #==================
        # only can query images if they exist
        # chunk into a "process"
        if len(reference_list) > 0:
            for reference_id in reference_list:
                written_file = extract_image(
                    butler,
                    reference_id,
                    ra,
                    dec,
                    raw_dir=raw_dir,
                    cutout_size=cutout_size,
                    verbose=verbose
                )
                if verbose:
                    print(f"wrote file {written_file} containing the extracted image")

                if other_args["psf_method"] == "lightcurver":
                    from livelcs.Util.ExternalUtil.LightcurverUtil import run_lightcurver
                    run_lightcurver()

                elif other_args["method"] == "lsst_supersampled_psf":
                    # insert some code here from Shenming's notebook on 
                    # calculating supersampled PSF
                    # insert some code here to make a h5 file from this for starred
                    print("Sorry, not supported (yet)! We have plans to support this method relatively soon.")
                    exit()

                else:
                    print("please pass an argument for a valid PSF construction method \n These currently include 'lightcurver' and 'lsst_supersampled_psf'.")
                    exit()

                if verbose:
                    print("cleaning directories of temp images")
                
                clean_directory_structure_of_jpg_and_fits(
                    base_dir=other_args["base_working_directory"],
                    blacklist_dirs=other_args["blacklist_dirs"]
                )
                os.remove(this_config_file)
            #===============



            # only work with images if they exist
            #if len(reference_list) > 0:
            # at this point, we've removed all temp files and should be left with a database file and an h5 file stored 
            # in the path indicated by flag --base_working_directory
            path_to_h5_data, path_to_database = find_h5_and_database(
                other_args["base_working_directory"], 
                target_string,
                band
            )

            # extract required tables from database file
            zpt_table = extract_table_from_database(path_to_database, 'absolute_zeropoints')
            frames_table = extract_table_from_database(path_to_database, 'frames')

            # extract frames from tables
            extracted_frames_dict = extract_frames_from_h5_file(path_to_h5_data, frames_table, zpt_table)
            
            # This starts the Starred process, convert into a function once it's working
            starred_parameters = initialize_starred_variables(
                extracted_frames_dict
            )

            k_optim_init_positions = identify_point_sources(
                extracted_frames_dict,
                n_sources
            )

            opt_model, opt_kwargs, diagnostics = optimize_starred_fit(
                 extracted_frames_dict,
                 k_optim_init_positions
            )

            magnitude_dataframe = process_fluxes(
                opt_model,
                extracted_frames_dict,
                opt_kwargs
            )

            light_curve_data = convert_mags_dataframe_to_light_curve(
                magnitude_dataframe,
                opt_kwargs,
                band
            )

            light_curve_file_path = os.path.join(
                "./extracted_light_curves/",
                target_string,
                "_lc.json"
            )

            if not os.path.isfile(light_curve_file_path):
                this_light_curve = LightCurve()
                this_light_curve.save_light_curve(target_string)
            this_light_curve = load_light_curve(target_string)
            this_light_curve.update_light_curve(light_curve_data)
            this_light_curve.save_light_curve(target_string)

    
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













