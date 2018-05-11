"""
Use filter functions to filter fields and subfields in fieldsets.

Each filter takes the following arguments.

    * The current item in the list of things you're filtering. This
      might be a Field object or a subfield dictionary, or either.

    * Any additional user-supplied arguments needed for the filter.

The filter should return a boolean value indicating whether the item
(field or subfield) matches the filter.
"""

import re


# Tag filters can apply either to subfields OR fields. (Filter by
# MARC field tag or subfield tag.)

def tag_equals(item, tag):
    """
    True if item['tag'] exactly matches the `tag` arg.
    """
    return item['tag'] == tag


def tag_in(item, tags):
    """
    True if item['tag'] occurs in the list of `tags` given.
    """
    return item['tag'] in tags


def tag_matches(item, regex):
    """
    True if item['tag'] matches the given `regex` arg.
    """
    return bool(re.search(regex, item['tag']))


# Data filters apply to things with `data` elements, mostly subfields.
# You could use them for the control fields (001-009). You'll get a
# KeyError if you try to use them with non-control fields.

def data_equals(item, data):
    """
    True if item['data'] exactly matches the `data` arg.
    """
    return item['data'] == data


def data_matches(item, regex):
    """
    True if item['data'] matches the given `regex` arg.
    """
    return bool(re.search(regex, item['data']))


def tag_in_and_data_equals(item, tags, data):
    """
    True if item['tag'] is in the given `tags` AND item['data'] exactly
    matches the `data` arg.
    """
    return tag_in(item, tags) and data_equals(item, data)


def tag_in_and_data_matches(item, tags, regex):
    """
    True if item['tag'] is in the given `tags` AND item['data'] matches
    the given `regex` arg.
    """
    return tag_in(item, tags) and data_matches(item, regex)


# Indicator filters only work with fields.

def indicator_equals(field, indicator_num, value):
    """
    True if field['indicators'] has a first or second indicator
    (`indicator_num` 1 or 2) exactly matching the given `value` arg.
    """
    return field['indicators'][indicator_num-1] == value


def indicator_in(field, indicator_num, values):
    """
    True if field['indicators'] has a first or second indicator
    (`indicator_num` 1 or 2) with a value in the given `values` list.
    """
    try:
        return field['indicators'][indicator_num-1] in values
    except TypeError:
        return False


# The below filters are used to filter fields based on what subfield
# content they have.
# Example: fieldset.where(field_has_any_subfields_where, tag_equals, 'a')
# filters a list of fields to ONLY the fields that have at least one
# subfield a.

def field_has_any_subfields_where(field, sf_test, *args, **kwargs):
    """
    True if field['subfields'] has ANY subfields that return True for
    the given `sf_test` function.
    """
    return any([sf_test(sf, *args, **kwargs) for sf in field['subfields']])
