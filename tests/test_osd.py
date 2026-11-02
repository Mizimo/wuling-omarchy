"""Device labels follow the same output target as Omarchy's volume command."""
import unittest
from unittest.mock import patch
from wuling import osd


class OsdTests(unittest.TestCase):
    def test_selected_sink_is_not_assumed_to_be_first(self):
        with patch("wuling.osd.probe", side_effect=["selected", '[{"name":"other","description":"Other"},{"name":"selected","description":"Speakers"}]']):
            self.assertEqual(osd.device("output")["name"], "Speakers")

    def test_unavailable_device_does_not_leak_unstructured_output(self):
        for data in ("service error", "{}", "null", '[{"name":"selected","description":{}}]'):
            with self.subTest(data=data), patch("wuling.osd.probe", side_effect=["selected", data]):
                self.assertEqual(osd.device("output")["name"], "")
