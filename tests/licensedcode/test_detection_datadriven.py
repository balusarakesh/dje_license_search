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

import codecs
from collections import OrderedDict
import os
from os.path import abspath
from os.path import join
import unittest
from unittest.case import expectedFailure

from commoncode import fileutils
from commoncode import functional
from commoncode import text

from licensedcode import saneyaml
from licensedcode import index


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data/licenses')


"""
Data-driven tests using expectations stored in YAML files.
"""


class LicenseTest(object):
    """
    A license detection test is used to verify that license detection works
    correctly

    It consists of two files with the same base name: a .yml file with test data
    and a test file with any other extension that needs to be tested for
    detection

    The following data are loaded from the .yml file:
     - a test file to scan for licenses,
     - a list of expected licenses (with optional positions) to detect,
     - optional notes.
     - a boolean flag expected_failure set to True if a test is expected to fail
       for now

    If the list of licenses is empty, then this test should not detect any
    license in the test file.
    """
    def __init__(self, data_file=None, test_file=None):
        self.data_file = data_file
        self.test_file = test_file
        if self.test_file:
            self.test_file_name = fileutils.file_name(test_file)

        if self.data_file:
            with codecs.open(data_file, mode='rb', encoding='utf-8') as df:
                data = saneyaml.load(df.read())

        self.licenses = data.get('licenses', [])
        # TODO: this is for future support of license expressions
        self.license = data.get('license', None)
        self.notes = data.get('notes')
        self.expected_failure = data.get('expected_failure', False)

    def asdict(self):
        dct = OrderedDict()
        if self.licenses:
            dct['licenses'] = self.licenses
        if self.expected_failure:
            dct['expected_failure'] = self.expected_failure
        if self.notes:
            dct['notes'] = self.notes
        return dct

    def dump(self):
        """
        Dump a representation of self to tgt_dir using two files:
         - a .yml for the rule data in YAML block format
         - a .RULE: the rule text as a UTF-8 file
        """
        as_yaml = saneyaml.dump(self.asdict())
        with codecs.open(self.data_file, 'wb', encoding='utf-8') as df:
            df.write(as_yaml)


def load_license_tests(test_dir=TEST_DATA_DIR):
    """
    Yield an iterable of LicenseTest loaded from test data files in test_dir.
    """
    # first collect files with .yml extension and files with other extensions
    # in two  maps keyed by file base_name
    data_files = {}
    test_files = {}
    for top, _, files in os.walk(test_dir):
        for yfile in files:
            base_name = fileutils.file_base_name(yfile)
            file_path = abspath(join(top, yfile))
            if yfile.endswith('.yml'):
                assert base_name not in data_files
                data_files[base_name] = file_path
            else:
                assert base_name not in test_files
                test_files[base_name] = file_path

    # ensure that each data file has a corresponding test file
    diff = set(data_files.keys()).symmetric_difference(set(test_files.keys()))
    assert not diff

    # second, create pairs of a data_file and the corresponding test file
    # that have the same base_name
    for base_name, data_file in data_files.items():
        test_file = test_files[base_name]
        yield LicenseTest(data_file, test_file)


def build_tests(license_tests, clazz):
    """
    Dynamically build test methods from a sequence of LicenseTest and attach
    these method to the clazz test class.
    """
    for test in license_tests:
        # absolute path
        tfn = test.test_file_name
        tf = test.test_file
        test_name = 'test_detection_%(tfn)s' % locals()
        test_name = text.python_safe_name(test_name)
        # closure on the test params
        test_method = make_license_test_function(test.licenses, tf, test_name)

        if test.expected_failure:
            test_method = expectedFailure(test_method)
        # attach that method to our test class
        setattr(clazz, test_name, test_method)


def flat_keys(matches):
    """
    Return a flattened list of detected license keys, sorted by position and then rule order.
    """
    return functional.flatten(match.rule.licenses for match in matches)


def make_license_test_function(expected_licenses, test_file, test_name, min_score=100, check_negative=True):
    """
    Build a test function closing on tests arguments
    """
    if not isinstance(expected_licenses, list):
        expected_licenses = [expected_licenses]

    def data_driven_test_function(self):
        idx = index.get_index()
        matches = idx.match(location=test_file, min_score=min_score, _check_negative=check_negative)
        # the detected license is the first member of the returned tuple
        license_result = flat_keys(matches)
        try:
            assert expected_licenses == license_result
        except:
            # on failure, we compare against more result data to get additional
            # failure details, including the test_file and full match details
            from licensedcode.query import get_texts
            matches_with_qtexts = []
            for m in matches:
                qtext, itext = get_texts(m, location=test_file, dictionary=idx.dictionary, width=80)
                matches_with_qtexts.append((m, qtext.splitlines(), m.qspans, itext.splitlines(), m.ispans,))
            assert expected_licenses == ['test file: ' + test_file] + [repr(license_result)] + matches_with_qtexts

    data_driven_test_function.__name__ = test_name
    data_driven_test_function.funcname = test_name
    return data_driven_test_function


class TestLicenseDataDriven(unittest.TestCase):
    # test functions are attached to this class at module import time
    pass


build_tests(license_tests=load_license_tests(), clazz=TestLicenseDataDriven)
