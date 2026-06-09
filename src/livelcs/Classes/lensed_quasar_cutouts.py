"""class containing quasar cutouts"""

# add point source positions to init


class QuasarCutouts(file_name=None):
    """contains cutout of quasar cutouts"""
    def __init__(self):
        if file_name is not None:
            with fits.open(file_name) as hdul:
                self.data = hdul[0].data
                self.header = hdul[0].header
        else:
            self.data = None
            self.header = None
