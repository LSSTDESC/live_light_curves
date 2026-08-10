"""Class that holds the light curves as they are being constructed"""

class LightCurve:
    '''LightCurve and data should be dictionaries. 
    data: dictionary with format:
    data = {
        'time_last_updated': time_last_updated,
        'label_A': {
            'u_time': [time1, time2, ...],
            'u_mag': [mag1, mag2, ...],
            'u_mag_err': [mag_err1, mag_err2, ...],
            'g_time': [time1, time2, ...],
            'g_mag': [mag1, mag2, ...],
            'g_mag_err': [mag_err1, mag_err2, ...],
        },
        'label_B': {
            'u_time': [time1, time2, ...],
            'u_mag': [mag1, mag2, ...],
            'u_mag_err': [mag_err1, mag_err2, ...],
            'g_time': [time1, time2, ...],
            'g_mag': [mag1, mag2, ...],
            'g_mag_err': [mag_err1, mag_err2, ...],
        }
    }
    update_time: time in MJD of the last update.
    '''
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

### NEED TO INCLUDE ASTROMETRY OF EACH OBJECT IN ROI. NEED RA/DEC PER IMAGE IN LC.
### ALSO NEED SOME RELATIVE PATH OF A JPEG PSF PER IMAGE PER BAND PER VISIT TO SEND TO WEBPAGE
    def save_light_curve(self, file_name, extension="_lc.json"):
        '''Save the current light curve
        file_name: string representing the full path of the file name
        extension: extension to use in the saved file name, default is .lc
        '''
        import json
        with open(file_name + extension, 'wb') as f:
            json.dump(self.data, f)
        return None
    
## UPDATE LIGHT CURVE MUST ALSO STORE THE PSF AT EACH VISIT IMAGE / BAND / TIME
    def update_light_curve(self, new_data):
        '''Update the current light curve
        new_data: dictionary object with the same signature of the lightcurve
        data dictionary.
        return: None
        '''
        from astropy.time import Time as astro_time
        from livelcs.Util.util import check_new_light_curve_data 
        if self.time_last_updated is None:
            self.time_last_updated = astro_time.now()

        new_data_bands = check_new_light_curve_data(new_data)

        if self.data is None:
            self.data = new_data

        else:
            for image in new_data.keys():
                if image not in self.data.keys():
                    self.data[image] = dict()

                for band in new_data_bands:
                    if band+"_time" not in self.data[image].keys():
                        self.data[image][band+"_time"] = new_data[image][band+"_time"]
                        self.data[image][band+"_mag"] = new_data[image][band+"_mag"]
                        self.data[image][band+"_mag_err"] = new_data[image][band+"_mag_err"]
                    else:
                        self.data[image][band+"_time"].extend(new_data[image][band+"_time"])
                        self.data[image][band+"_mag"].extend(new_data[image][band+"_mag"])
                        self.data[image][band+"_mag_err"].extend(new_data[image][band+"_mag_err"])

        self.time_last_updated = astro_time.now()
        return None




