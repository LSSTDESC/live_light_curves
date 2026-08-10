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
    extract_table_from_database
)


### External imports 
from numpy import (
    linspace,
    max,
    nan_to_num,
    asarray,
    zeros, 
    std
)
from pandas import DataFrame
import tqdm
from h5py import File


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

    working_series = targets.iloc[jj]

    target_string, ra, dec = extract_ra_dec_target_string(working_series)
    if target_string is None:
        continue

    # this will be an input parameter
    lsst_bands = other_args["lsst_bands"]

    if verbose:
        print(target_string)

    light_curve = load_light_curve(target_string)

    if other_args["redo_light_curve"]:
        time_start = float(other_args["time_start"])
    else:
        if light_curve.data["time_last_updated"] is not None:
            time_start = float(light_curve.data["time_last_updated"])
        else:
            # initialize time start to MJD 40587 = Jan 1, 1970
            time_start = 40587

    time_stop = float(other_args["time_stop"])

    cutout_size = int(other_args["cutout_size"]) # per edge in pixels, always square

    ## not needed now that I will query all relevant times, then go visit image by visit image
    #time_interval = float(other_args["time_interval"]) # check in batches of time
    #time_endpoints = linspace(time_start, time_stop, int((time_stop-time_start)/time_interval))
    #time_intervals = [(time_endpoints[ii], time_endpoints[ii+1]) for ii in range(len(time_endpoints)-1)]

    time_interval = [time_start, time_stop]

    # do we need this list?
    # current_position = []


    for band in lsst_bands:
        # Get all frames within a given time interval from Butler
        # make this a list of references, then afterwards fetch fits files 
        # within the next loop. This way Lightcurver or any other method can 
        # focus on a single visit image to get the psf, do the processing, and 
        # most importantly clean up before the next object. 

        ### make temporary configuration file to place ROI at current objects 
        this_config_file, raw_dir = make_temp_yaml_with_new_roi(working_series, config_path, band)
        os.environ['LIGHTCURVER_CONFIG'] = this_config_file
        # include this yaml file in cleanup step, fast enough to make again and we don't want thousands of mostly identical files
        print(os.environ['LIGHTCURVER_CONFIG'], raw_dir)


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

        # only can query images if they exist
        if len(reference_list) > 0:
            for reference_id in reference_list:
                extract_image(
                    butler,
                    reference_id,
                    ra,
                    dec,
                    raw_dir=raw_dir,
                    cutout_size=cutout_size,
                    verbose=verbose
                )

                if other_args["psf_method"] == "lightcurver":
                    from livelcs.Util.util_lightcurver import run_lightcurver
                    run_lightcurver()
                    print("lightcurver ran!")
                    

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
                
                clean_directory_structure_for_lightcurver(
                    base_dir=other_args["base_working_directory"],
                    blacklist_dirs=other_args["blacklist_dirs"]
                )

        # only work with images if they exist
        if len(reference_list) > 0:
            # at this point, we've removed all temp files and should be left with a database file and an h5 file stored 
            # in the path indicated by flag --base_working_directory
            path_to_h5_data = os.path.join(other_args["base_working_directory"], "regions.h5")
            path_to_database = os.path.join(other_args["base_working_directory"], "database.sqlite3")

            print(path_to_database)
            print(path_to_h5_data)

            zpt_table = extract_table_from_database(path_to_database, 'absolute_zeropoints')
            frames_table = extract_table_from_database(path_to_database, 'frames')

            times = frames_table['mjd'].to_numpy()
            seeings = frames_table['seeing_arcseconds'].to_numpy()
            zeropoints = zpt_table['zeropoint'].to_numpy()

            narrow_psfs = []
            data_roi = []
            noisemaps = []
            # note: we have all times in "times", but some of these correspond to nan images
            mjds = [] 

            with File(path_to_h5_data, "r") as file:

                for index, frame in enumerate(file['frames']):
                    for key in file['frames'][frame].keys():
                        # psf key is labeled with a series of star names, and differs between frames
                        if key.startswith("psf"):
                            current_psf_key = key
                    frame_data = asarray(
                        file['frames'][frame]['data']['ROI']
                    )
                    if nan_to_num(
                        max(frame_data), 
                        nan=-9999. # this is just a code number
                    ) == -9999:
                        continue
                    frame_narrow_psf = asarray(
                        file['frames'][frame][current_psf_key]['narrow_psf']
                    )
                    frame_noisemap = asarray(
                        file['frames'][frame]['noisemap']['ROI']
                    )
                    mjds.append(times[index])
                    data_roi.append(frame_data)
                    narrow_psfs.append(frame_narrow_psf)
                    noisemaps.append(frame_noisemap)

            mjds = asarray(mjds)
            narrow_psfs = asarray(narrow_psfs)
            noisemaps = asarray(noisemaps)
            data_roi = asarray(data_roi)

            im_size = data_roi.shape[1]
            im_size_up = narrow_psfs.shape[1]
            epochs = data_roi.shape[0]

            #sigma_2 = zeros((epochs, im_size, im_size))
            sigma_sky_2 = asarray(
                [
                    std(data_roi[ii, int(0.9 * im_size):, int(0.9 * im_size):]) for ii in range(epochs)
                ]
            ) ** 2

            sigma_2 = asarray(
                [
                    sigma_sky_2[ii] + data_roi[ii].clip(min=0) for ii in range(epochs)
                ]
            )

            scale = max(data_roi)
            normalization = data_roi[0].max() / 100
            data_roi /= normalization
            sigma_2 /= normalization

            offset = (im_size-1)/2
                    

            ## TO GET PROPER FLUXES, I need:
            # zeropoints, mjds, and seeings


    if verbose:
        print("removing tmp config file")
    os.remove(this_config_file)

    # at this point, we've removed all temp files and should be left with a database file and an h5 file stored 
    # in the path indicated by flag --base_working_directory





    
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













