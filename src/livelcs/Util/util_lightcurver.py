'''These utilities connect live light curves to lightcurver'''



def run_lightcurver():

    import os
    import yaml
    from pathlib import Path

    print("process of running lightcurver")

    print(os.environ['LIGHTCURVER_CONFIG'])
    with open(
        os.environ['LIGHTCURVER_CONFIG'],
        'r'
    ) as file:
        config = yaml.safe_load(file)

    print(config['raw_dirs'])
    print(config['workdir'])
    print(Path(config['workdir']))


    ### lightcurver imports
    from lightcurver.structure.user_config import get_user_config
    from lightcurver.structure.database import initialize_database
    from lightcurver.pipeline.task_wrappers import (
        read_convert_skysub_character_catalog, 
        plate_solve_all_frames, 
        calc_common_and_total_footprint_and_save
    )
    from lightcurver.processes.star_querying import query_gaia_stars
    from lightcurver.processes.cutout_making import extract_all_stamps
    from lightcurver.processes.psf_modelling import model_all_psfs
    from lightcurver.processes.normalization_calculation import calculate_coefficient
    from lightcurver.processes.star_photometry import do_star_photometry
    from lightcurver.processes.absolute_zeropoint_calculation import calculate_zeropoints
    from lightcurver.processes.roi_file_preparation import prepare_roi_file
    from lightcurver.processes.roi_modelling import do_modelling_of_roi

    # lightcurver requires a main wrapper
    #if __name__ == '__main__':
    if True:
        the_config = get_user_config()
        print(the_config)
        initialize_database()
        read_convert_skysub_character_catalog()
        plate_solve_all_frames()
        calc_common_and_total_footprint_and_save()
        query_gaia_stars()
        extract_all_stamps()
        model_all_psfs()
        do_star_photometry()
        calculate_coefficient()
        calculate_zeropoints()
        prepare_roi_file()
        do_modelling_of_roi()













