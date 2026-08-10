'''utility file'''

def parse_arguments(all_arguments=None):
    '''this function takes the list of arguments provided in the command line and generates a
    dictionary from them if possible. 
    targets: a json or csv containing the list of all relevant targets to be used to generate a pd.DataFrame object
    --verbose: Add to provide additional verbose information
    --time_start: time in MJD to query Butler. Must be greater than 40587 (Jan 1, 1970)
    --time_stop: time in MJD to query Butler. Must be greater than 40587
    --cutout_size: pixel size of the cutouts to produce
    --lsst_bands: series of bands to use
    --time_interval: number of days to query Butler between time_start and time_stop. Larger value means fewer queries.
    --butler_config: string defining butler configuration
    --butler_collections: strong defining which collections to query
    --redo_light_curve: Bool to reconstruct light curves. Will overwrite lightcurve data!
    --psf_method: "lightcurver" or "supersampled", defines the method of computing PSF
    return: list of dictionaries for each target, dictionary containing configuration from command line arguments
    '''
    import argparse
    import pandas as pd

    if all_arguments == []:
        return None, []

    all_args = argparse.ArgumentParser(
        description="This script takes a list of objects to monitor and queries the LSST data for new visit images containing those objects. It then processes the images and updates the light curves for those objects."
    )
    all_args.add_argument("--targets", default=None, help="Path to the file containing the list of targets to monitor")
    all_args.add_argument("--verbose", default=False, help="Print extra output")
    all_args.add_argument("--time_start", default=float(40587), help="Start time in MJD for querying Butler, any known light curves will default to their latest time")
    all_args.add_argument("--time_stop", default=None, help="Stop time in MJD for querying Butler, will default to current date if not provided")
    all_args.add_argument("--cutout_size", default=100, help="Size of cutouts in pixels")
    all_args.add_argument("--lsst_bands", default=list("ugrizy"), help="LSST bands to query")
    all_args.add_argument("--butler_config", default="dp1", help="Butler configuration to use")
    all_args.add_argument("--butler_collections", default="LSSTComCam/DP1", help="Butler collections to use")
    all_args.add_argument("--redo_light_curve", default=False, help="flag to recalculate full light curve instead of appending")
    all_args.add_argument("--known_lightcurver_config_path", default=None, help="path to the template lightcurver configuration path")
    all_args.add_argument("--base_working_directory", default='./LSST_data', help="path to directory where Lightcurver works in")
    all_args.add_argument("--blacklist_dirs", default=[], nargs="+", help="list of directories to not clean")
    all_args.add_argument("--psf_method", default="lightcurver", help="define which method to compute the PSF with")

    if all_arguments is None:
        print("please provide a list or json of targets to monitor")
        print("include the path to target coordinates as a json or csv file")
        print("these can be generated using the 'SLED_lenses.py' script provided")
        return None, {}

    my_args = all_args.parse_args(all_arguments)
    arg_dict = vars(my_args)

    if type(arg_dict["lsst_bands"]) is str:
        arg_dict["lsst_bands"] = list(arg_dict["lsst_bands"])
    
    if type(arg_dict["verbose"]) is str and arg_dict["verbose"] is not "False":
        arg_dict["verbose"] = True

    if arg_dict["targets"][-4:] == 'json':
        current_targets = pd.read_json(arg_dict["targets"])

    elif arg_dict["targets"][-3:] == 'csv':
        current_targets = pd.read_csv(arg_dict["targets"])

    elif arg_dict["targets"][-3:] == 'pkl':
        current_targets = pd.read_pickle(arg_dict["targets"])

    else:
        print(arg_dict)
        print("list of objects not recognized. please provide a valid json or csv file.")
        print("these can be generated using the 'SLED_lenses.py' script provided")
        return arg_dict["targets"], arg_dict
    return current_targets, arg_dict

def find_lsst_config(lsst_config_path=None):
    '''tests a few likely paths for the LSST configuration file
    lsst_config_path: path to search for the template LSST configuration file for Lightcurver
    return discovered configuration path
    '''
    from os import path
    if lsst_config_path is not None:
        if path.isfile(lsst_config_path):
            return lsst_config_path
    test_path = path.expanduser(
            "~/live_light_curves/config_LSST.yaml"
        )
    if path.isfile(test_path):
        config_path = test_path
    else:
        test_paths = [
            "./config_LSST.yaml",
            "../config_LSST.yaml",
            "../../config_LSST.yaml",
            "../../../config_LSST.yaml",
        ]
        for test_path in test_paths:
            if path.isfile(test_path):
                config_path = path.abspath(test_path)
                break
    if config_path:
        return config_path
    else: #pragma: no cover 
        # do not cover because we don't want to delete file for testing
        print("Error finding LSST configuration file.")
        return None


