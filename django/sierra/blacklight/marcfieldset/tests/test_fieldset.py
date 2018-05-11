"""
Tests the marcfieldset Field and Fieldset classes.
"""

import re
import copy

import pytest
from blacklight import marcfieldset as mfs


# FIXTURES AND TEST DATA

@pytest.fixture
def leader():
    """
    Pytest fixture, returns a MARC leader field.
    """
    return mfs.Field({
        'tag': 'LDR',
        'data': 'test leader data',
        'indicators': [None, None],
        'subfields': [],
        'occurrence': 0,
    })


@pytest.fixture
def controlfield():
    """
    Pytest fixture, returns a MARC control field.
    """
    return mfs.Field({
        'tag': '007',
        'data': 'test 007 data',
        'indicators': [None, None],
        'subfields': [],
        'occurrence': 0,
    })


@pytest.fixture
def m050():
    """
    Pytest fixture, returns a MARC 050 Field.

    Features repeated subfield "a".
    """
    return mfs.Field({
        'tag': '050',
        'indicators': [' ', ' '],
        'subfields': [
            {
                'tag': 'a',
                'data': 'TEST'
            },
            {
                'tag': 'a',
                'data': '1'
            }
        ],
        'occurrence': 0,
    })


@pytest.fixture
def m245():
    """
    Pytest fixture, returns a MARC 245 Field.

    Features indicator values and multiple different subfields.
    """
    return mfs.Field({
        'tag': '245',
        'indicators': ['1', '4'],
        'subfields': [
            {
                'tag': 'a',
                'data': 'The test title'
            },
            {
                'tag': 'h',
                'data': '[microform] :'
            },
            {
                'tag': 'b',
                'data': 'Test subtitle /'
            },
            {
                'tag': 'c',
                'data': 'by First Last.'
            }
        ],
        'occurrence': 0,
    })


@pytest.fixture
def m500_1():
    """
    Pytest fixture, returns a MARC 500 Field.

    (For tests involving repeated fields.)
    """
    return mfs.Field({
        'tag': '500',
        'indicators': [' ', ' '],
        'subfields': [
            {
                'tag': 'a',
                'data': 'Test 500, repeated field, 1.'
            }
        ],
        'occurrence': 0,
    })


@pytest.fixture
def m500_2():
    """
    Pytest fixture, returns a MARC 500 Field.

    (For tests involving repeated fields.)
    """
    return mfs.Field({
        'tag': '500',
        'indicators': [' ', ' '],
        'subfields': [
            {
                'tag': 'a',
                'data': 'Test 500, repeated field, 2.'
            }
        ],
        'occurrence': 1,
    })


@pytest.fixture
def m505():
    """
    Pytest fixture, returns a MARC 505 Field.

    (For tests involving field tag pattern r'5..'.)
    """
    return mfs.Field({
        'tag': '505',
        'indicators': [' ', ' '],
        'subfields': [
            {
                'tag': 'a',
                'data': 'Test formatted-contents note.'
            },
        ],
        'occurrence': 0,
    })


@pytest.fixture
def m509():
    """
    Pytest fixture, returns a MARC 509 Field.

    Features repeated subfield a AND multiple subfield tags.
    """
    return mfs.Field({
        'tag': '509',
        'indicators': [' ', ' '],
        'subfields': [
            {
                'tag': 'a',
                'data': 'Test 509.'
            },
            {
                'tag': 'a',
                'data': 'Test 509 repeated subfield a.'
            },
            {
                'tag': 'c',
                'data': 'Test 509 subfield c.'
            },
        ],
        'occurrence': 0,
    })


@pytest.fixture
def m856():
    """
    Pytest fixture, returns a MARC 856 Field.

    Features multiple subfield tags, and a first sf that is not 'a'.
    """
    return mfs.Field({
        'tag': '856',
        'indicators': [' ', ' '],
        'subfields': [
            {
                'tag': 'z',
                'data': 'View image of this item (side view).'
            },
            {
                'tag': 'u',
                'data': 'https://www.example.com/side'
            },
        ],
        'occurrence': 0,
    })


@pytest.fixture
def cfields(leader, controlfield):
    """
    Pytest fixture, returns a Fieldset of control fields.
    """
    return mfs.Fieldset([leader, controlfield])


@pytest.fixture
def m500s(m500_1, m500_2):
    """
    Pytest fixture, returns a Fieldset of 500 fields.
    """
    return mfs.Fieldset([m500_1, m500_2])


