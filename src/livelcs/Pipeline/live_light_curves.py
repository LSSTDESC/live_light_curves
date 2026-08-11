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
    extract_table_from_database,
    extract_frames_from_h5_file
)


### External imports 
import numpy as np
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
    #time_endpoints = np.linspace(time_start, time_stop, int((time_stop-time_start)/time_interval))
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
            path_to_h5_data = os.path.join(
                other_args["base_working_directory"], 
                'reduced_data',
                target_string, 
                band, 
                "regions.h5"
            )
            path_to_database = os.path.join(
                other_args["base_working_directory"], 
                'reduced_data',
                target_string, 
                band, 
                "database.sqlite3"
            )
            
            zpt_table = extract_table_from_database(path_to_database, 'absolute_zeropoints')
            frames_table = extract_table_from_database(path_to_database, 'frames')

            data_roi, narrow_psfs, data_noisemap, times_mjd = extract_frames_from_h5_file(path_to_h5_data, frames_table)

            seeings = frames_table['seeing_arcseconds'].to_numpy()
            zeropoints = zpt_table['zeropoint'].to_numpy()


            # This starts the Starred process, convert into a function once it's working
            im_size = data_roi.shape[1]
            im_size_up = narrow_psfs.shape[1]
            epochs = data_roi.shape[0]

            sigma_sky_2 = np.asarray(
                [
                    np.std(data_roi[ii, int(0.9 * im_size):, int(0.9 * im_size):]) for ii in range(epochs)
                ]
            ) ** 2

            sigma_2 = np.asarray(
                [
                    sigma_sky_2[ii] + data_roi[ii].clip(min=0) for ii in range(epochs)
                ]
            )

            scale = np.max(data_roi)
            normalization = data_roi[0].max() / 100
            data_roi /= normalization
            sigma_2 /= normalization

            offset = (im_size-1)/2

            subsampling_factor = 2

            ## look at best frames
            best_percentile = np.percentile(seeings, 0)
            lower_threshold_percentile = np.percentile(seeings, 10)
            selected_indices = np.where((seeings >= best_percentile)*(seeings<lower_threshold_percentile))
            best_data = data_roi[selected_indices]
            best_noise = data_noisemap[selected_indices]
            best_narrow_psfs = narrow_psfs[selected_indices]

            # need to generalize to n point sources and connect to the csv/json input file
            point_sources = dict()
            n_point_sources = 1
            generic_labels = list('abcdefghi')
            generic_image_coordinate_guesses = [
                (0, 0),
                (0, 0+2),
                (0+2, 0),
                (0, 0-2),
                (0-2, 0),
                (0-2, 0+2),
                (0+2, 0-2),
                (0-2, 0-2),
                (0+2, 0+2),                                                           
            ]
            intensities_for_each_object = []
            for jj in range(n_point_sources):
                point_sources[generic_labels[jj]] = generic_image_coordinate_guesses[jj]
                intensities_for_each_object.append(10)

            initial_intensities = len(best_data) * intensities_for_each_object

            initial_x_values = np.array(
                [coords[0] for _, coords in point_sources.items()]
            )
            initial_y_values = np.array(
                [coords[1] for _, coords in point_sources.items()]
            )

            model, kwargs_init, kwargs_up, kwargs_down, kwargs_fixed = setup_model(
                best_data,
                best_noise**2,
                best_narrow_psfs,
                initial_x_values,
                initial_y_values,
                subsampling_factor,
                initial_intensities
            )

            # optimize translations

            kwargs_fixed = kwargs_init.copy()
            del kwargs_fixed['kwargs_analytic']['dx']
            del kwargs_fixed['kwargs_analytic']['dy']

            parameters = ParametersDeconv(
                kwargs_init=kwargs_init,
                kwargs_fixed=kwargs_fixed,
                kwargs_up=kwargs_up,
                kwargs_down=kwargs_down
            )

            loss = Loss(best_data, model, parameters, best_noise**2)
            optim = Optimizer(loss, parameters, method='l-bfgs-b')
            best_fit, logL_best_fit, extra_fields, runtime = optim.minimize(maxiter=200)
            kwargs_partial1 = parameters.best_fit_values(as_kwargs=True).copy()

            # optimize other parameters

            del kwargs_fixed['kwargs_background']['h']
            del kwargs_fixed['kwargs_background']['mean']
            del kwargs_fixed['kwargs_analytic']['a']
            del kwargs_fixed['kwargs_analytic']['c_x']
            del kwargs_fixed['kwargs_analytic']['c_y']

            W = propagate_noise(
                model, 
            )




            




    if verbose:
        print("removing tmp config file")
    os.remove(this_config_file)

    # at this point, we've removed all temp files and should be left with a database file and an h5 file stored 
    # in the path indicated by flag --base_working_directory





    
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













