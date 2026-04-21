'''utility file'''



def parse_arguments(all_arguments=None):
    '''this function takes the list of arguments provided and generates a
    dictionaryfrom them if possible'''

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


def open_tap_service(
    home_directory='~',
    rsp_tap_token_filename='.rsp-tap.token',
):
    '''opens the RSP TAP service'''
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

    ### works on lsst cloud
    butler = Butler(configuration, collections=collections)
    assert butler is not None
    return butler


def query_coords(
    butler,
    band,
    ra,
    dec,
    time_start=40587,
    time_stop=None,
    cutout_size=500,
    verbose=False
):
    '''checks a given set of coordinates if there is a new visit image'''
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

    assert type(bands) is str

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

        for reference in dataset_references:
            visit_image = butler.get(reference)

            # this check needs astropy units
            if visit_image.containsSkyCoords(
                ra * u.deg,
                dec * u.deg,
            ):
                this_image = visit_image.getCutout(
                    center = point,
                    size = extent
                )
                output_cutouts.append(this_image)
        
    except:
        # this catches the failures when no images overlap with the
        # chosen coordinates
        if verbose:
            print("no visit images found matching given times and coordinates")

    return output_cutouts
        

def processed_stellar_cutouts():
    # use Lightcurver or other method
    pass







def send_alert():
    # send out alerts as defined
    pass

def update_web_page():
    # update the monitoring page
    pass












