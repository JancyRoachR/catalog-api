"""
Tests the sierritemstractor data extraction functions.
"""

import re

import pytest
from blacklight import sierraitemstractor as si


# FIXTURES AND TEST DATA
# External fixtures used here can be found in
# django/sierra/base/tests/conftest.py:
#    sierra_records_by_recnum_range

pytestmark = pytest.mark.django_db

@pytest.fixture
def item(sierra_records_by_recnum_range):
    """
    Pytest fixture, returns test item record i5942962.
    """
    return sierra_records_by_recnum_range('i5942962')[0]


@pytest.fixture
def item_without_local_cn(sierra_records_by_recnum_range):
    """
    Pytest fixture, returns test item record i5942970.
    """
    return sierra_records_by_recnum_range('i5942970')[0]


@pytest.fixture
def item_checked_out(sierra_records_by_recnum_range):
    """
    Pytest fixture, returns test item record i5942982.
    """
    return sierra_records_by_recnum_range('i5942982')[0]


# TESTS


def test_extractcallnumber_returns_correct_item_callnumber(item):
    """
    extract_callnumber should return the item call number if there is a
    call number associated with the item.
    """
    assert si.extract_callnumber(item) == {'callnumber': 'Test Call Number 12345', 'callnumber_type': 'lc'}


def test_extractcallnumber_returns_correct_bib_callnumber(item_without_local_cn):
    """
    extract_callnumber should return the bib call number if there is no
    call number associated with the item.
    """
    assert si.extract_callnumber(item_without_local_cn) == {'callnumber': 'AB 1234568 Test', 'callnumber_type': 'lc'}


def test_extractcheckoutinfo_returns_correct_info_for_checkedout_item(item_checked_out):
    """
    extract_checkout_info should return checkout information for an
    item that is currently checked out.
    """
    info = si.extract_checkout_info(item_checked_out)
    assert info['due_date'].year == 2018
    assert info['checkout_date'].year == 2018
    assert info['overdue_date'] == None
    assert info['recall_date'] == None
    assert info['loan_rule'] == 22
    assert info['renewal_count'] == 0 
    assert info['overdue_count'] == 0


def test_extractcheckoutinfo_returns_correct_info_for_not_checkedout_item(item):
    """
    extract_checkout_info should return an empty dict for an item that
    is currently not checked out.
    """
    info = si.extract_checkout_info(item)
    assert info == {}


def test_extractfixedfields_returns_correct_data(item):
    """
    extract_fixedfields should return fixed field data for the provided
    item.
    """
    fields = si.extract_fixedfields(item)
    assert fields['record_id'] == 'i5942962'
    assert fields['date_created'].year == 2018
    assert fields['date_last_updated'].year == 2018
    assert fields['copy_number'] == 1
    assert fields['last_checkin'].year == 2018
    assert fields['location_code'] == 'test'
    assert fields['location_name'] == 'Testing-do not use'
    assert fields['gift_stats'] == 20
    assert fields['suppress_code'] == 's'
    assert fields['last_checkin_stat_group'] == 310
    assert fields['last_checkout_stat_group'] == 310
    assert fields['status_code'] == '-'
    assert fields['status_name'] == 'AVAILABLE'
    assert fields['itype_code'] == 1
    assert fields['itype_name'] == 'Circulating Materials'
    assert fields['price'] == 5.00
    assert fields['checkout_total'] == 1
    assert fields['last_ytd_checkout_total'] == 0
    assert fields['ytd_checkout_total'] == 1
    assert fields['internal_use_count'] == 0
    assert fields['copy_use_count'] == 0
    assert fields['iuse3_count'] == 10
    assert fields['imessage_code'] == '-'
    assert fields['opac_message_code'] == '-'


def test_extractvarfields_returns_correct_data(item):
    """
    extract_varfields should return variable field data for the
    provided item.
    """
    fields = si.extract_varfields(item)
    assert fields['barcodes'] == ['9999999999']
    assert fields['volumes'] == ['Vol 26']
    assert fields['messages'] == ['This is a test message.']
    assert fields['x_notes'] == ['This is a test X note.']
    assert fields['n_notes'] == ['Another test N note, just for kicks.', 'This is a test N note.']
    assert fields['public_item_notes'] == ['This is a public item note. Hello!']


def test_extractvarfields_returns_empty_lists(item_checked_out):
    """
    extract_varfields should return empty lists for variable-length
    fields that have no data.
    """
    fields = si.extract_varfields(item_checked_out)
    assert True


def test_extract_works(item):
    """
    Just a sanity check to make sure the `extract` function works. It
    should run and return data without raising errors. It calls the
    other functions we've already tested, so no need for exhaustive
    tests.
    """
    fields = si.extract(item)
    assert fields['record_id'] == 'i5942962'
    assert fields['due_date'] == None
    assert fields['barcodes'] == ['9999999999']
    assert fields['callnumber'] == 'Test Call Number 12345'