@pytest.fixture
def m5xxes(m500s, m505, m509):
    """
    Pytest fixture, returns a Fieldset of all 5XX fields.
    """
    fields = m500s
    fields.extend(mfs.Fieldset([m505, m509]))
    return fields


@pytest.fixture
def vfields(m050, m245, m5xxes, m856):
    """
    Pytest fixture, returns a Fieldset of several varfields.
    """
    fields = mfs.Fieldset([m050, m245])
    fields.extend(m5xxes)
    fields.append(m856)
    return fields


@pytest.fixture
def allfields(cfields, vfields):
    """
    Pytest fixture, returns a Fieldset of all available test fields.
    """
    fields = cfields
    fields.extend(vfields)
    return fields

@pytest.fixture
def out_of_order(m500_1, m500_2, m505, m509):
    """
    Pytest fixture, returns a Fieldset with fields out of order.
    """
    return mfs.Fieldset([m505, m500_2, m509, m500_1])


@pytest.fixture
def tag_equals():
    """
    Pytest fixture, returns a `tag_equals` filter function.

    This is identical to the marcfieldset.filters.tag_equals function,
    but it seems like a good idea to replicate it here to ensure that
    tests are independent. The actual filters have their own tests.
    """
    def _tag_equals(item, tag):
        return item['tag'] == tag
    return _tag_equals


@pytest.fixture
def replace():
    """
    Pytest fixture, returns a `replace` function.

    Use this in `replace_subfield_data` tests.
    """
    def _replace(data):
        return '{} (r)'.format(data)
    return _replace


@pytest.fixture
def match_repl():
    """
    Pytest fixture, returns a match and replace function.

    Use this as the `do_for_each` function in do_for_each_subfield
    tests.
    """
    def _match_repl(sf):
        match_regex = r'\s*\[(.*)\]\s*'
        if sf['tag'] == 'h':
            matches = re.search(match_regex, sf['data'])
            if matches:
                sf['data'] = re.sub(match_regex, '', sf['data'])
                return matches.group(1)
    return _match_repl


@pytest.fixture
def sort_key():
    """
    Pytest fixture, returns a sort_key function.

    Use this to test Fieldset.get_sorted.
    """
    def _sort_key(item):
        return [item['tag'], item['occurrence']]
    return _sort_key


@pytest.fixture
def same_order():
    """
    Pytest fixture, returns a `same_order` utility function.

    Use this function to test whether a list of things that is a subset
    of things from another list has items in the same order they occur
    in the parent list. This is probably a wonky way to do this, but
    it works.
    """
    def _same_order(subset_list, parent_list):
        subset_list = [i for i in subset_list]
        for p_item in parent_list:
            try:
                sub_item = subset_list[0]
            except IndexError:
                break
            if sub_item == p_item:
                subset_list.pop(0)
        return not subset_list
    return _same_order


# TESTS

def test_field_subfieldswhere__control_field(controlfield, tag_equals):
    """
    Field.subfields_where should return a Field that has no subfields,
    like a control field, without erroring or altering the `subfields`
    element.
    """
    result = controlfield.subfields_where(tag_equals, 'a')
    assert not controlfield['subfields']
    assert not result['subfields']


def test_field_subfieldswhere__selects_single_sf(m509, tag_equals):
    """
    Field.subfields_where should return a Field with a single subfield
    if only one subfield matches the test criteria.
    """
    result = m509.subfields_where(tag_equals, 'c')
    assert len(result['subfields']) == 1
    assert result['subfields'][0]['tag'] == 'c'


def test_field_subfieldswhere__selects_multi_sfs(m509, tag_equals):
    """
    Field.subfields_where should return a Field with multiple subfields
    when multiple subfields match the test criteria.
    """
    result = m509.subfields_where(tag_equals, 'a')
    assert len(result['subfields']) == 2
    assert all([sub['tag'] == 'a' for sub in result['subfields']])


def test_field_subfieldswhere__selects_nothing(m509, tag_equals):
    """
    Field.subfields_where should return a Field with no subfields if
    no subfields match the test criteria.
    """
    result = m509.subfields_where(tag_equals, 'k')
    assert not result['subfields']


def test_field_subfieldswhere__creates_copy(m505, tag_equals):
    """
    Field.subfields_where should create and return a copy of the parent
    Field object.
    """
    result = m505.subfields_where(tag_equals, 'a')
    assert len(result['subfields']) == len(m505['subfields'])
    assert result is not m505


