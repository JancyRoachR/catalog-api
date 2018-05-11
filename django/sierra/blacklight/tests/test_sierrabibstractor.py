"""
Tests the sierrabibstractor data extraction functions.
"""

import re

import pytest
from blacklight import sierrabibstractor as sb


# FIXTURES AND TEST DATA
# External fixtures used here can be found in
# django/sierra/base/tests/conftest.py:
#    sierra_records_by_recnum_range

pytestmark = pytest.mark.django_db

@pytest.fixture
def bib(sierra_records_by_recnum_range):
    """
    Pytest fixture, returns test bib record b4371446.
    """
    return sierra_records_by_recnum_range('b4371446')[0]


@pytest.fixture
def varfields(bib):
    """
    Pytest fixture, returns all varfields on the test bib record.
    """
    fields = []
    for vf in bib.record_metadata.varfield_set.all():
        fields.append({'tag': vf.marc_tag, 'data': unicode(vf.field_content)})
    return fields


# TESTS
# Note here that Sierra has its own idea about what Control Fields and
# Variable Length Fields (varfields) are. According to the MARC
# standard, control fields are fields 001 to 009. In Sierra, only
# fields 006, 007, and 008 are stored in the control_field table.
# 001 through 005 are stored in the varfield table. (Fields 002, 004,
# and 009 are invalid.) Hence, there are some tests that test for tags
# < 010 in the varfields.

def test_extractleader__tag_is_LDR(bib):
    """
    The tag for the extracted leader should be LDR.
    """
    leader = sb.extract_leader(bib)[0]
    assert leader['tag'] == 'LDR'


def test_extractleader__data_is_correct(bib):
    """
    Data from the extracted leader should match what's in the test
    record.
    """
    leader = sb.extract_leader(bib)[0]
    assert leader['data'] == '#####nam  22#####   4500'


def test_extractleader__indicators_are_none(bib):
    """
    Leader indicators should be [None, None].
    """
    leader = sb.extract_leader(bib)[0]
    assert leader['indicators'] == [None, None]


def test_extractleader__subfields_is_empty(bib):
    """
    Leader subfields should be an empty list.
    """
    leader = sb.extract_leader(bib)[0]
    assert leader['subfields'] == []


def test_extractleader__occurrence_is_zero(bib):
    """
    Leader occurrence should always be 0. (It should sort first in a
    list of fields.)
    """
    leader = sb.extract_leader(bib)[0]
    assert leader['occurrence'] == 0


def test_extractcontrolfields__tags_have_correct_pattern(bib):
    """
    Control field tags should be less than 010 and 3 characters long.
    """
    cfields = sb.extract_controlfields(bib)
    for cf in cfields:
        assert int(cf['tag']) < 10
        assert len(cf['tag']) == 3


def test_extractcontrolfields__007_data_correct(bib):
    """
    Sanity test to make sure the test record returns the correct data
    for one of the control fields (007). (Whitespace at the end of
    control fields is inconsistent, so we strip it from the data for
    comparison.)
    """
    cfields = sb.extract_controlfields(bib)
    exp_data = 'sd|bsmenn||||e'
    for cf in cfields:
        if cf['tag'] == '007':
            assert cf['data'].strip() == exp_data


def test_extractcontrolfields__indicators_are_None(bib):
    """
    Control field indicators should be [None, None].
    """
    cfields = sb.extract_controlfields(bib)
    for cf in cfields:
        assert cf['indicators'] == [None, None]


def test_extractcontrolfields__subfields_is_empty(bib):
    """
    Control field subfields should be an empty list.
    """
    cfields = sb.extract_controlfields(bib)
    for cf in cfields:
        assert cf['subfields'] == []


def test_extractcontrolfields__occurrence_gte_zero(bib):
    """
    Control field occurrence should exist and be 0 or greater.
    """
    cfields = sb.extract_controlfields(bib)
    for cf in cfields:
        assert cf['occurrence'] >= 0


