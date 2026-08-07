"""Class to initialize cutouts of stars"""


class StellarCutouts:
    """contains info about stars"""
    def __init__(self, flux_array):
        from numpy import array as nparray
        from astropy.io import fits

        if type(flux_array) == nparray:
            self.my_hdu = fits.PrimaryHDU(data=flux_array)
        elif type(flux_array) == str:
            with fits.open(flux_array) as hdul:
                self.my_hdu = hdul[0]
        elif type(flux_array) == fits.PrimaryHDU:
            self.my_hdu = flux_array
        elif type(flux_array) == fits.HDUList:
            self.my_hdu = flux_array[0]
        else:
            print(
                "Unsupported data type for flux array. Please prove \n", \
                "a numpy array, fits object, or pathway to a fits file"
            )
        return

    def save_cutout(
            self, 
            file_path="./", 
            file_name="star.fits",
            overwrite=False
        ):
        '''This method saves the stellar cutout 
        as a fits file.
        param file_path: directory to store files
        param file_name: name of the file to store
        param overwrite: bool to overwrite previous file
        '''
        from astropy.io import fits
        from os.path import join
        fits.writeto(
            join(file_path, file_name),
            self.my_hdu,
            overwrite=overwrite
        )













