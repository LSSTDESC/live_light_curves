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
    def save_light_curve(self, file_name, directory="./extracted_light_curves/", extension="_lc.json"):
        '''Save the current light curve
        file_name: string representing the full path of the file name
        extension: extension to use in the saved file name, default is .lc
        '''
        import json
        from os.path import join
        with open(join(directory, file_name) + extension, 'w') as f:
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
        from livelcs.Util.InternalUtil.LiveLightCurvesUtil import check_new_light_curve_data 
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

        self.time_last_updated = float(astro_time.now().mjd)
        self.data['time_last_updated'] = self.time_last_updated
        return None


def load_light_curve(file_name, directory="./extracted_light_curves/", extension="_lc.json"):
    '''load the json light curve from a file
    file_name: string representing the path of the file to load
    directory: string representing the directory containing the file to load
    extension: extension of the lightcurve object, default is .lc
    return: lightcurve object
    '''

    import json
    import os

    if os.path.isdir(directory) is False:
        os.mkdir(directory)
    if os.path.isfile(os.path.join(directory+file_name)+extension) is False:
        blank_light_curve = LightCurve()
        blank_light_curve.save_light_curve(file_name, directory=directory, extension=extension)
    with open(os.path.join(directory,file_name)+extension, 'r') as f:
        loaded_light_curve_data = json.load(f)
        loaded_light_curve = LightCurve(data=loaded_light_curve_data)
    assert type(loaded_light_curve) == LightCurve
    if "time_last_updated" not in loaded_light_curve.data:
        loaded_light_curve["time_last_updated"] = None
    return loaded_light_curve



def check_new_light_curve_data(new_data):
    '''check that the new data is in the correct format for the light curve object
    new_data: dictionary of data to append a lightcurve object
    return: set object containing no duplicates for the bands to query
    '''
    assert type(new_data) is dict, "new data must be a dictionary"
    new_data_images = set([key for key in new_data.keys()])
    for image in new_data_images:
        new_data_bands = set([key.split("_")[0] for key in new_data[image].keys()])
        for band in new_data_bands:
            if band+"_time" not in new_data[image] or band+"_mag" not in new_data[image] or band+"_mag_err" not in new_data[image]:
                raise ValueError(f"new data for band {band} must include time, mag, and mag_err")
    return new_data_bands
  