def test_extractvarfields__tags_have_correct_pattern(bib):
    """
    Varfield tags should be 3 characters, 001 to 999.
    """
    varfields = sb.extract_varfields(bib)
    for vf in varfields:
        assert int(vf['tag']) < 1000 and int(vf['tag']) > 0
        assert len(vf['tag']) == 3


def test_extractvarfields__tags_lt_010__indicators_are_none(bib):
    """
    Varfield tags less than 010 (001, 003, 005) should have indicators
    equal to [None, None]
    """
    varfields = sb.extract_varfields(bib)
    for vf in varfields:
        if int(vf['tag']) < 10:
            assert vf['indicators'] == [None, None]


def test_extractvarfields__tags_lt_010__no_subfields(bib):
    """
    Varfield tags less than 010 (001, 003, 005) shouldn't have
    subfields (should be an empty list).
    """
    varfields = sb.extract_varfields(bib)
    for vf in varfields:
        if int(vf['tag']) < 10:
            assert vf['subfields'] == []


def test_extractvarfields__tags_gte_010__have_indicators(bib):
    """
    Varfield tags >= 010 should always have two indicator values.
    """
    varfields = sb.extract_varfields(bib)
    for vf in varfields:
        if int(vf['tag']) >= 10:
            assert len(vf['indicators']) == 2


def test_extractvarfields__tags_gte_010__have_subfields(bib):
    """
    Varfield tags >= 010 should always have at least one subfield.
    """
    varfields = sb.extract_varfields(bib)
    for vf in varfields:
        if int(vf['tag']) >= 10:
            assert len(vf['subfields']) > 0


def test_extractvarfields__subfields_have_valid_tags(bib):
    """
    For varfields with subfields, each subfield must have a valid
    (1-character) tag.
    """
    varfields = sb.extract_varfields(bib)
    for vf in varfields:
        for sf in vf['subfields']:
            assert len(sf['tag']) == 1


def test_extractvarfields_subfields_have_data(bib):
    """
    For varfields with subfields, each subfield should have data--at
    least, in the test record.
    """
    varfields = sb.extract_varfields(bib)
    for vf in varfields:
        for sf in vf['subfields']:
            assert sf['data']


def test_extractvarfields__subfields_in_correct_order(bib, varfields):
    """
    extract_varfields should put parsed subfields into
    the same order they occur in the BibRecord field data.
    """
    extracted_varfields = sb.extract_varfields(bib)
    for i, vf in enumerate(extracted_varfields):
        exp_subfields = re.findall(r'\|(.)', varfields[i]['data'])
        assert [sf['tag'] for sf in vf['subfields']] == exp_subfields


def test_extractvarfields__245_field_is_correct(bib):
    """
    Just a sanity check to make sure a varfield in the test record (the
    245) is structured correctly.
    """
    varfields = sb.extract_varfields(bib)
    for vf in varfields:
        if vf['tag'] == '245':
            assert vf['indicators'][0] == ' '
            assert vf['indicators'][1] == '0'
            assert len(vf['subfields']) == 1
            assert vf['subfields'][0]['tag'] == 'a'
            assert vf['subfields'][0]['data'] == 'Testing remote storage holds'


def test_extract__gets_all_fields(bib):
    """
    extract should pull the Leader, control fields, and variable length
    fields from the record and return them in one list. I'm not sure
    how to test this without either hardcoding the test record fields
    into the test (which I have done on a few of these) or re-creating
    the `extract` method code in the test. For now I'm just counting
    the number of fields returned to make sure it matches up with
    what's on the bib record object, and then doing spot-checks on a
    few important fields to make sure they exist.
    """
    fields = sb.extract(bib)
    exp_num_controlfields = len(bib.record_metadata.controlfield_set.all())
    exp_num_varfields = len(bib.record_metadata.varfield_set.all())
    assert len(fields) == exp_num_varfields + exp_num_controlfields + 1
    assert bool([field for field in fields if field['tag'] == 'LDR'])
    assert bool([field for field in fields if field['tag'] == '001'])
    assert bool([field for field in fields if field['tag'] == '007'])
    assert bool([field for field in fields if field['tag'] == '245'])
