'''This contains utilities designed to manipulate, add, and delete file objects'''


def find_lsst_config(target_string="config_LSST.yaml", lsst_config_path=None):
    '''tests a few likely paths for the chosen file (for config_LSST.yaml and parse_header.py)
    lsst_config_path: path to search for the template LSST configuration file for Lightcurver
    return discovered configuration path
    '''
    from os import path
    config_path = None
    if lsst_config_path is not None:
        if path.isfile(lsst_config_path):
            return lsst_config_path
    test_path = path.expanduser(
            f"~/live_light_curves/{target_string}"
        )
    if path.isfile(test_path):
        config_path = test_path
    else:
        test_paths = [
            f"./{target_string}",
            f"../{target_string}",
            f"../../{target_string}",
            f"../../../{target_string}",
        ]
        for test_path in test_paths:
            if path.isfile(test_path):
                config_path = path.abspath(test_path)
                break
    if config_path is not None:
        return config_path
    else: #pragma: no cover 
        # do not cover because we don't want to delete file for testing
        print(f"Error finding {target_string}")
        return None


def make_temp_yaml_with_new_roi(target, original_path, band, extension="_tmp"):
    """Lightcurver requires a configuration file with the region of interest
    input as the parameter ROI for each object
    target: pd.DataFrame contianing information about the targeted object. Must contain "name", "ra", "dec" keys.
    original_path: string representing the path to the template LSST config file
    band: string representing the band being used
    extension: string representing an additional extension to add to the file name
    return: newly generated temporary configuartion file name, directory for the raw files
    """
    import os
    import pandas as pd
    from shutil import copyfile
    from livelcs.Util.util import find_lsst_config
    from livelcs.Util.ExternalUtil.StandardUtil import extract_ra_dec_target_string_sources

    if type(target) is pd.DataFrame:
        target_string, ra, dec, _ = extract_ra_dec_target_string_sources(target.iloc[0])
    elif type(target) is pd.Series:
        target_string, ra, dec, _ = extract_ra_dec_target_string_sources(target)
    else:
        print("input target must be a pd.DataFrame or pd.Series")

    original_header_parser_path = find_lsst_config(
        target_string="LSST_data/reduced_data/header_parser/parse_header.py"
    )

    new_text = ''
    with open(original_path, 'r') as file:        
        current_line = None
        while current_line is not '':
            current_line = file.readline()
            # these checks adjust the current line
            if current_line.startswith('workdir:'):
                workdir_str = current_line.split(sep=':')
                if os.path.isdir(
                    os.path.normpath(
                        workdir_str[1].strip()+f'{target_string}/'
                    )
                ) is False:
                    os.mkdir(
                        os.path.normpath(
                            workdir_str[1].strip()+f'{target_string}/'
                        )
                    )
                workdir = os.path.normpath(
                    workdir_str[1].strip()+f'{target_string}/{band}/'
                )
                current_line = f'{workdir_str[0]}: {workdir} \n'
                if os.path.isdir(workdir) is False:
                    os.mkdir(workdir)
                if os.path.isdir(
                    os.path.normpath(
                        f'{workdir}/header_parser/'
                    )
                ) is False:
                    os.mkdir(
                        os.path.normpath(
                            f'{workdir}/header_parser/'
                        )
                    )
                copyfile(
                    original_header_parser_path, 
                    os.path.normpath(f'{workdir}/header_parser/parse_header.py')
                )
            if current_line.startswith('raw_dirs:'):
                raw_dir_str = current_line.split(sep=':')
                if os.path.isdir(
                    os.path.normpath(
                        raw_dir_str[1].strip()+f'{target_string}/'
                    )   
                ) is False:
                    os.mkdir(
                        os.path.normpath(
                            raw_dir_str[1].strip()+f'{target_string}/'
                        )
                    )
                raw_dir = os.path.normpath(
                    raw_dir_str[1].strip()+f'{target_string}/{band}/'
                )
                current_line = f'{raw_dir_str[0]}: {raw_dir} \n'
                if os.path.isdir(raw_dir) is False:
                    os.mkdir(raw_dir)
            if current_line.startswith('photometric_band:'):
                if band in ['u', 'g']: approx_band = "g_sdss"
                elif band == ['r']: approx_band = "r_sdss"
                else: approx_band = "i_sdss"
                split_line = current_line.split(sep=':')
                current_line = f'{split_line[0]}: {approx_band} \n'
            new_text += current_line
            # these checks add new lines
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


def clean_directory_structure_of_jpg_and_fits(base_dir="./", blacklist_dirs=[]):
    '''This cleans the directory structure that lightcurver filled with fits files.
    THIS WILL DELETE ALL .jpg AND .fits FILES RECURSIVELY IN THE BASE DIRECTORY.
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


def find_h5_and_database(
        base_working_directory,
        target_string, 
        band,
        override_h5_path=None, 
        override_database_path=None
    ):
    """This function returns the expected paths of the h5 and database files
    param target_string: str representing the object's name 
    param band: str representing which (LSST) band
    param override_h5_path: str to bypass this function for the h5 path
    param override_database_path: str to bypass this function for database path
    return: str representing the path of the h5 data, str representing the path of the database file
    """
    from os.path import join

    if override_h5_path is None:
        path_to_h5_data = join(
            base_working_directory, 
            'reduced_data',
            target_string, 
            band, 
            "regions.h5"
        )
    else:
        path_to_h5_data = override_h5_path

    if override_database_path is None:
        path_to_database = join(
            base_working_directory, 
            'reduced_data',
            target_string, 
            band, 
            "database.sqlite3"
        )
    else:
        path_to_database = override_database_path

    return path_to_h5_data, path_to_database