def prepare_butler(
    configuration='dp1',
    collections='LSSTComCam/DP1'
):
    '''prepare the lsst Butler required to get image data
    configuration: Butler configuration string
    collections: Butler collections string
    return: Butler class object
    '''
    from lsst.daf.butler import Butler
    try:
        butler = Butler(configuration, collections=collections)
    except:
        print("Error generating your butler. Please try adding your ACCESS_TOKEN to your environment")
    assert butler is not None
    return butler


def query_coords(
    butler,
    band,
    ra,
    dec,
    raw_dir=None,
    time_start=40587,
    time_stop=None,
    cutout_size=100,
    verbose=False
):
    '''checks a given set of coordinates if there is a new visit image
    butler: Butler class object used to query LSST images
    band: LSST band to query
    ra: right ascension in deg to query Butler at
    dec: declination in deg to query Butler at
    raw_dir: directory to write the raw files in
    time_start: date in MJD to start querying 
    time_end: date in MJD to end querying
    cutout_size: pixel size of the output
    verbose: Bool to print information about the querying process
    return: set of Butler dataset references
    '''
    from astropy.time import Time as astro_time
    from lsst.daf.butler import Timespan
    from os import path
    import astropy.units as u
    from numpy import asarray, float64

    # typecast the input time strings into numbers
    if type(time_stop) is str:
        time_stop = float(time_stop)
    if type(time_start) is str:
        time_start = float(time_start)

    if time_stop is None:
        time_stop = astro_time.now()
    elif type(time_stop) in [int, float, float64]:
        if verbose:
            print("Assuming stop time is in MJD")
        time_stop = astro_time(time_stop, format="mjd", scale="tai")
    if type(time_start) in [int, float, float64]:
        if verbose:
            print("Assuming start time is in MJD")
        time_start = astro_time(time_start, format="mjd", scale="tai")

    # this is the time window to query in
    timespan = Timespan(time_start, time_stop)

    assert type(band) is str
    raw_dir = path.abspath(raw_dir)

    # typecast values read from json or csv 
    if type(ra) is str: ra = float(ra)
    if type(dec) is str: dec = float(dec)

    # check provided bands are LSST bands. Update this in the future for flexibility to other surveys.
    if band not in list("ugrizy"):
        print("only lsst bands labeled 'u', 'g', 'r', 'i', 'z', 'y' are accepted at this time")
        return None

    # main query
    query = "band.name = :band AND " \
            "visit_detector_region.region OVERLAPS POINT(:ra, :dec) AND " \
            "visit.timespan OVERLAPS :timespan"
    bind_params = {
        "band": band,
        "ra": ra,
        "dec": dec,
        "timespan": timespan
    }

    # adjust query to only return the list of references
    # make a new functino to actually get the fits files for a single ref so 
    # we can deleete the excess files and not have such a large memory overhead
    if verbose:
        print("querying with parameters:", bind_params)
    try:
        # this returns a list of all IDs associated with the query
        dataset_references = butler.query_datasets(
            "visit_image",
            where=query,
            bind=bind_params
        )
        if verbose:
            print(f"{len(dataset_references)} images found")
        return dataset_references
    except Exception as expt:
        # this catches the failures when no images overlap with the chosen coordinates for a given time
        if verbose:
            print(expt)
            print("no visit images found matching given times and coordinates")
        return []


