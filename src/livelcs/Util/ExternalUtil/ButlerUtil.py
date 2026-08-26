'''This file contains utility functions which connect the Butler service to our pipeline'''

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
    from livelcs.Util.ExternalUtil.StandardUtil import adjust_fits_header
            
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
        my_header = adjust_fits_header(my_header, image_metadata)
        # rewrite the file with extra metadata
        fits.writeto(file_to_write, my_data, my_header, overwrite=True)
    else:
        if verbose:
            print("Fits file already saved, keep in mind these files are large!")

    return file_to_write




