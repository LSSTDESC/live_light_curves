from livelcs.Classes.stellar_photometry import StellarPhotometry


class TestStellarPhotometry:

    def test_init(self):
        my_photometry = StellarPhotometry()
        assert type(my_photometry) == StellarPhotometry
        






