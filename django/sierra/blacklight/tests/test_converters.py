"""
Tests the blacklight.converters functions and RecordConverter class.
"""

import pytest
import re

from blacklight import converters


# FIXTURES AND TEST DATA
@pytest.fixture
def in_rec():
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
    def _to_creators(rec, parsers):
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
    def _to_main_title(rec, parsers):
        main_title, subtitle = parsers.title(rec['title'])
        return {'main_title': main_title, 'subtitle': subtitle}
    return _to_main_title

@pytest.fixture
def title():
    """
    Pytest fixture, returns a simple title parsing function.
    """
    def _title(in_title):
        return re.split(r'\s*:\s+', in_title)
    return _title


@pytest.fixture
def rec_converter(to_creators, to_title, title):
    """
    Pytest fixture, returns a test RecordConverter object.
    """
    field_converters = {
        'creators': to_creators,
        'title': to_title
    }
    parsers = {
        'title': title
    }
    return converters.RecordConverter(field_converters, parsers)


# TESTS

def test_rc__convert(rec_converter, in_rec):
    """
    RecordConverter.convert should return the correct data.
    """
    result = rec_converter.convert(in_rec)
    assert result == {
        'creators': ['Thomas, Joseph -- author', 'Scott, Robert -- editor'],
        'title': {
            'main_title': 'This is a test record',
            'subtitle': 'Test record boogaloo'
        }
    }
