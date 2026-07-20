import livelcs.Util.util as util

def test_parse_arguments():
    import json
    import csv
    import os
    import pandas as pd
    from pandas.testing import assert_frame_equal

    expected_args = {
        "targets": "some_dummy_path",
        "verbose": True,
        "time_start": "55000",
        "time_stop": "56000",
        "cutout_size": "50",
        "lsst_bands": ["g"],
    }

    expected_keys = [
        'targets', 
        'verbose', 
        'time_start', 
        'time_stop', 
        'cutout_size', 
        'lsst_bands', 
        'butler_config', 
        'butler_collections', 
        'redo_light_curve', 
        'known_lightcurver_config_path', 
        'base_working_directory', 
        'blacklist_dirs'
    ]

    passed_args = [
        "--targets",
        "some_dummy_path", 
        "--verbose", 
        "True",
        "--time_start",
        "55000", 
        "--time_stop",
        "56000",
        "--cutout_size",
        "50",
        "--lsst_bands",
        "g"
    ]

    parsed_targets, parsed_args = util.parse_arguments(
        all_arguments=passed_args
    )
    assert parsed_targets == expected_args["targets"]

    for this_key in expected_args.keys():
        assert this_key in parsed_args.keys()
        assert parsed_args[this_key] == expected_args[this_key]

    no_targets, no_args = util.parse_arguments()
    assert no_targets is None
    assert type(no_args) is type({})

    blank_file = "./dummy_test.json"
    blank_json_data = {
        "blank_name": {
            "ra": 1,
            "dec": 3,
            "image_sep": 2
        },
        "second_object": {
            "ra": 10,
            "dec": -50,
            "image_sep": 0.03,
            "bogus_column": "yellow"
        }
    }
    json_data_as_dataframe = pd.DataFrame(blank_json_data)
    passed_args = [
        "--targets",
        blank_file, 
        "--verbose", 
        "True",
    ]

    # Test loading from a json file
    with open(blank_file, "w") as file:
        json.dump(blank_json_data, file)
    loaded_empty_targets_from_json, other_args = util.parse_arguments(
        all_arguments=passed_args
    )
    assert_frame_equal(loaded_empty_targets_from_json, json_data_as_dataframe)
    for this_key in expected_keys:
        assert this_key in other_args.keys()
    assert other_args["verbose"] == True
    if os.path.isfile(blank_file):
        os.remove(blank_file)
        
    # Test loading from a csv file
    blank_file = "./dummy_test.csv"
    passed_args = [
        "--targets",
        blank_file, 
        "--verbose", 
        "False"
    ]
    blank_csv_data = [
        ["name", "ra", "dec", "bogus_column"],
        ["blank_name", 1, 2, " "],
        ["second_object", 10, -30, "yellow"]
    ]
    with open(blank_file, "w", newline='') as file:
        csvwriter = csv.writer(file, delimiter=',')
        csvwriter.writerows(blank_csv_data)
    my_loaded_csv = pd.read_csv(blank_file)
    loaded_empty_targets_from_csv, other_args = util.parse_arguments(
        all_arguments=passed_args
    )
    assert_frame_equal(loaded_empty_targets_from_csv, my_loaded_csv)
    for this_key in expected_keys:
        assert this_key in other_args.keys()

    passed_args.append("--blacklist_dirs")
    passed_args.append("test_dir_number_1")
    passed_args.append("test_dir_number_2")
    passed_args.append("test_dir_number_3")
    passed_args.append("--psf_method")
    passed_args.append("supersampled")

    _, extracted_args = util.parse_arguments(all_arguments=passed_args)
    assert type(extracted_args["blacklist_dirs"]) is list
    assert len(extracted_args["blacklist_dirs"]) == 3
    assert "psf_method" in extracted_args.keys()
    assert extracted_args["psf_method"] is "supersampled"

    if os.path.isfile(blank_file):
        os.remove(blank_file)


def test_find_lsst_config():
    import os.path
    found_path = util.find_lsst_config()
    assert os.path.isfile(found_path)
    new_found_path = util.find_lsst_config(
        "false_file_location"
    )
    another_found_path = util.find_lsst_config(
        "./config_LSST.yaml"
    )
    assert os.path.isfile(new_found_path)
    assert os.path.isfile(another_found_path)

def test_prepare_butler():
    # Not sure how to test this one without giving data access
    assert 1

def test_query_coords():
    # also not sure how to test without giving data access
    assert 1

def test_extract_image():
    # again not sure how to test without constructing a valid butler object with data access
    assert 1

