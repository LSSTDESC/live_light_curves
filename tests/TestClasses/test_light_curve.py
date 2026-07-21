from livelcs.Classes.light_curve import LightCurve

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
        


        



        






