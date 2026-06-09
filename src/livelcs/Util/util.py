'''utility file'''

def parse_arguments(all_arguments=None):
    '''this function takes the list of arguments provided and generates a
    dictionary from them if possible'''
    import argparse

    if all_arguments == []:
        return None, []

    all_args = argparse.ArgumentParser(
        description="This script takes a list of objects to monitor and queries the LSST data for new visit images containing those objects. It then processes the images and updates the light curves for those objects."
    )
    all_args.add_argument("targets", help="Path to the file containing the list of targets to monitor")
    all_args.add_argument("--other-args", nargs="*", help="Other arguments for the script")
    all_args.add_argument("--verbose", action="store_true", help="Print verbose output")

        
    if all_arguments is None:
        print("please provide a list or json of targets to monitor")
        print("include the path to target coordinates as a json or csv file")
        print("these can be generated using the 'SLED_lenses.py' script provided")

    elif list_of_targets[-4:] == 'json':
        import json
        with open(list_of_targets, 'r') as f:
            current_targets = json.load(f)

    elif list_of_targets[-3:] == 'csv':
        import csv
        current_targets = []
        with open(list_of_targets, 'r') as f:
            my_reader = csv.DictReader(f)
            for row in my_reader:
                current_targets.append(row)
    else:
        print("list of objects not recognized. please provide a valid json or csv.")
        print("these can be generated using the 'SLED_lenses.py' script provided")
        return list_of_targets, all_arguments
    return current_targets, other_args

def find_lsst_config(lsst_config_path=None):
    '''tests a few likely paths for the LSST configuration file'''
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
    else:
        print("Error finding LSST configuration file.")


def open_tap_service(
    home_directory='~',
    rsp_tap_token_filename='.rsp-tap.token',
):
    '''opens the RSP TAP service. REDUNDANT?'''
    import pyvo
    import os 
    RSP_TAP_SERVICE = 'https://data.lsst.cloud/api/tap'
    homedir = os.path.expanduser(home_directory)
    token_file = os.path.join(homedir, rsp_tap_token_filename)
    with open(token_file, 'r') as f:
        token_str = f.readline()
    cred = pyvo.auth.CredentialStore()
    cred.set_password("x-oauth-basic", token_str)
    credential = cred.get("ivo://ivoa.net/sso#BasicAA")
    rsp_tap = pyvo.dal.TAPService(RSP_TAP_SERVICE, session=credential)
    return rsp_tap


def prepare_butler(
    configuration='dp1',
    collections='LSSTComCam/DP1'
):
    '''prepare the lsst Butler required to get image data'''
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
    '''checks a given set of coordinates if there is a new visit image'''
    from astropy.time import Time as astro_time
    from astropy.io import fits
    from lsst.daf.butler import Timespan
    from os import path
    import lsst.geom as geom
    import astropy.units as u
    from numpy import asarray
    if time_stop is None:
        time_stop = astro_time.now()
    elif type(time_stop) is int or type(time_stop) is float:
        if verbose:
            print("Assuming stop time is in MJD")
        time_stop = astro_time(time_stop, format="mjd", scale="tai")
    if type(time_start) is int or type(time_start) is float:
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

    if band not in list("ugrizy"):
        print("only lsst bands of 'u', 'g', 'r', 'i', 'z', 'y' are accepted now")
        return None
    
    # These are required to make sure the coordinates are actually
    # in the visit image
    center_point = geom.SpherePoint(
        ra * geom.degrees,
        dec * geom.degrees
    )
    extent = geom.Extent2I()
    extent.setX(cutout_size)
    extent.setY(cutout_size)

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

        for reference in dataset_references:
            visit_id = reference.dataId.get('visit')
            
            if verbose: # to be kept
                print(f"current id = {visit_id}")

            # only query if it's not in your raw directory
            if not path.isfile(raw_dir+"/LSST"+str(visit_id)+".fits"):
                file_to_write = raw_dir+"/LSST"+str(visit_id)+".fits"

                visit_image = butler.get(reference)
                #cutout = visit_image.getCutout(center=center_point, size=extent)

                if visit_image.containsSkyCoords(
                    ra * u.deg,
                    dec * u.deg,
                ):

                    visit_image.writeFits(file_to_write)

                    image_metadata = visit_image.getMetadata()

                    my_data, my_header = fits.getdata(file_to_write, header=True)

                    # Lightcurver needs some additional header info for Astropy.WCS
                    my_header = check_header(my_header, image_metadata)
                    
                    fits.writeto(file_to_write, my_data, my_header, overwrite=True)
                
    except Exception as expt:
        # this catches the failures when no images overlap with the
        # chosen coordinates
        if verbose:
            print(expt)
            print("no visit images found matching given times and coordinates")

    #return output_cutouts
    return None


