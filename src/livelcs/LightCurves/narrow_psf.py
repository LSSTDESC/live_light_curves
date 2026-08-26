"""Narrow point spread function class"""
import pickle

class NarrowPsf:
    """class that handles the PSF for this pipeline. Must be stored in a way that 
    is compatable with Starred."""
    def __init__(self, psf_file=None):
        if psf_file is not None:
            self.load_psf(psf_file)
        else:
            self.narrow_psf = dict()
    
    def load_psf(self, psf_file):
        """load the psf from a file. 
        The file should be a .pkl file containing a dictionary with keys 'data' and 'noisemap'."""
        self.psf_file = psf_file
        with open(psf_file, 'rb') as file:
            self.narrow_psf = pickle.load(file)
        assert 'data' in self.narrow_psf, "PSF file must contain 'data' key"
        assert 'noisemap' in self.narrow_psf, "PSF file must contain 'noisemap' key"
    
    def return_psf_data(self):
        """return the psf data and noisemap as a tuple."""
        return self.narrow_psf['data'], self.narrow_psf['noisemap']









    
