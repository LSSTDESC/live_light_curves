"""Class that holds the light curves as they are being constructed"""

class LightCurve():
    """LightCurve and data should be dictionaries. The format should be 
    such that:
    data = {
        'time_last_updated': time_last_updated,
        'img_A': {
            'u_time': [time1, time2, ...],
            'u_mag': [mag1, mag2, ...],
            'u_mag_err': [mag_err1, mag_err2, ...],
            'g_time': [time1, time2, ...],
            'g_mag': [mag1, mag2, ...],
            'g_mag_err': [mag_err1, mag_err2, ...],
        },
        'img_B': {
            'u_time': [time1, time2, ...],
            'u_mag': [mag1, mag2, ...],
            'u_mag_err': [mag_err1, mag_err2, ...],
            'g_time': [time1, time2, ...],
            'g_mag': [mag1, mag2, ...],
            'g_mag_err': [mag_err1, mag_err2, ...],
        }
    }
    ...
    }
    time_last_updated and update_time is in MJD.
    """
    def __init__(
            self, 
            data=None, 
            update_time=None
    ):
        if data is None:
            self.data = {'time_last_updated': 40587}
        else:
            self.data = data
        if update_time is None:
            self.time_last_updated = self.data['time_last_updated']
        else:
            self.time_last_updated = update_time

    def save_light_curve(self, file_name, extension=".lc"):
        # save the light curve to a file
        import pickle
        with open(file_name + extension, 'wb') as f:
            pickle.dump(self, f)
    

    def update_light_curve(self, new_data):
        # append new data to light curves
        from astropy.time import Time as astro_time
        from livelcs.Util.util import check_new_light_curve_data 
        if self.update_time is None:
            self.update_time = astro_time.now()

        new_data_bands = check_new_light_curve_data(new_data)

        if self.data is None:
            self.data = new_data

        else:
            for band in new_data_bands:
                if band+"_time" not in new_data:
                    self.data[band+"_time"] = new_data[band+"_time"]
                    self.data[band+"_mag"] = new_data[band+"_mag"]
                    self.data[band+"_mag_err"] = new_data[band+"_mag_err"]
                else:
                    for value in new_data[band+"_time"]:
                        self.data[band+"_time"].append(value)
                    for value in new_data[band+"_mag"]:
                        self.data[band+"_mag"].append(value)
                    for value in new_data[band+"_mag_err"]: 
                        self.data[band+"_mag_err"].append(value)
                    
        self.time_last_updated = astro_time.now()




