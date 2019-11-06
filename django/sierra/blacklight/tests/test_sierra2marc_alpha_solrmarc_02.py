"""
Tests the blacklight.parsers functions.
"""

import pytest
import pymarc
import ujson

from blacklight import sierra2marc_alpha_solrmarc_02 as s2m


# FIXTURES AND TEST DATA
pytestmark = pytest.mark.django_db


@pytest.fixture
def bibrecord_to_pymarc():
    """
    Pytest fixture for converting a `bib` from the Sierra DB (i.e. a
    base.models.BibRecord instance) to a pymarc MARC record object.
    """
    def _bibrecord_to_pymarc(bib):
        s2m_obj = s2m.S2MarcBatchBlacklightSolrMarc(bib)
        return s2m_obj.compile_original_marc(bib)
    return _bibrecord_to_pymarc

@pytest.fixture
def add_marc_fields():
    """
    Pytest fixture for adding fields to the given `bib` (pymarc Record
    object). If `overwrite_existing` is True, which is the default,
    then all new MARC fields will overwrite existing fields with the
    same tag.

    One or more `fields` may be passed. Each field is a tuple of:
        (tag, contents, indicators)

    Indicators is optional. If the MARC tag is 001 to 009, then a data
    field is created from `contents`. Otherwise `contents` is treated
    as a list of subfields, and `indicators` defaults to blank, blank.
    """
    def _add_marc_fields(bib, fields, overwrite_existing=True):
        pm_fields = []
        for f in fields:
            tag, contents = f[0:2]
            if overwrite_existing:
                bib.remove_fields(tag)
            if int(tag) < 10:
                pm_fields.append(s2m.make_pmfield(tag, data=contents))
            else:
                ind = tuple(f[2]) if len(f) > 2 else tuple('  ')
                pm_fields.append(s2m.make_pmfield(tag, subfields=contents,
                                                  indicators=ind))
        bib.add_grouped_field(*pm_fields)
        return bib
    return _add_marc_fields


@pytest.fixture
def blasm_pipeline_class():
    """
    Pytest fixture; returns the BlacklightASMPipeline class.
    """
    return s2m.BlacklightASMPipeline


@pytest.fixture
def plbundleconverter_class():
    """
    Pytest fixture; returns the PipelineBundleConverter class.
    """
    return s2m.PipelineBundleConverter


@pytest.fixture
def assert_json_matches_expected():
    """
    Pytest fixture for asserting that a list of `json_strs` and
    `exp_dicts` are equivalent. Tests to make sure each key/val pair
    in each of exp_dicts is found in the corresponding `json_strs`
    obj.
    """
    def _assert_json_matches_expected(json_strs, exp_dicts):
        assert len(json_strs) == len(exp_dicts)
        for json, exp_dict in zip(json_strs, exp_dicts):
            cmp_dict = ujson.loads(json)
            for key in exp_dict.keys():
                assert cmp_dict[key] == exp_dict[key]
    return _assert_json_matches_expected


@pytest.fixture
def update_test_bib_inst(add_varfields_to_record, add_items_to_bib):
    """
    Pytest fixture. Update the given `bib` (base.models.BibRecord)
    instance with given `varfields` and/or `items_info`. Returns the
    updated bib instance. Underneath, fixture factories are used that
    ensure the changes are reverted after the test runs. 
    """
    def _update_test_bib_inst(bib, varfields=[], items=[]):
        for field_tag, marc_tag, vals in varfields:
            bib = add_varfields_to_record(bib, field_tag, marc_tag, vals,
                                          overwrite_existing=True)

        items_to_add = []
        for item in items:
            try:
                attrs, item_vfs = item
            except ValueError:
                attrs, item_vfs = item, []
            items_to_add.append({'attrs': attrs, 'varfields': item_vfs})
        return add_items_to_bib(bib, items_to_add)
    return _update_test_bib_inst


# TESTS

