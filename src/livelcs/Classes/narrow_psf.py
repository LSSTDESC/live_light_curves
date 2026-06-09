"""Narrow point spread function class"""

class NarrowPsf(psf_file=None):
    """class that handles the PSF for this pipeline. Must be stored in a way that 
    is compatable with Starred."""
    def __init__(self):
        if psf_file is not None:
            self.load_psf(psf_file)
        else:
            self.narrow_psf = None
    
    def load_psf(self, psf_file):
        """load the psf from a file. 
        The file should be a .npy file containing a dictionary with keys 'data' and 'noisemaps'."""
        self.psf_file = psf_file
        self.narrow_psf = np.load(psf_file, allow_pickle=True).item()
        assert 'data' in self.narrow_psf, "PSF file must contain 'data' key"
        assert 'noisemaps' in self.narrow_psf, "PSF file must contain 'noisemaps' key"
    
    def return_psf_data(self):
        """return the psf data and noisemaps as a tuple."""
        return self.narrow_psf['data'], self.narrow_psf['noisemaps']









    
