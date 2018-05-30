"""
Tests blacklight.record_converters classes.
"""

import pytest
import re

from blacklight import record_converters
from blacklight.marcfieldset import filters as filt


# FIXTURES AND TEST DATA
# External fixtures used here can be found in
# django/sierra/base/tests/conftest.py:
#    sierra_records_by_recnum_range

pytestmark = pytest.mark.django_db


@pytest.fixture
def in_test_rec():
    """
    Pytest fixture, returns a basic input record for conversions.
    """
    return {
        'author': 'Thomas, Joseph',
        'editor': 'Scott, Robert',
        'title': 'This is a test record : Test record boogaloo',
    }


@pytest.fixture
def to_creators():
    """
    Pytest fixture, returns a basic `to_creators` converter function.
    """
    def _to_creators(rec):
        creators = []
        for key in ('author', 'editor'):
            creator = '{} -- {}'.format(rec[key], key)
            creators.append(creator)
        return creators
    return _to_creators


@pytest.fixture
def to_title():
    """
    Pytest fixture, returns a basic `to_title` converter function.
    """
    def _to_main_title(rec):
        main_title, subtitle = re.split(r'\s*:\s+', (rec['title']))
        return {'main_title': main_title, 'subtitle': subtitle}
    return _to_main_title


@pytest.fixture
def rec_converter(to_creators, to_title):
    """
    Pytest fixture, returns a test RecordConverter object.
    """
    field_converters = {
        'creators': to_creators,
        'title': to_title
    }
    return record_converters.RecordConverter(field_converters)


@pytest.fixture
def bib_authorname_converter():
    """
    Pytest fixture, returns a bib author name converter function.
    """
    def _converter(in_data):
        fieldset = in_data['bib']['marcfields']
        m100 = fieldset.fields_where(filt.tag_equals, '100')[0]
        return m100.get_subfields_as_string()
    return _converter


@pytest.fixture
def bib_title_converter():
    """
    Pytest fixture, returns a bib title converter function.
    """
    def _converter(in_data):
        fieldset = in_data['bib']['marcfields']
        m245 = fieldset.fields_where(filt.tag_equals, '245')[0]
        m245a_str = m245.subfields_where(filt.tag_equals, 'a').get_subfields_as_string()
        return m245a_str.lower()
    return _converter


@pytest.fixture
def item_location_converter():
    """
    Pytest fixture, returns an item location converter function.
    """
    def _converter(in_data):
        item = in_data['item']
        return { 'code': item['location_code'], 'name': item['location_name'] }
    return _converter


@pytest.fixture
def item_status_converter():
    """
    Pytest fixture, returns an item status converter function.
    """
    def _converter(in_data):
        item = in_data['item']
        is_checked_out = bool(item['checkout_date'])
        return { 'code': item['status_code'], 'name': item['status_name'], 'is_checked_out': is_checked_out }
    return _converter


@pytest.fixture
def construct_fullname():
    """
    Pytest fixture, returns a fullname constructor utility function.
    """
    def _construct_fullname(in_data):
        first, last, dates = in_data['forename'], in_data['surname'], in_data['dates']
        firstlast = '{} {}'.format(first, last) if last else first
        fullname = '{} ({})'.format(firstlast, dates) if dates else firstlast
        return fullname
    return _construct_fullname


@pytest.fixture
def solr_author_fullname_search_converter(construct_fullname):
    """
    Pytest fixture, returns a Solr author fullname search converter.
    """
    def _converter(in_data):
        return construct_fullname(in_data['author']).lower()
    return _converter


@pytest.fixture
def solr_author_lastname_search_converter():
    """
    Pytest fixture, returns a Solr author last name search converter.
    """
    def _converter(in_data):
        return in_data['author']['surname'].lower()
    return _converter


@pytest.fixture
def solr_author_fullname_facet_converter(construct_fullname):
    """
    Pytest fixture, returns a Solr author fullname facet converter.
    """
    def _converter(in_data):
        return construct_fullname(in_data['author'])
    return _converter


@pytest.fixture
def test_bib(sierra_records_by_recnum_range):
    """
    Pytest fixture, returns test bib record b4371446.
    """
    return sierra_records_by_recnum_range('b6029459')[0]


@pytest.fixture
def test_untbib():
    """
    Pytest fixture, returns a small pseudo-record, for testing.
    """
    return {
        'author': {
            'forename': 'William',
            'surname': 'Shakespeare',
            'dates': '1564-1616',
        }
    }


@pytest.fixture
def sb2ub_obj(bib_authorname_converter, bib_title_converter, item_location_converter,
              item_status_converter):
    """
    Pytest fixture, returns a test SierraBibToUntbib object.
    """
    return record_converters.SierraBibToUntbib(
        bibfield_map={
            'author': bib_authorname_converter,
            'title': bib_title_converter,
        },
        itemfield_map={
            'location': item_location_converter,
            'status': item_status_converter
        }
    )

@pytest.fixture
def ub2solr_obj(solr_author_fullname_facet_converter, solr_author_lastname_search_converter,
                solr_author_fullname_search_converter):
    """
    Pytest fixture, returns a test UntbibToSolr object.
    """
    return record_converters.UntbibToSolr(
        solrfield_map={
            'author_fullname_facet': solr_author_fullname_facet_converter,
            'author_fullname_search': solr_author_fullname_search_converter,
            'author_lastname_search': solr_author_lastname_search_converter
        }
    )


# TESTS

def test_rc__convert(rec_converter, in_test_rec):
    """
    RecordConverter.convert should return the correct data.
    """
    result = rec_converter.convert(in_test_rec)
    assert result == {
        'creators': ['Thomas, Joseph -- author', 'Scott, Robert -- editor'],
        'title': {
            'main_title': 'This is a test record',
            'subtitle': 'Test record boogaloo'
        }
    }


def test_sierrabibtountbib_convert(sb2ub_obj, test_bib):
    """
    SierraBibToUntbib.convert should return correct data.
    """
    samplebib = sb2ub_obj.convert(test_bib)
    assert samplebib['author'] == 'Shakespeare, William, 1564-1616'
    assert samplebib['title'] == 'catalog api test record 1'
    assert samplebib['items'][0]['location']['code'] == 'test'
    assert samplebib['items'][0]['location']['name'] == 'Testing-do not use'
    assert samplebib['items'][0]['status']['code'] == '-'
    assert samplebib['items'][0]['status']['name'] == 'AVAILABLE'
    assert not samplebib['items'][0]['status']['is_checked_out']
    assert samplebib['items'][1]['status']['code'] == 'w'
    assert samplebib['items'][1]['status']['name'] == 'ONLINE'
    assert not samplebib['items'][1]['status']['is_checked_out']
    assert samplebib['items'][2]['status']['code'] == '-'
    assert samplebib['items'][2]['status']['name'] == 'AVAILABLE'
    assert samplebib['items'][2]['status']['is_checked_out']


def test_untbibtosolr_convert(ub2solr_obj, test_untbib):
    """
    UntbibToSolr.convert should return correct data.
    """
    samplesolr = ub2solr_obj.convert(test_untbib)
    assert samplesolr['author_fullname_facet'] == 'William Shakespeare (1564-1616)'
    assert samplesolr['author_fullname_search'] == 'william shakespeare (1564-1616)'
    assert samplesolr['author_lastname_search'] == 'shakespeare'

