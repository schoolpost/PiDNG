from unittest import TestCase

from pidng.core import RPICAM2DNG

class TestConvert(TestCase):

    def test_convert(self):
        pidng = RPICAM2DNG().convert("../imx477.jpg")

