'''utility file'''



def parse_arguments(all_arguments=None):
    '''this function takes the list of arguments provided and generates a
    dictionary from them if possible'''

    if all_arguments == []:
        return None, []

    list_of_targets = all_arguments.pop(0)
    if len(list_of_targets) > 0:    
        other_args = all_arguments
    else:
        other_args = None
        
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
    cutout_size=1500,
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
    elif type(time_stop) is int:
        if verbose:
            print("Assuming stop time is in MJD")
        time_stop = astro_time(time_stop, format="mjd", scale="tai")
    if type(time_start) is int:
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
    
    # store cutouts in a list
    output_cutouts = []

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

            print(raw_dir+"/LSST"+str(visit_id)+".fits")
            print(path.isfile(raw_dir+"/LSST"+str(visit_id)+".fits"))

            if verbose:
                print(f"current id = {visit_id}")

            # only query if it's not in your raw directory
            if not path.isfile(raw_dir+"/LSST"+str(visit_id)+".fits"):
                file_to_write = raw_dir+"/LSST"+str(visit_id)+".fits"

                visit_image = butler.get(reference)
                cutout = visit_image.getCutout(center=center_point, size=extent)

                if cutout.containsSkyCoords(
                    ra * u.deg,
                    dec * u.deg,
                ):

                    cutout.writeFits(file_to_write)

                    image_metadata = visit_image.getMetadata()

                    my_data, my_header = fits.getdata(file_to_write, header=True)


                    # Lightcurver needs some additional header info
                    #my_header['PC1_1'] = my_header['CD1_1']
                    #my_header['PC1_2'] = my_header['CD1_2']
                    #my_header['PC2_1'] = my_header['CD2_1']
                    #my_header['PC2_2'] = my_header['CD2_2']
                    my_header['OBSTART'] = image_metadata['DATE-BEG']
                    my_header['EXPTIME'] = image_metadata['SHUTTIME']
                    my_header['GAIN'] = image_metadata['CCDGAIN']
                    fits.writeto(file_to_write, my_data, my_header, overwrite=True)
                    

        
    except Exception as expt:
        # this catches the failures when no images overlap with the
        # chosen coordinates
        print(expt)
        if verbose:
            print("no visit images found matching given times and coordinates")

    return output_cutouts


def make_temp_yaml_with_new_roi(targets, original_path, extension="_tmp"):
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
                for target in targets:
                    new_text += f'  {target["name"]}:\n'
                    new_text += f'    coordinates: [{target["ra"]}, {target["dec"]}]\n'

    new_config_file = original_path[:-5]+extension+original_path[-5:]

    with open(new_config_file, 'w') as file:
        file.write(new_text)

    return new_config_file, raw_dir

        

def processed_stellar_cutouts():
    # use Lightcurver or other method
    pass







def send_alert():
    # send out alerts as defined
    pass

def update_web_page():
    # update the monitoring page
    pass












