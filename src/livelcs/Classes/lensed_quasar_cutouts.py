"""class containing quasar cutout(s)"""

# add point source positions to init


class QuasarCutouts:
    """contains cutout of quasar cutouts
    file_name: string representing the path to the file of a cutout"""
    def __init__(self, file_name=None):
        if file_name is not None:
            with fits.open(file_name) as hdul:
                self.data = hdul[0].data
                self.header = hdul[0].header
        else:
            self.data = None
            self.header = None
