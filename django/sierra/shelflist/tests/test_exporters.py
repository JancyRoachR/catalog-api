"""
Tests shelflist-app classes derived from `export.exporter.Exporter`.
"""

import pytest
import importlib


# FIXTURES AND TEST DATA
# Fixtures used in the below tests can be found in
# django/sierra/base/tests/conftest.py:
#    sierra_records_by_recnum_range, new_exporter,
#    record_sets, export_records, delete_records,
#    derive_exporter_class, assert_all_exported_records_are_indexed,
#    assert_deleted_records_are_not_indexed

pytestmark = pytest.mark.django_db


@pytest.fixture
def exporter_class(derive_exporter_class):
    def _exporter_class(name):
        return derive_exporter_class(name, 'shelflist.exporters')
    return _exporter_class


# TESTS

def test_main_itemstosolr_version(new_exporter, exporter_class):
    """
    Make sure that the main ItemsToSolr job we're testing is from the
    shelflist app, not the export app.
    """
    expclass = exporter_class('ItemsToSolr')
    exporter = new_exporter(expclass, 'full_export', 'waiting')
    assert exporter.app_name == 'shelflist'


@pytest.mark.parametrize('et_code', [
    'ItemsBibsToSolr',
    'BibsAndAttachedToSolr'
])
def test_child_itemstosolr_versions(et_code, new_exporter, exporter_class):
    """
    Compound exporters from the main `export` app should use the
    ItemsToSolr from the `shelflist` app.
    """
    expclass = exporter_class(et_code)
    exporter = new_exporter(expclass, 'full_export', 'waiting')
    assert exporter.app_name == 'export'
    for child_etcode, child in exporter.children.items():
        if child_etcode == 'ItemsToSolr':
            assert child.app_name == 'shelflist'
        else:
            assert child.app_name == 'export'


@pytest.mark.exports
def test_itemstosolr_get_records(exporter_class, record_sets, new_exporter):
    """
    For Exporter classes that get data from Sierra, the `get_records`
    method should return a record set containing the expected records.
    """
    expclass = exporter_class('ItemsToSolr')
    exporter = new_exporter(expclass, 'full_export', 'waiting')
    db_records = exporter.get_records()
    assert len(db_records) > 0
    assert all([rec in db_records for rec in record_sets['item_set']])


@pytest.mark.deletions
def test_itemstosolr_get_deletions(exporter_class, record_sets, new_exporter):
    """
    For Exporter classes that get data from Sierra, the `get_deletions`
    method should return a record set containing the expected records.
    """
    expclass = exporter_class('ItemsToSolr')
    exporter = new_exporter(expclass, 'full_export', 'waiting')
    db_records = exporter.get_deletions()
    assert all([rec in db_records for rec in record_sets['item_del_set']])


@pytest.mark.exports
def test_itemstosolr_records_to_solr(exporter_class, record_sets, new_exporter,
                                     assert_all_exported_records_are_indexed):
    """
    The shelflist app ItemsToSolr `export_records` method should load
    the expected records into the expected Solr index.
    """
    records = record_sets['item_set']
    expclass = exporter_class('ItemsToSolr')
    exporter = new_exporter(expclass, 'full_export', 'waiting')
    exporter.export_records(records)
    exporter.commit_indexes()
    assert_all_exported_records_are_indexed(exporter, records)


@pytest.mark.deletions
def test_itemstosolr_delete_records(exporter_class, record_sets, new_exporter,
                                    solr_assemble_specific_record_data,
                                    assert_records_are_indexed,
                                    assert_deleted_records_are_not_indexed):
    """
    The shelflist app ItemsToSolr `delete_records` method should delete
    records from the appropriate index or indexes.
    """
    records = record_sets['item_del_set']
    data = ({'id': r.id, 'record_number': r.get_iii_recnum()} for r in records)
    assembler = solr_assemble_specific_record_data(data, ('item',))
    
    expclass = exporter_class('ItemsToSolr')
    exporter = new_exporter(expclass, 'full_export', 'waiting')

    for index in exporter.indexes.values():
        assert_records_are_indexed(index, records)
    exporter.delete_records(records)
    exporter.commit_indexes()
    assert_deleted_records_are_not_indexed(exporter, records)


@pytest.mark.shelflist
def test_export_shelflist_manifest():
    pass