def test_field_subfieldswhere__subfield_order(m509, tag_equals, same_order):
    """
    Fields.subfields_where should return a Field with subfields in the
    same order they appear in the parent object.
    """
    result = m509.subfields_where(tag_equals, 'a')
    res_data = [sub['data'] for sub in result['subfields']]
    org_data = [sub['data'] for sub in m509['subfields']]
    assert same_order(res_data, org_data)


def test_field_subfieldswherenot__control_field(controlfield, tag_equals):
    """
    Field.subfields_where_not should return a Field that has no
    subfields, like a control field, without erroring or altering the
    `subfields` element.
    """
    result = controlfield.subfields_where_not(tag_equals, 'a')
    assert not controlfield['subfields']
    assert not result['subfields']


def test_field_subfieldswherenot__selects_single_sf(m509, tag_equals):
    """
    Field.subfields_where_not should return a Field with a single
    subfield if only one subfield does not match the test criteria.
    """
    result = m509.subfields_where_not(tag_equals, 'a')
    assert len(result['subfields']) == 1
    assert result['subfields'][0]['tag'] == 'c'


def test_field_subfieldswherenot__selects_multi_sfs(m509, tag_equals):
    """
    Field.subfields_where_not should return a Field with a multiple
    subfields if multiple subfield do not match the test criteria.
    """
    result = m509.subfields_where_not(tag_equals, 'c')
    assert len(result['subfields']) == 2
    assert all([sub['tag'] == 'a' for sub in result['subfields']])


def test_field_subfieldswherenot__selects_nothing(m505, tag_equals):
    """
    Field.subfields_where_not should return a Field with no subfields
    if all subfields match the test criteria.
    """
    result = m505.subfields_where_not(tag_equals, 'a')
    assert not result['subfields']


def test_field_subfieldswherenot__creates_copy(m509, tag_equals):
    """
    Field.subfields_where_not should create and return a copy of
    the parent Field object.
    """
    result = m509.subfields_where_not(tag_equals, 'k')
    assert len(result['subfields']) == len(m509['subfields'])
    assert result is not m509


def test_field_subfieldswherenot__subfield_order(m245, tag_equals, same_order):
    """
    Field.subfields_where_not should return a Field with subfields in
    the same order they appear in the parent object.
    """
    result = m245.subfields_where_not(tag_equals, 'h')
    res_data = [sub['data'] for sub in result['subfields']]
    org_data = [sub['data'] for sub in m245['subfields']]
    assert same_order(res_data, org_data)


def test_field_replacesubfielddata__control_field(controlfield, replace):
    """
    Field.replace_subfield_data should do nothing when called on a
    field with no subfield data, like a control field.
    """
    result = controlfield.replace_subfield_data(replace)
    assert result == controlfield


def test_field_replacesubfielddata__repl_data_in_ret_obj(m245, replace):
    """
    Field.replace_subfield_data should replace subfield data in EACH
    subfield in the return object.
    """
    org_data = [sf['data'] for sf in m245['subfields']]
    result = m245.replace_subfield_data(replace)
    res_data = [sf['data'] for sf in result['subfields']]
    assert all([res_data[i] == '{} (r)'.format(odata)
                for i, odata in enumerate(org_data)])


def test_field_replacesubfielddata__repl_data_in_org_obj(m245, replace):
    """
    Field.replace_subfield_data should replace subfield data in EACH
    subfield in the ORIGINAL object.
    """
    org_data = [sf['data'] for sf in m245['subfields']]
    result = m245.replace_subfield_data(replace)
    res_data = [sf['data'] for sf in m245['subfields']]
    assert all([res_data[i] == '{} (r)'.format(odata)
                for i, odata in enumerate(org_data)])


def test_field_replacesubfielddata__repl_filtered_data(m245, tag_equals,
                                                       replace):
    """
    Field.replace_subfield_data should replace data only on the
    subfields that match the test criteria when used with a filtered
    set of subfields (e.g. via Field.subfields_where).
    """
    expected = []
    for sf in m245['subfields']:
        if sf['tag'] == 'h':
            expected.append('{} (r)'.format(sf['data']))
        else:
            expected.append(sf['data'])

    m245.subfields_where(tag_equals, 'h').replace_subfield_data(replace)
    assert [sf['data'] for sf in m245['subfields']] == expected


