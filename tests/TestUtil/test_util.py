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

    



    
    




