@pytest.mark.parametrize('kwargs', [
    {'data': 'abcdefg'},
    {'data': 'abcdefg', 'indicators': '12'},
    {'data': 'abcdefg', 'subfields': ['a', 'Test']},
    {'data': 'abcdefg', 'indicators': '12', 'subfields': ['a', 'Test']}
])
def test_make_pmfield_creates_control_field(kwargs):
    """
    When passed a `data` parameter, `make_pmfield` should create a
    pymarc control field, even if a `subfields` and/or `indicators`
    value is also passed.
    """
    field = s2m.make_pmfield('008', **kwargs)
    assert field.tag == '008'
    assert field.data == kwargs['data']
    assert not hasattr(field, 'indicators')
    assert not hasattr(field, 'subfields')


@pytest.mark.parametrize('kwargs', [
    {},
    {'indicators': '12'},
    {'subfields': ['a', 'Test1', 'b', 'Test2']}
])
def test_make_pmfield_creates_varfield(kwargs):
    """
    When NOT passed a `data` parameters, `make_pmfield` should create a
    pymarc variable-length field. If indicators are not provided,
    defaults should be blank ([' ', ' ']). If subfields are not
    provided, default should be an empty list.
    """
    field = s2m.make_pmfield('100', **kwargs)
    expected_ind = kwargs.get('indicators', '  ')
    expected_sf = kwargs.get('subfields', [])
    assert field.tag == '100'
    assert field.indicator1 == expected_ind[0]
    assert field.indicator2 == expected_ind[1]
    assert field.subfields == expected_sf


def test_blasmpipeline_do_creates_compiled_dict(blasm_pipeline_class):
    """
    The `do` method of BlacklightASMPipeline should return a dict
    compiled from the return value of each of the `get` methods--each
    key/value pair from each return value added to the finished value.
    """
    class DummyPipeline(blasm_pipeline_class):
        fields = ['dummy1', 'dummy2', 'dummy3']
        prefix = 'get_'

        def get_dummy1(self, r, marc_record):
            return {'d1': 'd1v'}

        def get_dummy2(self, r, marc_record):
            return { 'd2a': 'd2av', 'd2b': 'd2bv' }

        def get_dummy3(self, r, marc_record):
            return { 'stuff': ['thing'] }

    dummy_pipeline = DummyPipeline()
    bundle = dummy_pipeline.do('test', 'test')
    assert bundle == { 'd1': 'd1v', 'd2a': 'd2av', 'd2b': 'd2bv',
                       'stuff': ['thing'] }


def test_blasmpipeline_getid(bl_sierra_test_record, blasm_pipeline_class):
    """
    BlacklightASMPipeline.get_id should return the bib Record ID
    formatted according to III's specs.
    """
    pipeline = blasm_pipeline_class()
    bib = bl_sierra_test_record('b6029459')
    val = pipeline.get_id(bib, None)
    assert val == {'id': '.b6029459'}


@pytest.mark.parametrize('in_val, expected', [
    (True, 'true'),
    (False, 'false')
])
def test_blasmpipeline_getsuppressed(in_val, expected, bl_sierra_test_record,
                                     blasm_pipeline_class,
                                     setattr_model_instance):
    """
    BlacklightASMPipeline.get_suppressed should return 'false' if the
    record is not suppressed.
    """
    pipeline = blasm_pipeline_class()
    bib = bl_sierra_test_record('b6029459')
    setattr_model_instance(bib, 'is_suppressed', in_val)
    val = pipeline.get_suppressed(bib, None)
    assert val == {'suppressed': expected}


def test_blasmpipeline_getiteminfo_ids(bl_sierra_test_record,
                                       blasm_pipeline_class,
                                       update_test_bib_inst,
                                       assert_json_matches_expected):
    """
    The `items_json` key of the value returned by
    BlacklightASMPipeline.get_item_info should be a list of JSON
    objects, each one corresponding to an item. The 'i' key for each
    JSON object should match the numeric portion of the III rec num for
    that item.
    """
    pipeline = blasm_pipeline_class()
    bib = bl_sierra_test_record('bib_no_items')
    bib = update_test_bib_inst(bib, items=[{}, {}])
    val = pipeline.get_item_info(bib, None)
    
    items = [l.item_record for l in bib.bibrecorditemrecordlink_set.all()]
    expected = [{'i': str(item.record_metadata.record_num)} for item in items]
    assert_json_matches_expected(val['items_json'], expected)


