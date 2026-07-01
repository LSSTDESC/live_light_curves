import pytest
from livelcs.Classes.lensed_quasar_cutouts import QuasarCutouts

class TestQuasarCutouts:
    def test_init(self):
        not_a_file = "/Users/unknown_user/not_a_dir/not_a_file.fits"
        with pytest.raises(Exception):
            my_error_cutout = QuasarCutouts(file_name=not_a_file)
        initialization_with_no_data = QuasarCutouts(file_name=None)
        assert initialization_with_no_data.data is None
        assert initialization_with_no_data.header is None







