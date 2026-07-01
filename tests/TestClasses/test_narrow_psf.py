from numpy import array as nparray
import pickle
import os
from livelcs.Classes.narrow_psf import NarrowPsf

class TestNarrowPsf:

    dummy_file_name = "file_to_be_deleted.pkl"

    test_psf = {
        "data": nparray([
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
            [0,0,0.3,0.4,0,0],
            [0,0,0.3,0.4,0,0],
            [0,0,0,0,0,0],
            [0,0,0,0,0,0],
        ]),
        "noisemap": nparray([
            [0.05,0.05,0.05,0.05,0.05,0.05],
            [0.05,0.05,0.05,0.05,0.05,0.05],
            [0.05,0.05,0.05,0.05,0.05,0.05],
            [0.05,0.05,0.05,0.05,0.05,0.05],
            [0.05,0.05,0.05,0.05,0.05,0.05],
            [0.05,0.05,0.05,0.05,0.05,0.05],
        ])
    }
    
    with open(dummy_file_name, 'wb') as file:
        pickle.dump(test_psf, file)

    with open(dummy_file_name, 'rb') as file:
        loaded_data = pickle.load(file)
    
    def test_init(self):
        my_none_file = NarrowPsf()
        assert type(my_none_file) == NarrowPsf
        assert type(my_none_file.narrow_psf) is dict

        with open(self.dummy_file_name, 'wb') as file:
            pickle.dump(self.test_psf, file)

        my_loaded_file = NarrowPsf(self.dummy_file_name)
        assert type(my_loaded_file) == NarrowPsf
        assert type(my_loaded_file.narrow_psf) == dict

    def test_load_psf(self):
        with open(self.dummy_file_name, 'wb') as file:
            pickle.dump(self.test_psf, file)
        
        my_none_file = NarrowPsf()
        assert 'data' not in my_none_file.narrow_psf.keys()
        assert 'noisemap' not in my_none_file.narrow_psf.keys()

        my_none_file.load_psf(self.dummy_file_name)
        assert 'data' in my_none_file.narrow_psf.keys()
        assert 'noisemap' in my_none_file.narrow_psf.keys()
    
    def test_return_psf_data(self):
        with open(self.dummy_file_name, 'wb') as file:
            pickle.dump(self.test_psf, file)
        my_narrow_psf = NarrowPsf(self.dummy_file_name)
        pulled_data, pulled_noise = my_narrow_psf.return_psf_data()

        assert (pulled_data == self.test_psf['data']).all()
        assert (pulled_noise == self.test_psf['noisemap']).all()

    if os.path.isfile(dummy_file_name):
        os.remove(dummy_file_name)






