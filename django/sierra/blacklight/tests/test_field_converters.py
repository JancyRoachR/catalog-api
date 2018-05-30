"""
Tests the blacklight.field_converters functions.
"""

import pytest
import re
import collections

from blacklight import parsers
from blacklight import field_converters


# FIXTURES AND TEST DATA
# External fixtures used in this file can be found in
# django/sierra/blacklight/tests/conftest.py:
#    make_field
#    make_sierrabib



# TESTS

def test_sierrabib_to_record_id():
    """
    `sierrabib_to_record_id` should return the record_id from the bib
    fixedfields.
    """
    test_data = {'bib': {'fixedfields': {'record_id': 'b12345678'}}}
    assert field_converters.sierrabib_to_record_id(test_data) == 'b12345678'


@pytest.mark.parametrize('field_data, author_field_index, expect_result', [
    (['100 ##$aByron, George Gordon Byron,$cBaron,$d1788-1824.'], 0, True),
    (['100 1#$aByron, George Gordon Byron,$cBaron,$d1788-1824.'], 0, True),
    (['100 2#$aByron, George Gordon Byron,$cBaron,$d1788-1824.'], 0, True),
    (['100 3#$aByron, George Gordon Byron,$cBaron,$d1788-1824.'], 0, True),
    (['100 4#$aByron, George Gordon Byron,$cBaron,$d1788-1824.'], 0, True),
    (['100 12$aByron, George Gordon Byron,$cBaron,$d1788-1824.'], 0, True),
    (['110 ##$aTest Corporation',
      '700 1#$aByron, George Gordon Byron,$cBaron,$d1788-1824.'], 0, False),
])
def test_sierrabibtopersonauthor__correct_field_and_parsers(field_data, author_field_index,
                                                            expect_result, make_field,
                                                            make_sierrabib):
    """
    `sierrabib_to_person_author` should act on the correct field (MARC
    100) and extract correct data via parsers. Invalid indicators
    should be tolerated. If the correct field is not present, it should
    return None.
    """
    sierrabib = make_sierrabib({}, field_data)
    result = field_converters.sierrabib_to_person_author({'bib': sierrabib})
    if expect_result:
        author_field = make_field(field_data[0])
        expected_fields = parsers.person_name(author_field)
        expected_fields.update(parsers.person_dates(author_field))
        expected_fields['titles'] = parsers.person_titles(author_field)
        assert all([result[k] == v for k, v in expected_fields.iteritems()])
    else:
        assert result is None


def test_sierrabib_to_contributors():
    """
    Placeholder test.
    """
    pass    


def test_itemrecord_to_barcode():
    """
    Placeholder test.
    """
    pass
    

def test_itemrecord_to_location():
    """
    Placeholder test.
    """
    pass


def test_itemrecord_to_callnumber():
    """
    Placeholder test.
    """
    pass


def test_untbib_to_id():
    """
    Placeholder test.
    """
    pass


def test_untbib_to_person_author_search_fullname_forms():
    """
    Placeholder test.
    """
    pass


def test_untbib_to_person_author_search_bestname():
    """
    Placeholder test.
    """
    pass


def test_untbib_to_person_author_display():
    """
    Placeholder test.
    """
    pass


def test_untbib_to_person_author_facet():
    """
    Placeholder test.
    """
    pass


def test_untbib_to_callnumbers_display():
    """
    Placeholder test.
    """
    pass


def test_untbib_to_callnumbers_normalized():
    """
    Placeholder test.
    """
    pass
