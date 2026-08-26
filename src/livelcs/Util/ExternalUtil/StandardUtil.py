'''This file contains utility functions that focus on using standard libraries 
such as Astropy, Pandas, and Numpy to manipulate objects in our pipeline'''


def extract_ra_dec_target_string_sources(input_series):
    """Take an input pandas series that has columns 'name', 'ra', 'dec' and return extracted values
    input_series: pd.Series object 
    return: tuple with types 
        (
            str: name,
            float: ra,
            float: dec,
            int: n_sources
        )
    """
    from pandas import Series, Dataframe

    if type(input_series) is Series:
        try:
            ra = float(input_series["ra"])
            dec = float(input_series["dec"])
            target_string = str(input_series["name"])
            return target_string, ra, dec
        except:
            print("input dataframe must have 'name', 'ra', and 'dec'")
            return None, None, None
    elif type(input_series) is DataFrame:

        try:
            ra = float(input_series["ra"].values[0])
            dec = float(input_series["dec"].values[0])
            target_string = str(input_series["name"].values[0])
            n_sources = int(input_series['n_sources'].values[0])
            return target_string, ra, dec, n_sources
        except:
            print("input dataframe must have 'name', 'ra', 'dec', and 'n_sources'")
            return None, None, None, None


def adjust_fits_header(my_header, image_metadata):
    '''This adds a few pieces of metadata to the header
    my_header: FITS header object to adjust for Lightcurver
    image_metadata: metadata from an LSST image_exposure object using it's method image_exposure.getMetadata()
    return: updated header with 'OBSTART', 'EXPTIME', 'GAIN' key value pairs
    '''
    my_header['OBSTART'] = image_metadata['DATE-BEG']
    my_header['EXPTIME'] = image_metadata['SHUTTIME']
    my_header['GAIN'] = image_metadata['CCDGAIN']
    return my_header


def extract_table_from_database(path_to_database, table_to_extract):
    '''This function queries the database file for a specific table to extract
    param path_to_database: string representing the path to a sqlite3 database
    param table_to_extract: string representing the name of the table to extract
    return: Pandas table with the requested label
    '''
    from sqlite3 import connect
    from pandas import read_sql_query

    query = f"SELECT * FROM {table_to_extract}"
    with connect(path_to_database) as database:
        extracted_table = read_sql_query(query, database)
    return extracted_table


def extract_frames_from_h5_file(path_to_h5_file, frames_table, zeropoint_table):
    '''This function extracts the important information stored in the h5 file, 
    which contains information about each frame.
    param path_to_h5_file: string representing a path to the h5 file
    param frames_table: pandas table with information about the frames
    param zeropoint_table: pandas table with information about the zeropoints
    return: series of lists of information about each frame
    '''
    from h5py import File
    import numpy as np

    narrow_psfs = []
    data_roi = []
    data_noisemap = []
    times_mjd = []

    with File(path_to_h5_file, 'r') as h5file:
        for index, frame in enumerate(h5file['frames']):
            for key in h5file['frames'][frame].keys():
                if key.startswith("psf"):
                    current_psf_key = key
            frame_narrow_psf = np.asarray(
                h5file['frames'][frame][current_psf_key]['narrow_psf']
            )
            frame_data = np.asarray(
                h5file['frames'][frame]['data']['ROI']
            )
            frame_noisemap = np.asarray(
                h5file['frames'][frame]['noisemap']['ROI']
            )
            # check if the frame has undefined or corrupted data
            if np.nan_to_num(
                np.max(frame_data), nan=-9999
            ) == -9999:
                continue
            times_mjd.append(frames_table['mjd'].to_numpy()[index])
            data_roi.append(frame_data)
            narrow_psfs.append(frame_narrow_psf)
            data_noisemap.append(frame_noisemap)
    times_mjd = np.asarray(times_mjd)
    data_roi = np.stack(data_roi)
    narrow_psfs = np.stack(narrow_psfs)
    data_noisemap = np.stack(data_noisemap)
    seeings = frames_table['seeing_arcseconds'].to_numpy()
    zeropoints = zeropoint_table['zeropoint'].to_numpy()

    extracted_frames_dict = {
        'times_mjd': times_mjd,
        'data_roi': data_roi,
        'narrow_psfs': narrow_psfs,
        'data_noisemap': data_noisemap,
        'seeings': seeings,
        'zeropoints': zeropoints
    }

    return extracted_frames_dict











