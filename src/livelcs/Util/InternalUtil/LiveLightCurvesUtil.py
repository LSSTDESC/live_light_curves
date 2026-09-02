'''These utilities are unique to Live Light Curves'''


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
    all_args.add_argument("--time_stop", default=float(99999), help="Stop time in MJD for querying Butler, will default to current date if not provided")
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




def send_alert():
    # send out alerts as defined
    pass

def update_web_page():
    # update the monitoring page
    pass