def test_field_doforeachsubfield__control_field(controlfield, match_repl):
    """
    Field.do_for_each_subfield should do nothing when called on a
    field with no subfield data, like a control field.
    """
    result = controlfield.do_for_each_subfield(match_repl)
    assert not result


def test_field_doforeachsubfield__returns_correct_data(m245, match_repl):
    """
    Field.do_for_each_subfield should run the provided function on
    EACH subfield in the Field object, and return the correct results.
    """
    expected = []
    for sf in m245['subfields']:
        exp = {'before': {'tag': sf['tag'], 'data': sf['data']}}
        if sf['tag'] == 'h':
            exp['return_value'] = 'microform'
            exp['after'] = {'tag': 'h', 'data': ':'}
        else:
            exp['return_value'] = None
            exp['after'] = {'tag': sf['tag'], 'data': sf['data']}
        expected.append(exp)
    result = m245.do_for_each_subfield(match_repl)
    assert result == expected


def test_field_doforeachsubfield__replacing_data(m245, match_repl):
    """
    When running Field.do_for_each_subfield, if the `do_for_each`
    function modifies the subfield dict that is passed to it, that
    modifies the data in the original Field object. This is intended
    behavior.
    """
    subfield_h_before = [sf['data'] for sf in m245['subfields']
                         if sf['tag'] == 'h'][0]
    m245.do_for_each_subfield(match_repl)
    subfield_h_after = [sf['data'] for sf in m245['subfields']
                         if sf['tag'] == 'h'][0]
    assert subfield_h_before == '[microform] :'
    assert subfield_h_after == ':'


def test_field_getsubfieldsasstring__control_field(controlfield):
    """
    Field.get_subfields_as_string should return a blank string when
    called on a field with no subfield data, like a control field.
    """
    result = controlfield.get_subfields_as_string(' ')
    assert result == ''


def test_field_getsubfieldsasstring__gets_all_subfields(m245):
    """
    Field.get_subfields_as_string should return all subfields joined
    together as one string, in the correct order, using the supplied
    delimiter string.
    """
    expected =  'The test title [microform] : Test subtitle / by First Last.'
    result = m245.get_subfields_as_string(' ')
    assert result == expected


def test_field_getsubfieldsasstring__gets_filtered_subfields(m245, tag_equals):
    """
    Field.get_subfields_as_string should return subfields joined
    together as one string, based on the filtered subfield set.
    """
    expected =  'The test title'
    result = m245.subfields_where(tag_equals, 'a').get_subfields_as_string(' ')
    assert result == expected


def test_fieldset_getslice__returns_fieldset(allfields):
    """
    Slicing a Fieldset should return a Fieldset object.

    (Tests __getslice__.)
    """
    assert isinstance(allfields[1:], mfs.Fieldset)


def test_fieldset_add__returns_fieldset(cfields, vfields):
    """
    Adding/concatenating two fieldsets should return another Fieldset.

    (Tests __add__.)
    """
    assert isinstance(cfields + vfields, mfs.Fieldset)


def test_fieldset_mul__returns_fieldset(cfields):
    """
    Multiplying a Fieldset should return another Fieldset.
    """
    assert isinstance(cfields * 2, mfs.Fieldset)


def test_fieldset_fieldswhere__selects_single_field(allfields, tag_equals):
    """
    Fieldset.fields_where should select a single field when the test
    criteria matches one field.
    """
    result = allfields.fields_where(tag_equals, '245')
    assert len(result) == 1
    assert result[0]['tag'] == '245'


def test_fieldset_fieldswhere__selects_mult_fields(allfields, tag_equals):
    """
    Fieldset.fields_where should select multiple fields when the test
    criteria matches multiple fields.
    """
    result = allfields.fields_where(tag_equals, '500')
    assert len(result) == 2
    assert all([r['tag'] == '500' for r in result])


def test_fieldset_fieldswhere__selects_no_fields(allfields, tag_equals):
    """
    Fieldset.fields_where should select no fields (returning an empty
    Fieldset) when the test criteria matches nothing.
    """
    result = allfields.fields_where(tag_equals, 'none')
    assert not result
    assert isinstance(result, mfs.Fieldset)