@pytest.mark.parametrize('bib_cn_info, items_info, expected_cns', [
    ([('c', '050', ['|aTEST BIB CN'])],
     [({'copy_num': 1}, [])],
     ['TEST BIB CN']),
    ([('c', '090', ['|aTEST BIB CN'])],
     [({'copy_num': 1}, [])],
     ['TEST BIB CN']),
    ([('c', '092', ['|aTEST BIB CN'])],
     [({'copy_num': 1}, [])],
     ['TEST BIB CN']),
    ([('c', '099', ['|aTEST BIB CN'])],
     [({'copy_num': 1}, [])],
     ['TEST BIB CN']),
    ([],
     [({'copy_num': 1}, [('c', '050', ['|aTEST ITEM CN'])])],
     ['TEST ITEM CN']),
    ([],
     [({'copy_num': 1}, [('c', '090', ['|aTEST ITEM CN'])])],
     ['TEST ITEM CN']),
    ([],
     [({'copy_num': 1}, [('c', '092', ['|aTEST ITEM CN'])])],
     ['TEST ITEM CN']),
    ([],
     [({'copy_num': 1}, [('c', '099', ['|aTEST ITEM CN'])])],
     ['TEST ITEM CN']),
    ([],
     [({'copy_num': 1}, [('c', None, ['TEST ITEM CN'])])],
     ['TEST ITEM CN']),
    ([('c', '050', ['TEST BIB CN'])],
     [({'copy_num': 1}, [('c', None, ['TEST ITEM CN'])]),
      ({'copy_num': 1}, [])],
     ['TEST ITEM CN',
      'TEST BIB CN']),
    ([('c', '050', ['TEST BIB CN'])],
     [({'copy_num': 2}, [('c', None, ['TEST ITEM CN'])]),
      ({'copy_num': 3}, [])],
     ['TEST ITEM CN c.2',
      'TEST BIB CN c.3']),
    ([('c', '050', ['TEST BIB CN'])],
     [({'copy_num': 1}, [('v', None, ['volume 1'])])],
     ['TEST BIB CN volume 1']),
    ([('c', '050', ['TEST BIB CN'])],
     [({'copy_num': 1}, [('v', None, ['volume 2', 'volume 1'])])],
     ['TEST BIB CN volume 2']),
    ([('c', '050', ['TEST BIB CN'])],
     [({'copy_num': 2}, [('v', None, ['volume 1'])])],
     ['TEST BIB CN volume 1 c.2']),
    ([],
     [({'copy_num': 1}, [])],
     [None]),
], ids=[
    'bib cn (c050), no item cn => bib cn',
    'bib cn (c090), no item cn => bib cn',
    'bib cn (c092), no item cn => bib cn',
    'bib cn (c099), no item cn => bib cn',
    'no bib cn, item cn (c050) => item cn',
    'no bib cn, item cn (c090) => item cn',
    'no bib cn, item cn (c092) => item cn',
    'no bib cn, item cn (c099) => item cn',
    'no bib cn, item cn (non-marc c-tagged field) => item cn',
    'item cn, if present, overrides bib cn',
    'copy_num > 1 is appended to cn',
    'volume is appended to cn',
    'if >1 volumes, only the first is used',
    'both copy_num AND volume may appear (volume first, then copy)',
    'if NO cn, copy, or volume, cn defaults to None/null'
])
def test_blasmpipeline_getiteminfo_callnumbers(bib_cn_info, items_info,
                                               expected_cns,
                                               bl_sierra_test_record,
                                               blasm_pipeline_class,
                                               update_test_bib_inst,
                                               assert_json_matches_expected):
    """
    The `items_json` key of the value returned by
    BlacklightASMPipeline.get_item_info should be a list of JSON
    objects, each one corresponding to an item. The 'c' key for each
    JSON object contains the call number. Various parameters test how
    the item call number is generated.
    """
    pipeline = blasm_pipeline_class()
    bib = bl_sierra_test_record('bib_no_items')
    bib = update_test_bib_inst(bib, varfields=bib_cn_info, items=items_info)
    val = pipeline.get_item_info(bib, None)
    expected = [{'c': cn} for cn in expected_cns]
    assert_json_matches_expected(val['items_json'], expected)


