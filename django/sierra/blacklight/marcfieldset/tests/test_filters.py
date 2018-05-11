"""
Tests the marcfieldset filter functions.
"""

import pytest
from blacklight.marcfieldset import filters as filt


# TESTS

@pytest.mark.parametrize('item, tag, expected', [
    ({'tag': '245'}, '245', True),
    ({'tag': '500'}, '245', False),
    ({'tag': 'a'}, 'a', True),
    ({'tag': 'a'}, 'b', False),
])
def test_tagequals(item, tag, expected):
    """
    tag_equals should return True if item['tag'] equals the given
    `tag`.
    """
    assert expected == filt.tag_equals(item, tag)


@pytest.mark.parametrize('item, tags, expected', [
    ({'tag': '245'}, ['245', '500'], True),
    ({'tag': '500'}, ['245', '500'], True),
    ({'tag': '501'}, ['245', '500'], False),
    ({'tag': 'a'}, 'ab', True),
    ({'tag': 'a'}, ['a', 'b'], True),
    ({'tag': 'b'}, 'ab', True),
    ({'tag': 'c'}, 'ab', False),
])
def test_tagin(item, tags, expected):
    """
    tag_in should return True if item['tag'] occurs in the `tags`
    given.
    """
    assert expected == filt.tag_in(item, tags)


@pytest.mark.parametrize('item, regex, expected', [
    ({'tag': '245'}, r'2..', True),
    ({'tag': '245'}, r'24.', True),
    ({'tag': '245'}, r'3..', False),
    ({'tag': 'a'}, r'[a-z]', True),
    ({'tag': '2'}, r'[a-z]', False),
])
def test_tagmatches(item, regex, expected):
    """
    tag_matches should return True if item['tag'] matches the given
    `regex` arg.
    """
    assert expected == filt.tag_matches(item, regex)


@pytest.mark.parametrize('item, data, expected', [
    ({'data': 'Test'}, 'Test', True),
    ({'data': 'Test'}, 'Tes', False),
    ({'data': 'Test'}, 'test', False),
])
def test_dataequals(item, data, expected):
    """
    data_equals should return True if item['data'] exactly matches the
    `data` arg.
    """
    assert expected == filt.data_equals(item, data)


@pytest.mark.parametrize('item, regex, expected', [
    ({'data': 'Test'}, r'^Test$', True),
    ({'data': 'Test'}, r'^Tes$', False),
    ({'data': 'Test'}, r'^Tes', True),
    ({'data': 'Test'}, r'[tT]est', True),
    ({'data': 'Test'}, r'es', True),
])
def test_datamatches(item, regex, expected):
    """
    data_matches should return True if item['data'] matches the given
    `regex` arg.
    """
    assert expected == filt.data_matches(item, regex)


@pytest.mark.parametrize('item, tags, data, expected', [
    ({'tag': 'a', 'data': 'Test'}, 'a', 'Test', True),
    ({'tag': 'a', 'data': 'Test'}, 'a', 'Tes', False),
    ({'tag': 'a', 'data': 'Test'}, 'b', 'Test', False),
    ({'tag': 'a', 'data': 'Test'}, 'ab', 'Test', True),
    ({'tag': 'a', 'data': 'Test'}, 'bc', 'Test', False),
    ({'tag': 'a', 'data': 'Test'}, 'bc', 'Tes', False),
    ({'tag': 'a', 'data': 'Test'}, ['a', 'b'], 'Test', True),
])
def test_taginanddataequals(item, tags, data, expected):
    """
    tag_in_and_data_equals should return True if item['tag'] is in the
    given `tags` AND item['data'] exactly matches the `data` arg.
    """
    assert expected == filt.tag_in_and_data_equals(item, tags, data)


