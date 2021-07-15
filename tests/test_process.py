from unittest import TestCase

from pydng.core import RPICAM2DNG


class TestProcessing(TestCase):
    def test_processing(self):

        def processing(raw, _dummy):
            # access to the bayer raw numpy array here.
            print(raw.shape, raw.size)
            return raw

        RPICAM2DNG().convert("../imx477.jpg", process=processing)