def extract_image(
    butler,
    reference_id,
    ra, 
    dec,
    raw_dir=None,
    cutout_size=100,
    verbose=False
):
    '''This takes in a single dataset reference and extracts the visit image
    butler: Butler class object used to query LSST images
    reference_id: int or str with the visit image identifier
    ra: float representing right ascension
    dec: float representing declination
    raw_dir: directory to write the temporary files in
    cutout_size: n/a, but if used an int representing the cutout size to save
    verbose: flag to give the user more information
    '''
    from astropy.io import fits
    import lsst.geom as geom
    from os import path
    # for reference in dataset_references: # loop in the live_light_curves pipeline
            
    visit_id = reference_id.dataId.get('visit')
    # print visit ids if verbose
    if verbose: 
        print(f"current id = {visit_id}")

    file_to_write = path.normpath(
        raw_dir+"/LSST"+str(visit_id)+".fits"
    )

    # This is required for cutout generation (not implimented at this point)
    center_point = geom.SpherePoint(
        ra * geom.degrees,
        dec * geom.degrees
    )
    extent = geom.Extent2I()
    extent.setX(cutout_size)
    extent.setY(cutout_size)

    # only query if it's not in your raw directory
    if not path.isfile(file_to_write):
        visit_image = butler.get(reference_id)
        # If we want to add cutout capability, add cutout generation here

        # Write the visit image to a fits file for processing
        visit_image.writeFits(file_to_write)
        # collect additional metadata
        image_metadata = visit_image.getMetadata()
        # add metadata required for Lightcurver as keywords
        my_data, my_header = fits.getdata(file_to_write, header=True)
        my_header = adjust_header(my_header, image_metadata)
        # rewrite the file with extra metadata
        fits.writeto(file_to_write, my_data, my_header, overwrite=True)
    else:
        if verbose:
            print("Fits file already saved, keep in mind these files are large!")

    return file_to_write

def extract_ra_dec_target_string(input_series):
    """Take an input pandas series that has columns 'name', 'ra', 'dec' and return extracted values
    input_series: pd.Series object 
    return: tuple with types 
        (
            str: name,
            float: ra,
            float: dec
        )
    """
    import pandas as pd

    if type(input_series) is pd.Series:
        print("gets to pd series check")
        try:
            ra = float(input_series["ra"])
            dec = float(input_series["dec"])
            target_string = str(input_series["name"])
            return target_string, ra, dec
        except:
            print(input_series)
            print("input dataframe must have 'name', 'ra', and 'dec'")
            return None, None, None
    elif type(input_series) is pd.DataFrame:

        try:
            ra = float(input_series["ra"].values[0])
            dec = float(input_series["dec"].values[0])
            target_string = str(input_series["name"].values[0])
            return target_string, ra, dec
        except:
            print(input_series)
            print("input dataframe must have 'name', 'ra', and 'dec'")
            return None, None, None

def make_temp_yaml_with_new_roi(target, original_path, band, extension="_tmp"):
    """Lightcurver requires a configuration file with the region of interest
    input as the parameter ROI for each object
    target: pd.DataFrame contianing information about the targeted object. Must contain "name", "ra", "dec" keys.
    original_path: path to the template LSST config file
    extension: additional extension to add to the file name
    return: newly generated temporary configuartion file name, directory for the raw files
    """
    import os
    import pandas as pd

    if type(target) is pd.DataFrame:
        target_string, ra, dec = extract_ra_dec_target_string(target.iloc[0])
    elif type(target) is pd.Series:
        target_string, ra, dec = extract_ra_dec_target_string(target)
    else:
        print("input target must be a pd.DataFrame or pd.Series")

    new_text = ''
    toggle_path_to_raw_data = False
    with open(original_path, 'r') as file:        
        current_line = None
        while current_line is not '':
            current_line = file.readline()
            if current_line.startswith('raw_dirs:'):
                raw_dir_str = current_line.split(sep=':')
                raw_dir = raw_dir_str[1].strip()+f'{band}/'
            if current_line == 'photometric_band:\n':
                if band in ['u', 'g']: approx_band = "g_sdss"
                elif band == ['r']: approx_band = "r_sdss"
                else: approx_band = "i_sdss"
                current_line = current_line[:-2]+approx_band+"\n"
            new_text += current_line
            if current_line == 'ROI:\n':
                new_text += f'  {target_string}:\n'
                new_text += f'    coordinates: [{ra}, {dec}]\n'
            if current_line == 'roi_name:\n':
                new_text += f'  {target_string}_{band}:\n'
            
            # not 100% sure if I need this, but other yaml files have similar lines
            # probably can remove this, since ROI is modelled in Starred
            if current_line == "point_sources: #  'label: [ra, dec]'\n":
                new_text += f'  A: [{ra}, {dec}]\n'

    tmp_yaml_path = os.path.dirname(original_path)+"/tmp_configs/"
    if os.path.isdir(tmp_yaml_path) is False:
        os.mkdir(tmp_yaml_path)

    tmp_config_file_name = tmp_yaml_path+original_path.split("/")[-1][:-5]+f"_{band}_"+target_string+extension+".yaml"

    with open(tmp_config_file_name, 'w') as file:
        file.write(new_text)

    return tmp_config_file_name, raw_dir