def make_temp_yaml_with_new_roi(target, original_path, extension="_tmp"):
    """Lightcurver requires a configuration file with the region of interest
    input as the parameter ROI for each object"""
    new_text = ''
    toggle_path_to_raw_data = False
    with open(original_path, 'r') as file:        
        current_line = None
        while current_line is not '':
            if current_line == 'raw_dirs:\n':
                toggle_path_to_raw_data=True
            current_line = file.readline()
            if toggle_path_to_raw_data is True:
                raw_dir = current_line[4:-1]
                toggle_path_to_raw_data=False
            new_text += current_line
            if current_line == 'ROI:\n':
                new_text += f'  {target["name"]}:\n'
                new_text += f'    coordinates: [{target["ra"]}, {target["dec"]}]\n'
            # Do we include some dummy n image positions to the yaml file for n image objects?
    new_config_file = original_path[:-5]+target+extension+original_path[-5:]

    with open(new_config_file, 'w') as file:
        file.write(new_text)

    return new_config_file, raw_dir


def check_header(my_header, image_metadata):
    # check that the header has the necessary information for lightcurver
    #my_header['PC1_1'] = my_header['CD1_1']
    #my_header['PC1_2'] = my_header['CD1_2']
    #my_header['PC2_1'] = my_header['CD2_1']
    #my_header['PC2_2'] = my_header['CD2_2']
    my_header['OBSTART'] = image_metadata['DATE-BEG']
    my_header['EXPTIME'] = image_metadata['SHUTTIME']
    my_header['GAIN'] = image_metadata['CCDGAIN']
    return my_header

def build_directory_structure_for_lightcurver(base_dir="./"):
    # this is the directory structure that lightcurver expects for its configuration file
    from lightcurver.structure.database import initialize_databse
    initialize_databse(db_path=base_dir)
    return None





def clean_directory_structure_for_lightcurver(base_dir="./"):
    # this cleans the directory structure that lightcurver 
    # filled with fits files
    import os
    for dirpath, dirnames, filenames in os.walk(base_dir):
        for filename in filenames:
            if filename.endswith(".jpg") or filename.endswith(".fits"):
                os.remove(os.path.join(dirpath, filename))
    return None


def check_new_light_curve_data(new_data):
    # check that the new data is in the correct format for lightcurver
    assert type(new_data) is dict, "new data must be a dictionary"
    new_data_bands = set([key.split("_")[0] for key in new_data.keys()])
    for band in new_data_bands:
        if band+"_time" not in new_data or band+"_mag" not in new_data or band+"_mag_err" not in new_data:
            raise ValueError(f"new data for band {band} must include time, mag, and mag_err")
    return new_data_bands
        

def load_light_curve(self, file_name, extension=".lc"):
        # load the light curve from a file
        import pickle
        from livelcs.Classes.light_curve import LightCurve
        with open(file_name, 'rb') as f:
            data_dict = pickle.load(f)
        assert type(data_dict) == dict
        if "time_last_updated" not in data_dict:
            data_dict["time_last_updated"] = None
            return None
        return LightCurve(**data_dict)




def processed_stellar_cutouts():
    # use Lightcurver or other method
    pass







def send_alert():
    # send out alerts as defined
    pass

def update_web_page():
    # update the monitoring page
    pass












