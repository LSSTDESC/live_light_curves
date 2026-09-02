from livelcs.LightCurves.light_curve import LightCurve

class TestLightCurve:
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

    def test_init(self):
        self.empty_light_curve = LightCurve()
        self.mock_light_curve = LightCurve(data=self.mock_data)
    
    def test_save_light_curve(self):
        import os
        file_name_to_be_deleted = "./garbage_test_file"
        assert not os.path.isfile(file_name_to_be_deleted+"_lc.json")
        self.empty_light_curve = LightCurve()
        self.mock_light_curve = LightCurve(data=self.mock_data)

        self.empty_light_curve.save_light_curve(
            file_name=file_name_to_be_deleted,
        )
        assert os.path.isfile(file_name_to_be_deleted+"_lc.json")
        os.remove(file_name_to_be_deleted+"_lc.json")
        assert not os.path.isfile(file_name_to_be_deleted+".lc_alt")
        self.mock_light_curve.save_light_curve(
            file_name=file_name_to_be_deleted,
            extension=".lc_alt"
        )
        assert os.path.isfile(file_name_to_be_deleted+".lc_alt")
        os.remove(file_name_to_be_deleted+".lc_alt")

    
    def test_update_light_curve(self):
        self.empty_light_curve = LightCurve()
        self.mock_light_curve = LightCurve(data=self.mock_data)
        assert "time_last_updated" in self.empty_light_curve.data.keys()
        assert "u_time" not in self.empty_light_curve.data.keys()
        self.empty_light_curve.update_light_curve(
            new_data={
                "image_1": self.mock_image_1_data
            }
        )
        assert "u_time" in self.empty_light_curve.data["image_1"].keys()
        assert "image_2" not in self.empty_light_curve.data.keys()
        self.empty_light_curve.update_light_curve(
            new_data={
                "image_1": self.mock_image_1_data,
                "image_2": self.mock_image_2_data
            }
        )
        

def test_load_light_curve():
    # this test requires the lightcurve object
    from livelcs.LightCurves.light_curve import LightCurve
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
    extension = "_lc.json"

    mock_light_curve.save_light_curve(
        file_name=os.path.join(working_directory,file_name_to_be_deleted),
        extension = "_lc.json"
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

def test_check_new_light_curve_data():
    import pytest 
    from livelcs.LightCurves.light_curve import check_new_light_curve_data
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

    lightcurve_bands = check_new_light_curve_data(new_data)
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
        check_new_light_curve_data(broken_data)

    # test an exception is thrown when the signature is not correct
    non_dict_data = [(50500, 20.0, 0.5)]
    with pytest.raises(AssertionError):
        check_new_light_curve_data(non_dict_data)
    
            
        



        