def test_extract_ra_dec_target_string():
    import pandas as pd
    blank_csv_data = [
        ["blank_name", int(1), float(2.5), " "],
        ["second_object", 10.00000, -30., "yellow"]
    ]
    my_dataframe = pd.DataFrame(blank_csv_data, columns=["name", "ra", "dec", "bogus_column"])
    first_expected_target = "blank_name"
    my_selected_object = my_dataframe.query("name == @first_expected_target")
    extracted_name_as_string, extracted_ra, extracted_dec = util.extract_ra_dec_target_string(my_selected_object)
    assert extracted_name_as_string == first_expected_target
    assert type(extracted_name_as_string) == str
    assert type(extracted_ra) == float
    assert type(extracted_dec) == float

    second_expected_target = "second_object"
    my_selected_object = my_dataframe.query("name == @second_expected_target")
    extracted_name_as_string, extracted_ra, extracted_dec = util.extract_ra_dec_target_string(my_selected_object)
    assert extracted_name_as_string == second_expected_target
    assert type(extracted_name_as_string) == str
    assert type(extracted_ra) == float
    assert type(extracted_dec) == float

    path_to_sample_csv_file = "./sample_csv_lenses.csv"
    my_loaded_dataframe = pd.read_csv(path_to_sample_csv_file)
    test_target = "HE0047-1756"
    my_selected_object = my_loaded_dataframe.query("name == @test_target")
    extracted_name_as_string, extracted_ra, extracted_dec = util.extract_ra_dec_target_string(my_selected_object)
    assert extracted_name_as_string == test_target
    assert type(extracted_name_as_string) == str
    assert type(extracted_ra) == float
    assert type(extracted_dec) == float

    test_target_coords = "Test_coords"
    my_selected_object = my_loaded_dataframe.query("name == @test_target_coords")
    extracted_name_as_string, extracted_ra, extracted_dec = util.extract_ra_dec_target_string(my_selected_object)
    assert extracted_name_as_string == test_target_coords
    assert type(extracted_name_as_string) == str
    assert type(extracted_ra) == float
    assert type(extracted_dec) == float

