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

from commoncode.testcase import FileBasedTesting
from licensedcode import models


TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


class TestLicense(FileBasedTesting):
    test_data_dir = TEST_DATA_DIR

    def test_load_license(self):
        test_dir = self.get_test_loc('models/licenses')
        lics = models.load_licenses(test_dir)
        # one license is obsolete and not loaded
        expected = [u'apache-2.0', u'bsd-ack-carrot2', u'w3c-docs-19990405']
        assert expected == sorted(lics.keys())

        assert all(isinstance(l, models.License) for l in lics.values())
        # test a sample of a licenses field
        assert '1994-2002 World Wide Web Consortium' in lics[u'w3c-docs-19990405'].text

    def test_get_texts(self):
        test_dir = self.get_test_loc('models/licenses')
        lics = models.load_licenses(test_dir)
        for lic in lics.values():
            assert 'distribut' in lic.text.lower()

    def test_rules_from_licenses(self):
        test_dir = self.get_test_loc('models/licenses')
        lics = models.load_licenses(test_dir)
        rules = list(models.rules_from_licenses(lics))
        assert 4 == len(rules)
        for rule in rules:
            assert 'distribut' in rule.text().lower()


class TestRule(FileBasedTesting):
    test_data_dir = TEST_DATA_DIR

    def test_create_template_rule(self):
        test_rule = models.Rule(_text=u'A one. A {{}}two. A three.')
        expected = ['a', 'one', 'a', 'two', 'a', 'three']
        assert expected == list(test_rule.tokens())
        assert 6 == test_rule.length
        assert set([2]) == test_rule.gaps

    def test_create_plain_rule_with_text_file(self):
        def create_test_file(text):
            tf = self.get_temp_file()
            with open(tf, 'wb') as of:
                of.write(text)
            return tf

        test_rule = models.Rule(text_file=create_test_file('A one. A two. A three.'))
        expected = ['a', 'one', 'a', 'two', 'a', 'three']
        assert expected == list(test_rule.tokens())
        assert set() == test_rule.gaps
        assert 6 == test_rule.length

    def test_load_rules(self):
        test_dir = self.get_test_loc('models/rules')
        rules = list(models.rules(test_dir))
        # one license is obsolete and not loaded
        assert 3 == len(rules)
        assert all(isinstance(r, models.Rule) for r in rules)
        # test a sample of a licenses field
        expected = [[u'lzma-sdk-original'], [u'gpl-2.0'], [u'oclc-2.0']]
        assert sorted(expected) == sorted(r.licenses for r in rules)

    def test_template_rule_is_loaded_correctly(self):
        test_dir = self.get_test_loc('models/rule_template')
        rules = list(models.rules(test_dir))
        assert 1 == len(rules)

    def test_rule_data_ignores_small_text_differences(self):
        r1 = models.Rule(_text='Some text')
        r2 = models.Rule(_text='Some \n_-text')
        assert r1._data() == r2._data()

    def test_rule_data_includes_structure(self):
        r1 = models.Rule(_text='Some text', license_choice=False)
        r2 = models.Rule(_text='Some text', license_choice=True)
        assert r1._data() != r2._data()

    def test_rule_len_is_computed_correctly(self):
        test_text = '''zero one two three
            four {{gap1}}
            five six seven eight nine ten'''
        r1 = models.Rule(_text=test_text)
        list(r1.tokens())
        assert 11 == r1.length

    def test_gaps_at_start_and_end_are_ignored(self):
        test_text = '''{{gap0}}zero one two three{{gap2}}'''
        r1 = models.Rule(_text=test_text)
        assert ['zero', 'one', 'two', 'three'] == list(r1.tokens())
        assert set() == r1.gaps

    def test_rule_tokens_and_gaps_are_computed_correctly(self):
        test_text = '''I hereby abandon any{{SAX 2.0 (the)}}, and Release all of {{the SAX 2.0 }}source code of his'''
        rule = models.Rule(_text=test_text, licenses=['public-domain'])

        rule_tokens = list(rule.tokens())
        assert ['i', 'hereby', 'abandon', 'any', 'and', 'release', 'all', 'of', 'source', 'code', 'of', 'his'] == rule_tokens

        rule_tokens = list(rule.tokens(lower=False))
        assert ['I', 'hereby', 'abandon', 'any', 'and', 'Release', 'all', 'of', 'source', 'code', 'of', 'his'] == rule_tokens

        gaps = rule.gaps
        assert set([3, 7]) == gaps

    def test_negative(self):
        assert models.Rule(_text='test_text').negative()
        assert not models.Rule(_text='test_text', licenses=['mylicense']).negative()
        assert models.Rule(_text='test_text', licenses=[]).negative()
