"""
Contains Sierra field data conversion functions.
"""

from __future__ import unicode_literals
import logging

import pycallnumber as pycn

from blacklight.marcfieldset import filters as filt
from blacklight import parsers

# set up logger, for debugging
logger = logging.getLogger('sierra.custom')


# Conversion functions

def sierrabib_to_record_id(in_data):
    """
    Get the record ID (III record number) from the sierrabib.
    """
    fixedfields = in_data['bib']['fixedfields']
    return fixedfields['record_id']


def sierrabib_to_person_author(in_data):
    """
    Convert personal author data (MARC 100) to untbib `person_author`.
    """
    fixedfields, fieldset = in_data['bib']['fixedfields'], in_data['bib']['marcfields']
    out_data = {
        'forename': '',
        'surname': '',
        'family_name': '',
        'fuller_form_of_name': '',
        'titles': [],
        'start_date': '',
        'start_date_qualifier': '',
        'end_date': '',
        'end_date_qualifier': '',
        'date_type': '',
        'full_dates': '',
        'relation_to_work': '',
        'attribution_qualifer': '',
        'affiliation': '',
        'authorized_heading': '',
    }
    try:
        person_author_field = fieldset.fields_where(filt.tag_equals, '100')[0]
    except IndexError:
        return None
    out_data.update(parsers.person_name(person_author_field))
    out_data.update(parsers.person_dates(person_author_field))
    out_data['titles'] = parsers.person_titles(person_author_field)
    return out_data


def sierrabib_to_contributors(in_data):
    """
    This is a placeholder for contributors.
    """
    fixedfields, fieldset = in_data['bib']['fixedfields'], in_data['bib']['marcfields']
    out_data = [{'name': 'PLACEHOLDER'}]
    return out_data


def itemrecord_to_barcode(in_data):
    """
    Get item barcode data.
    """
    item = in_data['item']
    try:
        return item['barcodes'][0]
    except IndexError:
        return None


def itemrecord_to_location(in_data):
    """
    Get item location data.
    """
    item = in_data['item']
    return {'code': item['location_code'], 'name': item['location_name']}


def itemrecord_to_callnumber(in_data):
    """
    Get item callnumber data.
    """
    item = in_data['item']
    return {'display': item['callnumber'], 'type': item['callnumber_type']}


def untbib_to_id(untbib):
    """
    Get the record_id from the untbib.
    """
    return untbib['record_id']


def untbib_to_person_author_search_fullname_forms(untbib):
    """
    Convert untbib.person_author name to fullname forms for searching.
    """
    author = untbib['person_author']
    if author is None:
        return []
    straight = parsers.untbib_person_get_name_straight(author)
    inverted = parsers.untbib_person_get_name_inverted(author)
    full = parsers.untbib_person_get_fullname(author)
    return [straight, inverted, full]


def untbib_to_person_author_search_bestname(untbib):
    """
    Convert untbib.person_author name to the best name for searching.
    """
    author = untbib['person_author']
    if author is None:
        return ''
    if author['surname']:
        best_name = author['surname']
    else:
        best_name = '{}{}'.format(author['forename'], ' '.join(author['titles']))
    return best_name


def untbib_to_person_author_display(untbib):
    """
    Format untbib.person_author name for display.
    """
    author = untbib['person_author']
    if author is None:
        return ''
    fullname = parsers.untbib_person_get_fullname(author)
    return fullname


def untbib_to_person_author_facet(untbib):
    """
    Format untbib.person_author name for faceting.
    """
    author = untbib['person_author']
    if author is None:
        return ''
    name = parsers.untbib_person_get_name_inverted(author)
    name_with_dates = '{} ({})'.format(name, author['full_dates']) if author['full_dates'] else name
    return name_with_dates


def untbib_to_callnumbers_display(untbib):
    """
    Format untbib item callnumbers for display.
    """
    callnumbers = []
    for item in untbib['items']:
        if item['callnumber']['display']:
            callnumbers.append(item['callnumber']['display'])
        else:
            callnumbers.append('')
    return callnumbers


def untbib_to_callnumbers_normalized(untbib):
    """
    Normalize untbib item callnumbers.
    """
    callnumbers = []
    for item in untbib['items']:
        if item['callnumber']['display']:
            callnumbers.append(pycn.callnumber(item['callnumber']['display'].strip()).for_sort())
        else:
            callnumbers.append('')
    return callnumbers