@pytest.mark.parametrize('items_info, expected', [
    ([({'copy_num': 1}, [('b', None, ['1234567890'])])],
     [{'b': '1234567890'}]),
    ([({'copy_num': 1}, [('b', None, ['2', '1'])])],
     [{'b': '2'}]),
    ([({'copy_num': 1}, [('p', None, ['Note1', 'Note2'])])],
     [{'n': ['Note1', 'Note2']}]),
    ([({'copy_num': 1}, [])],
     [{'b': None, 'n': None}]),
], ids=[
    'one barcode',
    'if the item has >1 barcode, just the first is used',
    'if the item has >1 note, then all are included',
    'if no barcodes/notes, barcode/notes is None/null',
])
def test_blasmpipeline_getiteminfo_bcodes_notes(items_info, expected,
                                                bl_sierra_test_record,
                                                blasm_pipeline_class,
                                                update_test_bib_inst,
                                                assert_json_matches_expected):
    """
    The `items_json` key of the value returned by
    BlacklightASMPipeline.get_item_info should be a list of JSON
    objects, each one corresponding to an item. The 'b' and 'n' keys
    for each JSON object contain the barcode and public notes,
    respectively. Various parameters test how those are generated.
    """
    pipeline = blasm_pipeline_class()
    bib = bl_sierra_test_record('bib_no_items')
    bib = update_test_bib_inst(bib, items=items_info)
    val = pipeline.get_item_info(bib, None)
    assert_json_matches_expected(val['items_json'], expected)


@pytest.mark.parametrize('items_info, exp_items, exp_more_items', [
    ([({}, [('b', None, ['1'])]),
      ({}, [('b', None, ['2'])])],
     [{'b': '1'},
      {'b': '2'}],
     None),
    ([({}, [('b', None, ['1'])]),
      ({}, [('b', None, ['2'])]),
      ({}, [('b', None, ['3'])])],
     [{'b': '1'},
      {'b': '2'},
      {'b': '3'}],
     None),
    ([({}, [('b', None, ['1'])]),
      ({}, [('b', None, ['2'])]),
      ({}, [('b', None, ['3'])]),
      ({}, [('b', None, ['4'])]),
      ({}, [('b', None, ['5'])])],
     [{'b': '1'},
      {'b': '2'},
      {'b': '3'}],
     [{'b': '4'},
      {'b': '5'}]),
    ([({}, [('b', None, ['7'])]),
      ({}, [('b', None, ['3'])]),
      ({}, [('b', None, ['5'])]),
      ({}, [('b', None, ['2'])]),
      ({}, [('b', None, ['4'])]),
      ({}, [('b', None, ['6'])]),
      ({}, [('b', None, ['1'])])],
     [{'b': '7'},
      {'b': '3'},
      {'b': '5'}],
     [{'b': '2'},
      {'b': '4'},
      {'b': '6'},
      {'b': '1'},]),
], ids=[
    'fewer than three items => expect <3 items, no more_items',
    'three items => expect 3 items, no more_items',
    'more than three items => expect >3 items, plus more_items',
    'multiple items in bizarre order stay in order'
])
def test_blasmpipeline_getiteminfo_num_items(items_info, exp_items,
                                             exp_more_items,
                                             bl_sierra_test_record,
                                             blasm_pipeline_class,
                                             update_test_bib_inst,
                                             assert_json_matches_expected):
    """
    BlacklightASMPipeline.get_item_info return value should be a dict
    with keys `items_json`, `more_items_json`, and `has_more_items`
    that are based on the total number of items on the record. The
    first three attached items are in items_json; others are in
    more_items_json. has_more_items is 'true' if more_items_json is
    not empty. Additionally, items should remain in the order they
    appear on the record.
    """
    pipeline = blasm_pipeline_class()
    bib = bl_sierra_test_record('bib_no_items')
    bib = update_test_bib_inst(bib, items=items_info)
    val = pipeline.get_item_info(bib, None)
    assert_json_matches_expected(val['items_json'], exp_items)
    if exp_more_items:
        assert val['has_more_items'] == 'true'
        assert_json_matches_expected(val['more_items_json'], exp_more_items)
    else:
        assert val['has_more_items'] == 'false'
        assert val['more_items_json'] is None


