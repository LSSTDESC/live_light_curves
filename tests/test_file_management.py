import livelcs.FileManagementUtil as FMU 
import livelcs.LiveLightCurvesUtil as LLCU

def test_find_lsst_config():
    import os.path
    found_path = FMU.find_lsst_config()
    assert os.path.isfile(found_path)
    new_found_path = FMU.find_lsst_config(
        "false_file_location"
    )
    another_found_path = FMU.find_lsst_config(
        "./config_LSST.yaml"
    )
    assert os.path.isfile(new_found_path)
    assert os.path.isfile(another_found_path)


def test_make_temp_yaml_with_new_roi():
    import os

    expected_target = "Test_coords"
    original_path = FMU.find_lsst_config()
    testing_extension = ".test_tmp"

    # load targets into a dataframe
    loaded_targets_from_csv, _ = FMU.parse_arguments(
        all_arguments=["--targets","./sample_csv_lenses.csv"]
    )

    print(expected_target)
    # create a pd.DataFrame with only one object
    target_of_interest = loaded_targets_from_csv.query("name == @expected_target")

    new_file_name, new_raw_dir = LLCU.make_temp_yaml_with_new_roi(
        target_of_interest,
        original_path,
        extension=testing_extension
    )

    # assure cleanup
    if os.path.isfile(new_file_name):
        os.remove(new_file_name)
    assert not os.path.isfile(new_file_name)
    if os.path.isdir(new_raw_dir):
        os.rmdir(new_raw_dir)
    assert not os.path.isdir(new_raw_dir)



def test_clean_directory_structure_of_jpg_and_fits():
    # to test this function, we will place 5 fits file and a jpg in various subdirectories
    import os

    # define some files in various directories
    empty_files_to_be_deleted = [
        "./this_is_a_dummy_file.fits",
        "./tests/another_dummy_file.fits",
        "./tests/TestPipeline/third_dummy_file.fits",
        "./tests/TestUtil/fourth_dummy_file.fits",
        "./tmp_configs/fifth_dummy_file.fits",
        "./tmp_configs/a_dummy_image.jpg"
    ]
    FMU.clean_directory_structure_of_jpg_and_fits()

    # assure the files don't already exist
    for file in empty_files_to_be_deleted:
        assert not os.path.isfile(file)
    
    # write the files
    for file in empty_files_to_be_deleted:
        with open(file, "x+") as f:
            f.write(file)
    
    # check that they were written
    for file in empty_files_to_be_deleted:
        assert os.path.isfile(file)
    
    # test cleanup process with blacklisting a subdirectory
    safe_subdirectories = ["./tmp_configs", "./tests"]
    FMU.clean_directory_structure_of_jpg_and_fits(base_dir="./", blacklist_dirs = safe_subdirectories)

    # check only our first file was deleted
    for jj, file in enumerate(empty_files_to_be_deleted):
        if jj == 0:
            assert not os.path.isfile(file)
        else:
            print(file)
            assert os.path.isfile(file)
    
    # rerun process with base directory of "./tests" and no blacklist
    FMU.clean_directory_structure_of_jpg_and_fits(base_dir="./tests/", blacklist_dirs=[])

    # check that files in "./tmp_configs/" are still untouched
    for jj, file in enumerate(empty_files_to_be_deleted):
        if jj < 4:
            assert not os.path.isfile(file)
        else:
            assert os.path.isfile(file)
    
    # rerun process to delete the remainder files (default config)
    FMU.clean_directory_structure_of_jpg_and_fits()

    for file in empty_files_to_be_deleted:
        assert not os.path.isfile(file)

def test_find_h5_and_database():
    # To test this function, we are expecting returned strings 
    # representing a very specific path. This is a requirement to 
    # make sure all objects and all bands have their data isolated 
    # for lightcurver and starred.
    from os.path import join
    my_base_working_directory = "./"
    my_targets = [
        'target_1',
        'g',
        'green'
    ]
    my_bands = [
        'y',
        'u'
    ]
    my_expected_locations = [
        "./reduced_data/target_1/y/",
        "./reduced_data/target_1/u/",
        './reduced_data/g/y/',
        './reduced_data/g/u/',
        './reduced_data/green/y/',
        './reduced_data/green/u/',
    ]
    for ii, band in enumerate(my_bands):
        for jj, target in enumerate(my_targets):
            path_h5, path_db = FMU.find_h5_and_database(
                my_base_working_directory,
                target,
                band
            )

            assert path_h5 == join(my_expected_locations[ii+jj+jj], 'regions.h5')
            assert path_db == join(my_expected_locations[ii+jj+jj], 'database.sqlite3')
                                    
    override_h5_path = "./../.././yellow/regions.h5"
    override_database_path = "../../storage/database.sqlite3"

    path_h5, path_db = FMU.find_h5_and_database(
        "./",
        target,
        band,
        override_h5_path=override_h5_path,
        override_database_path=override_database_path
    )
    assert path_h5 == override_h5_path
    assert path_db == override_database_path
    




