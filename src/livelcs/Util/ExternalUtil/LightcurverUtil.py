'''These utilities connect Lightcurver to our pipeline'''

def check_current_config():
    '''This function checks that the environment variable is defined for Lightcurver
    output: dictionary representing the current configuration
    '''
    from yaml import safe_load
    import os 
    assert "LIGHTCURVER_CONFIG" in os.environ.keys(), "Lightcurver configuration not in current environment keys, please check!"
    with open(
        os.environ['LIGHTCURVER_CONFIG'],
        'r'
    ) as file:
        config = safe_load(file)
    return config

def find_paths_to_current_outputs():
    '''This function checks through the current configuration and returns a list of the directories where 
    files will be stored.
    output: list of strings representing directories
    '''
    configuration = get_lsst_config()
    all_written_directories = [
        configuration['workdir'],
        configuration['database_path'],
        configuration['plots_dir'],
        configuration['logs_dir'],
        configuration['frames_dir'],
        configuration['regions_path'],
        configuration['psfs_path'],
    ]
    return all_written_directories

def get_lsst_config():
    '''Connects the user's configuration to Lightcurver
    return: dict representing the configuration
    '''
    from lightcurver.structure.user_config import get_user_config
    configuration = get_user_config()
    return configuration

def initialize_lightcurver_database(database_path=None):
    '''Initialize the lightcurver database. Inputs are only for testing.
    param database_path: string representing a test pathway to a database file
    return: None
    '''
    from lightcurver.structure.database import initialize_database

    if database_path is not None:
        ## Short test if the provided database path is equal to the current configuration
        from os.path import abspath
        actual_path = get_lsst_config()['database_path']
        assert abspath(database_path) == abspath(actual_path), "provided database path is not the one being used."

    initialize_database()

def run_lightcurver_task_wrappers():
    '''Process the frames with lightcurver. Please request tests or adjustments
    return: None
    '''

    from lightcurver.pipeline.task_wrappers import (
        read_convert_skysub_character_catalog, 
        plate_solve_all_frames, 
        calc_common_and_total_footprint_and_save
    )

    read_convert_skysub_character_catalog()
    plate_solve_all_frames()
    calc_common_and_total_footprint_and_save()

def query_stars():
    '''Query the stars in Gaia catalog. Tests?
    return: None
    '''
    from lightcurver.processes.star_querying import query_gaia_stars

    query_gaia_stars()

def extract_stamps():
    '''Run the cutout making process. Tests?
    return: None
    '''
    from lightcurver.processes.cutout_making import extract_all_stamps

    extract_all_stamps()

def model_psfs(test=False):
    '''Run the PSF construction process of lightcurver. Tests?
    param test: bool to check that the saved location is the expected location
    return: None
    '''
    from lightcurver.processes.psf_modelling import model_all_psfs
    from os.path import join
    if test:
        configuration = get_lsst_config()
        save_location = join(configuration['workdir'], 'regions.h5')
        assert save_location == configuration['regions_path'], 'regions are not being saved in the expected location'

    model_all_psfs()

def compute_stellar_photometry():
    '''run the do_star_photometry function in lightcurver. Tests?
    return: None
    '''
    from lightcurver.processes.star_photometry import do_star_photometry

    do_star_photometry()

def calculate_normalization_coefficient():
    '''run lightcurver function calculate_coefficient. Tests?
    return: None
    '''
    from lightcurver.processes.normalization_calculation import calculate_coefficient

    calculate_coefficient()

def calculate_zeropoint():
    '''Runs the lightcurver process used to compute the zeropoint. Tests?
    return: None
    '''
    from lightcurver.processes.absolute_zeropoint_calculation import calculate_zeropoints

    calculate_zeropoints()

def prepare_roi_data_file():
    '''Runs the lightcurver process to build the ROI file. Tests?
    return: None
    '''

    from lightcurver.processes.roi_file_preparation import prepare_roi_file

    prepare_roi_file()

def model_roi():
    '''Run the lightcurver process of modeling the region of interest. Tests?
    return: None
    '''
    from lightcurver.processes.roi_modelling import do_modelling_of_roi

    do_modelling_of_roi()




def run_lightcurver():
    '''This function runs the full lightcurver process
    return: None
    '''
    if __name__ == '__main__':
        get_lsst_config()
        initialize_lightcurver_database()
        run_lightcurver_task_wrappers()
        query_stars()
        extract_stamps()
        model_psfs()
        compute_stellar_photometry()
        calculate_normalization_coefficient()
        calculate_zeropoint()
        prepare_roi_data_file()
        model_roi()