def test_fieldset_fieldswherenot__selects_single_field(cfields, tag_equals):
    """
    Fieldset.fields_where_not should select a single field when the test
    criteria matches all but one field.
    """
    result = cfields.fields_where_not(tag_equals, 'LDR')
    assert len(result) == 1
    assert result[0]['tag'] == '007'


def test_fieldset_fieldswherenot__selects_mult_fields(allfields, tag_equals):
    """
    Fieldset.fields_where should select multiple fields when the test
    criteria does not match multiple fields.
    """
    result = allfields.fields_where_not(tag_equals, '245')
    assert len(result) > 1
    assert '245' not in [r['tag'] for r in result]


def test_fieldset_fieldswherenot__selects_no_fields(m500s, tag_equals):
    """
    Fieldset.fields_where should select no fields (returning an empty
    Fieldset) when the test criteria matches all fields.
    """
    result = m500s.fields_where_not(tag_equals, '500')
    assert not result
    assert isinstance(result, mfs.Fieldset)


def test_fieldset_subfieldswhere(allfields, tag_equals):
    """
    Calling Fieldset.subfields_where should be the equivalent of
    calling `subfields_where` on each Field object and returning the
    resulting list of Fields.
    """
    exp = [f.subfields_where(tag_equals, 'a') for f in allfields]
    result = allfields.subfields_where(tag_equals, 'a')
    assert mfs.Fieldset(exp) == result


def test_fieldset_subfieldswherenot(allfields, tag_equals):
    """
    Calling Fieldset.subfields_where_not should be the equivalent of
    calling `subfields_where` on each Field object and returning the
    resulting list of Fields as a fieldset.
    """
    exp = [f.subfields_where_not(tag_equals, 'a') for f in allfields]
    result = allfields.subfields_where_not(tag_equals, 'a')
    assert mfs.Fieldset(exp) == result


def test_fieldset_replacesubfielddata(allfields, replace):
    """
    Calling Fieldset.replace_subfield_data should be the equivalent of
    calling `replace_subfield_data` on each Field object and returning
    the resulting list of Fields as a fieldset.
    """
    original_fields = copy.deepcopy(allfields)
    exp = [f.replace_subfield_data(replace) for f in allfields]
    result = original_fields.replace_subfield_data(replace)
    assert mfs.Fieldset(exp) == result


def test_fieldset_doforeachsubfield(allfields, match_repl):
    """
    Calling Fieldset.do_for_each_subfield should be the equivalent of
    calling `do_for_each_subfield` on each Field object and returning
    the list of results, one for each run.
    """
    original_fields = copy.deepcopy(allfields)
    exp = [f.do_for_each_subfield(match_repl) for f in allfields]
    result = original_fields.do_for_each_subfield(match_repl)
    assert exp == result


def test_fieldset_getsubfieldsasstrings(allfields):
    """
    Calling Fieldset.get_subfields_as_strings should be the equivalent
    of calling `get_subfields_as_string` on each Field object and
    returning the list of strings.
    """
    exp = [f.get_subfields_as_string(' ') for f in allfields]
    result = allfields.get_subfields_as_strings(' ')
    assert exp == result


def test_fieldset_getsorted__sort_by_element_name(out_of_order, sort_key):
    """
    Fieldset.get_sorted should return a Fieldset sorted by the provided
    list of element names, if `element` is specified.
    """
    result = out_of_order.get_sorted(elements=['tag', 'occurrence'])
    assert result == sorted(out_of_order, key=sort_key)


def test_fieldset_getsorted__sort_by_key_function(out_of_order, sort_key):
    """
    Fieldset.get_sorted should return a Fieldset sorted by the provided
    list of element names, if `element` is specified.
    """
    result = out_of_order.get_sorted(key=sort_key)
    assert result == sorted(out_of_order, key=sort_key)


def test_fieldset_getsorted__sort_reverse(out_of_order, sort_key):
    """
    Fieldset.get_sorted should reverse the sort order if the `reverse`
    argument is True.
    """
    result = out_of_order.get_sorted(key=sort_key, reverse=True)
    assert result == sorted(out_of_order, key=sort_key, reverse=True)


def test_fieldset_getsorted__ignore_nonexistent_element_name(out_of_order,
                                                             sort_key):
    """
    Fieldset.get_sorted should ignore any element names passed via the
    `elements` argument that one or more Field objects don't have.
    """
    result = out_of_order.get_sorted(elements=['tag', 'what', 'occurrence'])
    assert result == sorted(out_of_order, key=sort_key)
