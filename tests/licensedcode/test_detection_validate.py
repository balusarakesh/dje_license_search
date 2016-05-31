#
# Copyright (c) 2015 nexB Inc. and others. All rights reserved.
# http://nexb.com and https://github.com/nexB/scancode-toolkit/
# The ScanCode software is licensed under the Apache License version 2.0.
# Data generated with ScanCode require an acknowledgment.
# ScanCode is a trademark of nexB Inc.
#
# You may not use this software except in compliance with the License.
# You may obtain a copy of the License at: http://apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed
# under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
# CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#
# When you publish or redistribute any data created with ScanCode or any ScanCode
# derivative work, you must accompany this data with the following acknowledgment:
#
#  Generated with ScanCode and provided on an "AS IS" BASIS, WITHOUT WARRANTIES
#  OR CONDITIONS OF ANY KIND, either express or implied. No content created from
#  ScanCode should be considered or used as legal advice. Consult an Attorney
#  for any legal advice.
#  ScanCode is a free software code scanning tool from nexB Inc. and others.
#  Visit https://github.com/nexB/scancode-toolkit/ for support and download.

from __future__ import absolute_import, print_function

import os
import unittest

from commoncode import text
from licensedcode import models

from test_detection_datadriven import make_license_test_function


"""
Validate that each reference license texts is properly detected.
"""

def build_tests(data_set, clazz):
    """
    Dynamically build an individual test method for each license texts and spdx
    texts in a licenses `data_set` mapping attaching the test method to the
    `clazz` test class.
    """
    for license_key, license_obj in data_set.items():
        if license_obj.text_file and os.path.exists(license_obj.text_file):
            test_name = ('test_validate_detection_of_text_for_' + text.python_safe_name(license_key))
            test_method = make_license_test_function(license_key, license_obj.text_file, test_name, min_score=100, check_negative=False)
            setattr(clazz, test_name, test_method)

        if license_obj.spdx_license_key:
            if license_obj.spdx_file and os.path.exists(license_obj.spdx_file):
                test_name = ('test_validate_detection_of_spdx_text_for_' + text.python_safe_name(license_key))
                test_method = make_license_test_function(license_key, license_obj.spdx_file, test_name, min_score=100, check_negative=False)
                setattr(clazz, test_name, test_method)


class TestValidateLicenseTextDetection(unittest.TestCase):
    # Test functions are attached to this class at import time
    pass


build_tests(data_set=models.get_licenses_by_key(), clazz=TestValidateLicenseTextDetection)
