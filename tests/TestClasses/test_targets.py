from livelcs.Classes.targets import Targets


class TestTargets:

    def test_init(self):
        my_targets = Targets()
        assert type(my_targets) == Targets
        