def adjust_header(my_header, image_metadata):
    '''This adds a few pieces of metadata to the header
    my_header: FITS header object to adjust for Lightcurver
    image_metadata: metadata from an LSST image_exposure object using it's method image_exposure.getMetadata()
    return: updated header with 'OBSTART', 'EXPTIME', 'GAIN' key value pairs
    '''
    my_header['OBSTART'] = image_metadata['DATE-BEG']
    my_header['EXPTIME'] = image_metadata['SHUTTIME']
    my_header['GAIN'] = image_metadata['CCDGAIN']
    return my_header


def clean_directory_structure_for_lightcurver(base_dir="./", blacklist_dirs=[]):
    '''This cleans the directory structure that lightcurver filled with fits files
    base_dir: uppermost directory to clean of all files with .fits and .jpg extensions
    blacklist_dirs: list of directories to ignore in the cleaning process
    return: None
    '''
    import os
    for dirpath, _, filenames in os.walk(base_dir):
        for filename in filenames:
            total_file_path = os.path.abspath(os.path.join(dirpath, filename))
            if filename.endswith(".jpg") or filename.endswith(".fits"):
                flag_for_deletion = True
                for directory in blacklist_dirs:
                    full_blacklisted_path = os.path.abspath(directory)
                    if os.path.commonpath(
                        [total_file_path, full_blacklisted_path]
                    ) == full_blacklisted_path:
                        flag_for_deletion = False
                        continue
                if flag_for_deletion:
                    os.remove(os.path.join(dirpath, filename))
    return None


def check_new_light_curve_data(new_data):
    '''check that the new data is in the correct format for the light curve object
    new_data: dictionary of data to append a lightcurve object
    return: set object containing no duplicates for the bands to query
    '''
    assert type(new_data) is dict, "new data must be a dictionary"
    new_data_images = set([key for key in new_data.keys()])
    for image in new_data_images:
        new_data_bands = set([key.split("_")[0] for key in new_data[image].keys()])
        for band in new_data_bands:
            if band+"_time" not in new_data[image] or band+"_mag" not in new_data[image] or band+"_mag_err" not in new_data[image]:
                raise ValueError(f"new data for band {band} must include time, mag, and mag_err")
    return new_data_bands
        

def load_light_curve(file_name, directory="./extracted_light_curves/", extension="_lc.json"):
    '''load the json light curve from a file
    file_name: string representing the path of the file to load
    directory: string representing the directory containing the file to load
    extension: extension of the lightcurve object, default is .lc
    return: lightcurve object
    '''
    import json
    from livelcs.Classes.light_curve import LightCurve
    import os
    if os.path.isdir(directory) is False:
        os.mkdir(directory)
    if os.path.isfile(os.path.join(directory+file_name)+extension) is False:
        blank_light_curve = LightCurve()
        blank_light_curve.save_light_curve(os.path.join(directory+file_name), extension=extension)
    with open(os.path.join(directory,file_name)+extension, 'r') as f:
        loaded_light_curve_data = json.load(f)
        loaded_light_curve = LightCurve(data=loaded_light_curve_data)
    assert type(loaded_light_curve) == LightCurve
    if "time_last_updated" not in loaded_light_curve.data:
        loaded_light_curve["time_last_updated"] = None
    return loaded_light_curve


def extract_table_from_database(path_to_database, table_to_extract):
    '''This function queries the database file for a specific table to extract
    param path_to_database: string representing the path to a sqlite3 database
    param table_to_extract: string representing the name of the table to extract
    return: Pandas table with the requested label
    '''
    from sqlite3 import connect
    from pandas import read_sql_query

    query = f"SELECT * FROM {table_to_extract}"
    with connect(path_to_database) as database:
        extracted_table = read_sql_query(query, database)
    return extracted_table


def send_alert():
    # send out alerts as defined
    pass

def update_web_page():
    # update the monitoring page
    pass