def test_make_temp_yaml_with_new_roi():
    import os

    expected_target = "Test_coords"
    original_path = util.find_lsst_config()
    testing_extension = ".test_tmp"

    # load targets into a dataframe
    loaded_targets_from_csv, _ = util.parse_arguments(
        all_arguments=["--targets","./sample_csv_lenses.csv"]
    )

    print(expected_target)
    # create a pd.DataFrame with only one object
    target_of_interest = loaded_targets_from_csv.query("name == @expected_target")

    new_file_name, new_raw_dir = util.make_temp_yaml_with_new_roi(
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

def test_adjust_header():
    from astropy.io import fits
    from astropy.wcs import WCS
    import matplotlib.pyplot as plt
    # note this sterile fits file has been scrubbed of image data. 
    # the fits header was kept with original values
    sterile_fits_file_path = "./tests/TestUtil/sample_cleaned_fits_file.fitz"
    with fits.open(sterile_fits_file_path) as hdul:
        data = hdul[0].data
        header = hdul[0].header
    
    expected_header_cards = ['OBSTART', 'EXPTIME', 'GAIN']
    
    # These are non-typical header cards for the LSST pipeline output that are 
    # required for Lightcurver, but provided in the visit image metadata
    for item in expected_header_cards:
        assert item not in header.keys()
    
    # I will only provide the minimum metadata required for this pipeline. 
    # The actual metadata is a much larger dictionary and these are only 
    # representative values, not true values from Rubin.
    required_metadata = {
        'DATE-BEG': "2000-01-01T00:30:00.000",
        'SHUTTIME': "30",
        'CCDGAIN': "1"
    }

    adjusted_header = util.adjust_header(header, required_metadata)
    # check that OBSTART, EXPTIME, GAIN are now in the header cards
    for item in expected_header_cards:
        assert item in header.keys()

    # test initialization of WCS with the adjusted header
    my_wcs = WCS(adjusted_header)
    # test we can generate world coordinates from the header
    wcs_coords = my_wcs.all_pix2world(adjusted_header["naxis1"], adjusted_header["naxis2"], 1)
    # test that we could generate the WCS overlay in a pyplot figure
    fig = plt.figure()
    ax = plt.subplot(projection=my_wcs)
    ax.get_coords_overlay("icrs")
    ax.imshow(data)

def test_clean_directory_structure_for_lightcurver():
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
    util.clean_directory_structure_for_lightcurver()

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
    util.clean_directory_structure_for_lightcurver(base_dir="./", blacklist_dirs = safe_subdirectories)

    # check only our first file was deleted
    for jj, file in enumerate(empty_files_to_be_deleted):
        if jj == 0:
            assert not os.path.isfile(file)
        else:
            print(file)
            assert os.path.isfile(file)
    
    # rerun process with base directory of "./tests" and no blacklist
    util.clean_directory_structure_for_lightcurver(base_dir="./tests/", blacklist_dirs=[])

    # check that files in "./tmp_configs/" are still untouched
    for jj, file in enumerate(empty_files_to_be_deleted):
        if jj < 4:
            assert not os.path.isfile(file)
        else:
            assert os.path.isfile(file)
    
    # rerun process to delete the remainder files (default config)
    util.clean_directory_structure_for_lightcurver()

    for file in empty_files_to_be_deleted:
        assert not os.path.isfile(file)
     
def test_check_new_light_curve_data():
    import pytest 
    new_data = {
        "image_1": {
            "g_time": [50300, 50350, 50420],
            "g_mag": [19.3, 17.3, 18.9],
            "g_mag_err": [0.5, 1.0, 0.5], 
            "z_time": [50001, 50110, 50200],
            "z_mag": [20.5, 20.8, 20.3],
            "z_mag_err": [0.3, 0.1, 0.2]
        },
        "image_2": {
            "g_time": [50300, 50350, 50420],
            "g_mag": [19.4, 17.9, 18.2],
            "g_mag_err": [0.5, 1.0, 0.5], 
            "z_time": [50001, 50110, 50200],
            "z_mag": [20.0, 20.2, 20.3],
            "z_mag_err": [0.3, 0.1, 0.2]
        },
    }

    lightcurve_bands = util.check_new_light_curve_data(new_data)
    expected_bands = list("gz")
    for band in expected_bands:
        assert band in lightcurve_bands
    unexpected_bands = list("uriy")
    for band in unexpected_bands:
        assert band not in lightcurve_bands

    # test an exception is thrown when missing part of the light curve data
    broken_data = {
        "image_1": {
            "g_time": [50500],
            "g_mag_err": [0.5]
        }
    }
    with pytest.raises(ValueError):
        util.check_new_light_curve_data(broken_data)

    # test an exception is thrown when the signature is not correct
    non_dict_data = [(50500, 20.0, 0.5)]
    with pytest.raises(AssertionError):
        util.check_new_light_curve_data(non_dict_data)
    
def test_load_light_curve():
    # this test requires the lightcurve object
    from livelcs.Classes.light_curve import LightCurve
    import pickle
    import os
    
    mock_image_1_data = {
        "u_time": [50000, 50001, 50003, 50004, 50010],
        "u_mag": [16.3, 16.3, 16.5, 16.2, 16.3],
        "u_mag_err": [0.1, 0.2, 0.1, 0.1, 0.1],
        "z_time": [50000, 50002, 50006, 50007, 50009],
        "z_mag": [17.3, 17.5, 17.7, 16.8, 17.1],
        "z_mag_err": [0.2, 0.2, 0.3, 0.3, 0.1]   
    }
    mock_image_2_data = {
        "u_time": [50000, 50001, 50003, 50004, 50010],
        "u_mag": [16.1, 16.0, 16.1, 16.1, 16.2],
        "u_mag_err": [0.1, 0.2, 0.1, 0.1, 0.1],
        "z_time": [50000, 50002, 50006, 50007, 50009],
        "z_mag": [17.5, 17.5, 17.3, 17.1, 17.1],
        "z_mag_err": [0.2, 0.2, 0.3, 0.3, 0.1]   
    }
    mock_data = {
        "time_last_updated": 10,
        "image_1": mock_image_1_data,
        "image_2": mock_image_2_data
    }
    mock_light_curve = LightCurve(data=mock_data)

    working_directory = "./"
    file_name_to_be_deleted = "test_light_curve"
    extension = ".lc"

    mock_light_curve.save_light_curve(
        file_name=os.path.join(working_directory,file_name_to_be_deleted),
        extension = ".lc"
    )

    loaded_light_curve = util.load_light_curve(
        file_name_to_be_deleted,
        directory=working_directory,
        extension=extension
    )

    assert type(loaded_light_curve) == LightCurve
    for item in mock_data:
        assert item in loaded_light_curve.data.keys()
    for key in mock_data.keys():
        if key.startswith("image_"):
            for image_key in mock_data[key].keys():
                assert image_key in loaded_light_curve.data[key].keys()
    
    if os.path.isfile(
        os.path.join(working_directory,file_name_to_be_deleted)+extension
    ):
        os.remove(
            os.path.join(working_directory, file_name_to_be_deleted)+extension
        )


            

    

    


    



    
    




