@pytest.mark.parametrize('item, tags, regex, expected', [
    ({'tag': 'a', 'data': 'Test'}, 'a', r'^Test$', True),
    ({'tag': 'a', 'data': 'Test'}, 'a', r'^Tes$', False),
    ({'tag': 'a', 'data': 'Test'}, 'a', r'^Tes', True),
    ({'tag': 'a', 'data': 'Test'}, 'b', r'^Test$', False),
    ({'tag': 'a', 'data': 'Test'}, 'ab', r'Tes', True),
    ({'tag': 'a', 'data': 'Test'}, 'bc', r'Tes', False),
    ({'tag': 'a', 'data': 'Test'}, 'bc', r'^Tes$', False),
    ({'tag': 'a', 'data': 'Test'}, ['a', 'b'], r'Test', True),
])
def test_taginanddatamatches(item, tags, regex, expected):
    """
    tag_in_and_data_matches should return True if item['tag'] is in the
    given `tags` AND item['data'] matches the given `regex` arg.
    """
    assert expected == filt.tag_in_and_data_matches(item, tags, regex)


@pytest.mark.parametrize('field, indicator_num, value, expected', [
    ({'indicators': [' ', '1']}, 1, ' ', True),
    ({'indicators': [' ', '1']}, 2, '1', True),
    ({'indicators': [' ', '1']}, 1, '1', False),
    ({'indicators': [' ', '1']}, 2, ' ', False),
    ({'indicators': [None, None]}, 1, ' ', False),
    ({'indicators': [None, None]}, 2, ' ', False),
])
def test_indicatorequals(field, indicator_num, value, expected):
    """
    indicator_equals should return True if field['indicators'] has a
    first or second indicator (`indicator_num` 1 or 2) exactly matching
    the given `value` arg.
    """
    assert expected == filt.indicator_equals(field, indicator_num, value)


@pytest.mark.parametrize('field, indicator_num, values, expected', [
    ({'indicators': [' ', '1']}, 1, ' ', True),
    ({'indicators': [' ', '1']}, 1, [' ', '1'], True),
    ({'indicators': [' ', '1']}, 1, ' 1', True),
    ({'indicators': [' ', '1']}, 1, '12', False),
    ({'indicators': [' ', '1']}, 2, '1', True),
    ({'indicators': [' ', '1']}, 2, '21', True),
    ({'indicators': [' ', '1']}, 2, ' ', False),
    ({'indicators': [' ', '1']}, 2, ' 2', False),
    ({'indicators': [None, None]}, 1, ' ', False),
    ({'indicators': [None, None]}, 1, ' 1', False),
    ({'indicators': [None, None]}, 2, ' ', False),
    ({'indicators': [None, None]}, 2, ' 1', False),
])
def test_indicatorin(field, indicator_num, values, expected):
    """
    indicator_in should return True if field['indicators'] has a first
    or second indicator (`indicator_num` 1 or 2) with a value in the
    given `values` list.
    """
    assert expected == filt.indicator_in(field, indicator_num, values)


@pytest.mark.parametrize('field, sf_test, args, kwargs, expected', [
    ({'subfields': [{'tag': 'a', 'data': 'Test'}]}, filt.tag_equals, ['a'],
     {}, True),
    ({'subfields': [{'tag': 'a', 'data': 'Test'}]}, filt.tag_equals, ['b'],
     {}, False),
    ({'subfields': [{'tag': 'a', 'data': 'Test'},
                    {'tag': 'b', 'data': 'Test'}]}, filt.tag_equals, ['b'],
     {}, True),
    ({'subfields': [{'tag': 'a', 'data': 'Test'},
                    {'tag': 'b', 'data': 'Test'}]}, filt.tag_equals, ['c'],
     {}, False),
])
def test_fieldhasanysubfieldswhere(field, sf_test, args, kwargs, expected):
    """
    field_has_any_subfield_where should return True if
    field['subfields'] has ANY subfields that return True for the given
    `sf_test` function.
    """
    res = filt.field_has_any_subfields_where(field, sf_test, *args, **kwargs)
    assert expected == res

