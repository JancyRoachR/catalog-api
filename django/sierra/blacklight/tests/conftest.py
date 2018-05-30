"""
Contains pytest fixtures shared by Catalog API blacklight app
"""

import pytest

from blacklight import marcfieldset


# External fixtures used below can be found in
# django/sierra/base/tests/conftest.py:
#    new_exporter, export_records, delete_records, solr_conn,
#    solr_search

@pytest.fixture
def export_to_solr(new_exporter, export_records, delete_records, solr_conn,
                       solr_search):
    """
    Export test records to Solr and return results.

    This is a pytest fixture that allows you to run a set of test
    records (`recset`) through an export process (`etype_code`) and
    then pull results from a particular Solr `core`. If `delete` is
    True, then it will attempt to delete the test records as well.

    Returns a dictionary containing results at three different states.
    `pre` contains results before the export; `load` contains results
    after the export; `del` contains results after the deletion, or
    `None` if `delete` is False.
    """
    def _export_to_solr(core, recset, etype_code, delete=True):
        exp = new_exporter(etype_code, 'full_export', 'waiting')
        conn = solr_conn(core)
        pre_results = solr_search(conn, {'q': '*'})
        export_records(exp, recset)
        load_results = solr_search(conn, {'q': '*'})
        del_results = None
        if delete:
            del_exp = new_exporter(etype_code, 'full_export', 'waiting')
            del_recset = [r.record_metadata for r in recset]
            delete_records(del_exp, del_recset)
            del_results = solr_search(conn, {'q': '*'})

        return {'pre': pre_results, 'load': load_results, 'del': del_results}
    return _export_to_solr


@pytest.fixture
def make_field():
    """
    Make a marcfieldset.Field object given the provided data.

    This is a pytest fixture that lets you create the Field object by
    passing string data (e.g. copied from the loc.gov/marc
    documentation) for easy testing.

    Data should be in this format:

    007 1234567890
    100 1#$aAuthor Name,$d1900-2000
    """
    def _make_field(data):
        tag = data[0:3]
        field = {'tag': tag}

        if tag < '010':
            field['indicators'] = [None, None]
            field['data'] = d[4:]
        else:
            field['indicators'] = [' ' if ind == '#' else ind for ind in (data[4], data[5])]
            field['subfields'] = [{'tag': d[0], 'data': d[1:] } for d in data[6:].split('$')[1:]]

        return marcfieldset.Field(field)
    return _make_field


@pytest.fixture
def make_fieldset(make_field):
    """
    Make a marcfieldset.Fieldset object given the provided data.

    This is a pytest fixture that lets you create a Fieldset object by
    passing a list of strings, one per MARC field, formatted like this:

    [
        '007 1234567890',
        '100 1#$aAuthor Name,$d1900-2000',
        '245 ##$aSome title:$bSubtitle' 
    ]
    """
    def _make_fieldset(field_data_rows):
        fields = [make_field(r) for r in field_data_rows]
        return marcfieldset.Fieldset(fields)
    return _make_fieldset


@pytest.fixture
def make_sierrabib(make_fieldset):
    """
    Make a bib data struct like you would get from sierrabibstractor.

    This is a pytest fixture that lets you create dict structure
    containing fixed fields and a Fieldset object, like you would get
    from the sierrabibstractor.extract function.
    """
    def _make_sierrabib(fixed_fields, field_data_rows):
        return {'fixedfields': fixed_fields, 'marcfields': make_fieldset(field_data_rows)}
    return _make_sierrabib