@pytest.mark.parametrize('items_info, expected_r', [
    ([({'location_id': 'w3'}, {}),
      ({'location_id': 'xmus', 'itype_id': 7}, {})],
     'catalog'),
    ([({'location_id': 'czwww'}, {}),
      ({'location_id': 'w3', 'item_status_id': 'o'}, {}),
      ({'location_id': 'w3', 'itype_id': 7}, {}),
      ({'location_id': 'w3', 'itype_id': 20}, {}),
      ({'location_id': 'w3', 'itype_id': 29}, {}),
      ({'location_id': 'w3', 'itype_id': 69}, {}),
      ({'location_id': 'w3', 'itype_id': 74}, {}),
      ({'location_id': 'w3', 'itype_id': 112}, {}),
      ],
     None),
    ([({'location_id': 'w4spe'}, {}),
      ({'location_id': 'w4mr1'}, {}),
      ({'location_id': 'w4mr2'}, {}),
      ({'location_id': 'w4mr3'}, {}),
      ({'location_id': 'w4mrb'}, {}),
      ({'location_id': 'w4mrx'}, {})],
     'aeon'),
], ids=[
    'items that are requestable through the catalog (Sierra)',
    'items that are not requestable',
    'items that are requestable through Aeon',
])
def test_blasmpipeline_getiteminfo_requesting(items_info, expected_r,
                                              bl_sierra_test_record,
                                              blasm_pipeline_class,
                                              update_test_bib_inst,
                                              assert_json_matches_expected):
    """
    The `items_json` key of the value returned by
    BlacklightASMPipeline.get_item_info should be a list of JSON
    objects, each one corresponding to an item. The 'r' key for each
    JSON object contains a string describing how end users request the
    item. (See parameters for details.) Note that this hits the
    highlights but isn't exhaustive.
    """
    pipeline = blasm_pipeline_class()
    bib = bl_sierra_test_record('bib_no_items')
    bib = update_test_bib_inst(bib, items=items_info)
    val = pipeline.get_item_info(bib, None)
    exp_items = [{'r': expected_r} for i in range(0, len(items_info))]
    assert_json_matches_expected(val['items_json'], exp_items[0:3])
    if val['more_items_json'] is not None:
        assert_json_matches_expected(val['more_items_json'], exp_items[3:])


@pytest.mark.parametrize('marcfields, items_info, expected', [
    ([('856', ['u', 'http://example.com', 'y', 'The Resource',
               'z', 'connect to electronic resource'])],
     [],
     [{'u': 'http://example.com', 'n': 'connect to electronic resource',
       'l': 'The Resource', 't': 'fulltext' }]),
    ([('856', ['u', 'http://example.com" target="_blank"', 'y', 'The Resource',
               'z', 'connect to electronic resource'])],
     [],
     [{'u': 'http://example.com', 'n': 'connect to electronic resource',
       'l': 'The Resource', 't': 'fulltext' }]),
    ([('856', ['u', 'http://example.com', 'u', 'incorrect',
               'z', 'connect to electronic resource', 'z', 'incorrect'])],
     [],
     [{'u': 'http://example.com', 'n': 'connect to electronic resource',
       't': 'fulltext'}]),
    ([('856', ['u', 'http://example.com'])],
     [],
     [{'u': 'http://example.com', 't': 'link' }]),
    ([('856', ['z', 'Some label, no URL'])],
     [],
     []),
    ([('856', ['u', 'http://example.com', 'z', 'connect to e-resource'])],
     [],
     [{'t': 'fulltext'}]),
    ([('856', ['u', 'http://example.com', 'z', 'connect to online version'])],
     [],
     [{'t': 'fulltext'}]),
    ([('856', ['u', 'http://example.com', 'z', 'access Journal Online'])],
     [],
     [{'t': 'fulltext'}]),
    ([('856', ['u', 'http://example.com', 'z', 'get full-text access'])],
     [],
     [{'t': 'fulltext'}]),
    ([('856', ['u', 'http://example.com', 'z', 'access Full Text'])],
     [],
     [{'t': 'fulltext'}]),
    ([('856', ['u', 'http://example.com', 'z', 'access thing here'], ' 0')],
     [],
     [{'t': 'fulltext'}]),
    ([('856', ['u', 'http://example.com', 'z', 'access thing here'], ' 1')],
     [],
     [{'t': 'fulltext'}]),
    ([('856', ['u', 'http://example.com', 'z', 'access thing here'], ' 2')],
     [],
     [{'t': 'link'}]),
    ([('856', ['u', 'http://example.com', 'z', 'access online copy'], ' 2')],
     [],
     [{'t': 'fulltext'}]),
    ([('856', ['u', 'http://example.com', 'z', 'access Bookplate here'])],
     [],
     [{'t': 'link'}]),
    ([('856', ['u', 'http://example.com', 'z', 'access thing here'])],
     [({'item_status_id': 'w'}, [])],
     [{'t': 'fulltext'}]),
    ([('856', ['u', 'http://example.com', 'z', 'access thing here'])],
     [({'item_status_id': '-'}, []),
      ({'item_status_id': 'w'}, [])],
     [{'t': 'fulltext'}]),
    ([('856', ['u', 'http://example.com', 'z', 'access contents here']),
      ('856', ['u', 'http://example.com/2', 'z', 'access thing here'])],
     [({'item_status_id': 'w'}, [])],
     [{'t': 'link'}, {'t': 'link'}]),
    ([('962', ['t', 'Media Thing', 'u', 'http://example.com'])],
     [],
     [{'u': 'http://example.com', 'n': 'Media Thing', 't': 'media' }]),
    ([('962', ['t', 'Media Thing', 'u', 'http://example.com',
               'e', 'http://example.com/thumbnail'])],
     [],
     []),
    ([('962', ['t', 'Media Thing'])],
     [],
     []),
    ([('962', ['t', 'Access Online Version', 'u', 'http://example.com'])],
     [],
     [{'t': 'fulltext' }]),
], ids=[
    '856: simple full text URL',
    '856: strip text from end of URL: " target=_blank',
    '856 w/repeated subfields: use the first occ of each subfield',
    '856 w/out |y or |z is okay',
    '856 w/out |u is ignored (NO urls_json entry)',
    '856, type fulltext ("e-resource")',
    '856, type fulltext ("online version")',
    '856, type fulltext ("X Online")',
    '856, type fulltext ("full-text")',
    '856, type fulltext ("Full Text")',
    '856, type fulltext, ind2 == 0',
    '856, type fulltext, ind2 == 1',
    '856, type link, ind2 == 2',
    '856, type fulltext, ind2 == 2 BUT note says e.g. "online copy"',
    '856, type link ("bookplate")',
    '856, type fulltext: item with online status and 1 URL',
    '856, type fulltext: >1 items, 1 with online status, and 1 URL',
    '856, type link: item with online status but >1 URLs',
    '962 (media manager) URL, no thumb => urls_json entry',
    '962 (media manager) URL, w/thumb => NO urls_json entry',
    '962 (media manager) field, no URL => NO urls_json entry',
    '962 (media manager) field, type fulltext based on title',
])
def test_blasmpipeline_geturlsjson(marcfields, items_info, expected,
                                   bl_sierra_test_record, blasm_pipeline_class,
                                   bibrecord_to_pymarc, update_test_bib_inst,
                                   add_marc_fields,
                                   assert_json_matches_expected):
    """
    The `urls_json` key of the value returned by
    BlacklightASMPipeline.get_urls_json should be a list of JSON
    objects, each one corresponding to a URL.
    """
    pipeline = blasm_pipeline_class()
    bib = bl_sierra_test_record('bib_no_items')
    bib = update_test_bib_inst(bib, items=items_info)
    bibmarc = bibrecord_to_pymarc(bib)
    bibmarc.remove_fields('856', '962')
    bibmarc = add_marc_fields(bibmarc, marcfields)
    val = pipeline.get_urls_json(bib, bibmarc)
    assert_json_matches_expected(val['urls_json'], expected)


@pytest.mark.parametrize('mapping, bundle, expected', [
    ( (('900', ('name', 'title')),),
      {'name': 'N1', 'title': 'T1'},
      [{'tag': '900', 'data': [('a', 'N1'), ('b', 'T1')]}] ),
    ( (('900', ('names', 'titles')),),
      {'names': ['N1', 'N2'], 'titles': ['T1', 'T2', 'T3']},
      [{'tag': '900', 'data': [('a', 'N1'), ('a', 'N2'),
                               ('b', 'T1'), ('b', 'T2'), ('b', 'T3')]}] ),
    ( (('900', ('names', 'titles')),
       ('900', ('subjects', 'eras')),),
      {'names': ['N1', 'N2'], 'titles': ['T1', 'T2'], 'subjects': ['S1'],
       'eras': ['E1', 'E2']},
      [{'tag': '900', 'data': [('a', 'N1'), ('a', 'N2'),
                               ('b', 'T1'), ('b', 'T2')]},
       {'tag': '900', 'data': [('c', 'S1'), ('d', 'E1'), ('d', 'E2')]}] ),
    ( (('900', ('names', 'titles')),
       ('950', ('subjects', 'eras')),),
      {'names': ['N1', 'N2'], 'titles': ['T1', 'T2'], 'subjects': ['S1'],
       'eras': ['E1', 'E2']},
      [{'tag': '900', 'data': [('a', 'N1'), ('a', 'N2'),
                               ('b', 'T1'), ('b', 'T2')]},
       {'tag': '950', 'data': [('a', 'S1'), ('b', 'E1'), ('b', 'E2')]}] ),
    ( (('900', ('names',)),),
      {'names': ['N1', 'N2']},
      [{'tag': '900', 'data': [('a', 'N1'),]},
       {'tag': '900', 'data': [('a', 'N2'),]}] ),
    ( (('900', ('names',)),
       ('900', ('titles',))),
      {'names': ['N1', 'N2'], 'titles': ['T1', 'T2', 'T3']},
      [{'tag': '900', 'data': [('a', 'N1'),]},
       {'tag': '900', 'data': [('a', 'N2'),]},
       {'tag': '900', 'data': [('b', 'T1'),]},
       {'tag': '900', 'data': [('b', 'T2'),]}] ),
    ( (('900', ('names',)),
       ('900', ('titles',)),
       ('900', ('subjects', 'eras')),),
      {'names': ['N1', 'N2'], 'titles': ['T1', 'T2'], 'subjects': ['S1'],
       'eras': ['E1', 'E2']},
      [{'tag': '900', 'data': [('a', 'N1'),]},
       {'tag': '900', 'data': [('a', 'N2'),]},
       {'tag': '900', 'data': [('b', 'T1'),]},
       {'tag': '900', 'data': [('b', 'T2'),]},
       {'tag': '900', 'data': [('c', 'S1'), ('d', 'E1'), ('d', 'E2')]}] ),
    ( (('900', ('names',)),
       ('900', ('titles',)),
       ('950', ('subjects',)),
       ('950', ('eras',)),),
      {'names': ['N1', 'N2'], 'titles': ['T1', 'T2'], 'subjects': ['S1'],
       'eras': ['E1', 'E2']},
      [{'tag': '900', 'data': [('a', 'N1'),]},
       {'tag': '900', 'data': [('a', 'N2'),]},
       {'tag': '900', 'data': [('b', 'T1'),]},
       {'tag': '900', 'data': [('b', 'T2'),]},
       {'tag': '950', 'data': [('a', 'S1'),]},
       {'tag': '950', 'data': [('b', 'E1'),]},
       {'tag': '950', 'data': [('b', 'E2'),]}] ),
    ( (('900', ('auth', 'contrib')),
       ('900', ('auth_display',)),
       ('950', ('subjects',)),
       ('950', ('eras', 'regions')),
       ('950', ('topics', 'genres')),),
      {'auth': ['A1'], 'contrib': ['C1', 'C2'],
       'auth_display': ['A1', 'C1', 'C2'], 'subjects': ['S1', 'S2', 'S3'],
       'eras': ['E1'], 'regions': ['R1', 'R2'], 'topics': ['T1'],
       'genres': ['G1']},
      [{'tag': '900', 'data': [('a', 'A1'), ('b', 'C1'), ('b', 'C2')]},
       {'tag': '900', 'data': [('c', 'A1')]},
       {'tag': '900', 'data': [('c', 'C1')]},
       {'tag': '900', 'data': [('c', 'C2')]},
       {'tag': '950', 'data': [('a', 'S1')]},
       {'tag': '950', 'data': [('a', 'S2')]},
       {'tag': '950', 'data': [('a', 'S3')]},
       {'tag': '950', 'data': [('b', 'E1'), ('c', 'R1'), ('c', 'R2')]},
       {'tag': '950', 'data': [('d', 'T1'), ('e', 'G1')]}] ),
    ( (('900', ('auth', 'contrib')),
       ('900', ('auth_display',)),
       ('950', ('subjects',)),
       ('950', ('eras', 'regions')),
       ('950', ('topics', 'genres')),),
      {'auth': ['A1'], 'contrib': ['C1', 'C2'],
       'auth_display': ['A1', 'C1', 'C2'], 'subjects': ['S1', 'S2', 'S3'],
       'regions': ['R1', 'R2'], 'topics': ['T1'], 'genres': ['G1']},
      [{'tag': '900', 'data': [('a', 'A1'), ('b', 'C1'), ('b', 'C2')]},
       {'tag': '900', 'data': [('c', 'A1')]},
       {'tag': '900', 'data': [('c', 'C1')]},
       {'tag': '900', 'data': [('c', 'C2')]},
       {'tag': '950', 'data': [('a', 'S1')]},
       {'tag': '950', 'data': [('a', 'S2')]},
       {'tag': '950', 'data': [('a', 'S3')]},
       {'tag': '950', 'data': [('c', 'R1'), ('c', 'R2')]},
       {'tag': '950', 'data': [('d', 'T1'), ('e', 'G1')]}] ),
    ( (('900', ('auth', 'contrib')),
       ('900', ('auth_display',)),
       ('950', ('subjects',)),
       ('950', ('eras', 'regions')),
       ('950', ('topics', 'genres')),),
      {'auth': ['A1'], 'contrib': ['C1', 'C2'],
       'auth_display': ['A1', 'C1', 'C2'], 'subjects': ['S1', 'S2', 'S3'],
       'topics': ['T1'], 'genres': ['G1']},
      [{'tag': '900', 'data': [('a', 'A1'), ('b', 'C1'), ('b', 'C2')]},
       {'tag': '900', 'data': [('c', 'A1')]},
       {'tag': '900', 'data': [('c', 'C1')]},
       {'tag': '900', 'data': [('c', 'C2')]},
       {'tag': '950', 'data': [('a', 'S1')]},
       {'tag': '950', 'data': [('a', 'S2')]},
       {'tag': '950', 'data': [('a', 'S3')]},
       {'tag': '950', 'data': [('d', 'T1'), ('e', 'G1')]}] ),
    ( (('900', ('auth', 'contrib')),
       ('900', ('auth_display',)),
       ('950', ('subjects',)),
       ('950', ('eras', 'regions')),
       ('950', ('topics', 'genres')),),
      {'subjects': ['S1', 'S2', 'S3'], 'topics': ['T1'], 'genres': ['G1']},
      [{'tag': '950', 'data': [('a', 'S1')]},
       {'tag': '950', 'data': [('a', 'S2')]},
       {'tag': '950', 'data': [('a', 'S3')]},
       {'tag': '950', 'data': [('d', 'T1'), ('e', 'G1')]}] ),
], ids=[
    '1 field with >1 subfields (single vals)',
    '1 field with >1 subfields (multiple vals => repeated subfields)',
    '>1 of same field with >1 subfields (single vals and multiple vals)',
    '>1 of diff fields with >1 subfields (single vals and multiple vals)',
    '1 field with 1 subfield (multiple vals => repeated field)',
    '>1 of same field with 1 subfield (multiple vals => repeated fields)',
    '>1 of same field with mixed subfields',
    '>1 of diff fields with 1 subfield (multiple vals => repeated field)',
    'mixed fields and subfields',
    'missing subfield is skipped',
    'missing row is skipped',
    'entire missing field is skipped'
])
def test_plbundleconverter_do_maps_correctly(mapping, bundle, expected,
                                             plbundleconverter_class):
    """
    PipelineBundleConverter.do should convert the given data dict to
    a list of pymarc Field objects correctly based on the provided
    mapping.
    """
    converter = plbundleconverter_class(mapping=mapping)
    fields = converter.do(bundle)
    for field, exp in zip(fields, expected):
        assert field.tag == exp['tag']
        assert list(field) == exp['data']
