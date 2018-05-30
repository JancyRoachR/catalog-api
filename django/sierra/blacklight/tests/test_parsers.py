"""
Tests the blacklight.parsers functions.
"""

import re

import pytest

from blacklight import parsers


# FIXTURES AND TEST DATA

# External fixtures used in this file can be found in
# django/sierra/blacklight/tests/conftest.py:
#    make_field

@pytest.fixture
def pp_do():
    """
    Pytest fixture that returns a sample `do` function.
    """
    def _do(data):
        return re.sub(r'\.', '', data)
    return _do



# TESTS

@pytest.mark.parametrize('data, expected', [
    ('First, Last', True),
    ('First,Last', True),
    ('First,Last,', True),
    ('First, Last, Something Else', True),
    (', Last, First', True),
    ('First,', False),
    ('First', False),
    ('First Last', False),
    ('First, ', False),
    (', Last', False),
    (',Last', False),
])
def test_has_comma_in_middle(data, expected):
    """
    `has_comma_in_middle` should return True if the given string has a
    comma separating two or more words.
    """
    assert parsers.has_comma_in_middle(data) == expected


@pytest.mark.parametrize('data, expected', [
    (' test data', 'test data'),
    ('test data ', 'test data'),
    ('test  data', 'test data'),
    (' test  data ', 'test data'),
    (' test  data test', 'test data test'),
    (' test  data test  ', 'test data test'),
    (' test data  test  ', 'test data test'),
])
def test_normalize_whitespace(data, expected):
    """
    `normalize_whitespace` should strip whitespace from the beginning
    and end of a string AND consolidate internal spacing.
    """
    assert parsers.normalize_whitespace(data) == expected


@pytest.mark.parametrize('data, expected', [
    ('test : data', 'test: data'),
    ('test / data', 'test / data'),
    ('test : data / data', 'test: data / data'),
    ('test . ; : data / data', 'test: data / data'),
    ('test .;: data / data', 'test: data / data'),
    ('test . ; : / data / data', 'test / data / data'),
    ('.:;test / data', ';test / data'),
    ('test / data.:;', 'test / data;'),
])
def test_normalize_punctuation(data, expected):
    """
    `normalize_punctuation` should remove whitespace to the immediate
    left of certain punctuation marks and instances of consecutive
    punctuation marks.
    """
    assert parsers.normalize_punctuation(data) == expected


@pytest.mark.parametrize('data, keep_inner, to_keep_re, to_remove_re, to_protect_re, expected', [
    ('Test data', True, None, None, None, 'Test data'),
    ('Test data [inner]', True, None, None, None, 'Test data inner'),
    ('Test data-[inner]', True, None, None, None, 'Test data-inner'),
    ('Test data[inner]', True, None, None, None, 'Test datainner'),
    ('Test [inner] data', True, None, None, None, 'Test inner data'),
    ('[Inner] test data', True, None, None, None, 'Inner test data'),
    ('[First] test [Middle] data [Last]', True, None, None, None, 'First test Middle data Last'),
    ('Test data', True, None, r'inner', None, 'Test data'),
    ('Test data [inner]', True, None, r'inner', None, 'Test data'),
    ('Test data-[inner]', True, None, r'inner', None, 'Test data-'),
    ('Test data[inner]', True, None, r'inner', None, 'Test data'),
    ('Test [inner] data', True, None, r'inner', None, 'Test data'),
    ('[Inner] test data', True, None, r'Inner', None, 'test data'),
    ('[First] test [Middle] data [Last]', True, None, r'(Middle|Last)', None, 'First test data'),
    ('[First] test [Middle] [Middle] data [Last]', True, None, r'(Middle|Last)', None, 'First test data'),
    ('Test data', False, None, None, None, 'Test data'),
    ('Test data [inner]', False, None, None, None, 'Test data'),
    ('Test data-[inner]', False, None, None, None, 'Test data-'),
    ('Test data[inner]', False, None, None, None, 'Test data'),
    ('Test [inner] data', False, None, None, None, 'Test data'),
    ('[Inner] test data', False, None, None, None, 'test data'),
    ('[First] test [Middle] data [Last]', False, None, None, None, 'test data'),
    ('[First] test [Middle] [Middle] data [Last]', False, None, None, None, 'test data'),
    ('Test data', False, r'inner', None, None, 'Test data'),
    ('Test data [inner]', False, r'inner', None, None, 'Test data inner'),
    ('Test data-[inner]', False, r'inner', None, None, 'Test data-inner'),
    ('Test data[inner]', False, r'inner', None, None, 'Test datainner'),
    ('Test [inner] data', False, r'inner', None, None, 'Test inner data'),
    ('[Inner] test data', False, r'Inner', None, None, 'Inner test data'),
    ('[First] test [Middle] data [Last]', False, r'(Middle|Last)', None, None, 'test Middle data Last'),
    ('[First] test [Middle] [Middle] data [Last]', False, r'(Middle|Last)', None, None, 'test Middle Middle data Last'),
    ('Test data', True, None, None, r'inner', 'Test data'),
    ('Test data [inner]', True, None, None, r'inner', 'Test data [inner]'),
    ('Test data-[inner]', True, None, None, r'inner', 'Test data-[inner]'),
    ('Test data[inner]', True, None, None, r'inner', 'Test data[inner]'),
    ('Test [inner] data', True, None, None, r'inner', 'Test [inner] data'),
    ('[Inner] test data', True, None, None, r'Inner', '[Inner] test data'),
    ('[First] test [Middle] data [Last]', True, None, None, r'(Middle|Last)', 'First test [Middle] data [Last]'),
    ('[First] test [Middle] [Middle] data [Last]', True, None, None, r'(Middle|Last)', 'First test [Middle] [Middle] data [Last]'),
])
def test_strip_brackets(data, keep_inner, to_keep_re, to_remove_re, to_protect_re, expected):
    """
    `strip_brackets` should correctly strip square brackets based on
    the provided keep/remove/protect arguments.
    """
    assert parsers.strip_brackets(data, keep_inner, to_keep_re, to_remove_re, to_protect_re) == expected


@pytest.mark.parametrize('data, expected', [
    ('No periods, no changes', 'No periods, no changes'),
    ('Remove ending period.', 'Remove ending period'),
    ('Remove ending period from numeric ordinal 1.', 'Remove ending period from numeric ordinal 1'),
    ('Remove ending period from alphabetic ordinal 21st.', 'Remove ending period from alphabetic ordinal 21st'),
    ('Remove ending period from Roman Numeral XII.', 'Remove ending period from Roman Numeral XII'),
    ('Protect ending period from abbreviation eds.', 'Protect ending period from abbreviation eds.'),
    ('Protect ending period from initial J.', 'Protect ending period from initial J.'),
    ('Lowercase initials do not count, j.', 'Lowercase initials do not count, j'),
    ('Remove inner period. Dude', 'Remove inner period Dude'),
    ('Protect period inside a word, like 1.1', 'Protect period inside a word, like 1.1'),
    ('Protect inner period from numeric ordinal 1. Dude', 'Protect inner period from numeric ordinal 1. Dude'),
    ('Protect inner period from alphabetic ordinal 21st. Dude', 'Protect inner period from alphabetic ordinal 21st. Dude'),
    ('Protect inner period from Roman Numeral XII. Dude', 'Protect inner period from Roman Numeral XII. Dude'),
    ('Protect inner period from abbreviation eds. Dude', 'Protect inner period from abbreviation eds. Dude'),
    ('Protect inner period from inital J. Dude', 'Protect inner period from inital J. Dude'),
    ('J.R.R. Tolkien', 'J.R.R. Tolkien'),
    ('Tolkien, J.R.R.', 'Tolkien, J.R.R.'),
    ('Tolkien, J.R.R..', 'Tolkien, J.R.R.'),
])
def test_protect_periods_and_do(data, expected, pp_do):
    """
    `protect_periods_and_do` should perform the supplied `do` function
    but protect "structural" periods first. The idea is that the
    supplied function parses the supplied data based on structural
    periods, so non-structural periods are converted to a different
    character before the `do` function runs.

    In this case, the pp_do fixture strips all periods. So protected
    (i.e. non-structural) periods should not be stripped.
    """
    assert parsers.protect_periods_and_do(data, pp_do) == expected


@pytest.mark.parametrize('data, expected', [
    ('do not strip inner whitespace', 'do not strip inner whitespace'),
    ('do not strip, inner punctuation', 'do not strip, inner punctuation'),
    (' strip whitespace ', 'strip whitespace'),
    ('strip one punctuation mark at end.', 'strip one punctuation mark at end'),
    ('strip repeated punctuation marks at end...', 'strip repeated punctuation marks at end'),
    ('strip multiple different punctuation marks at end./', 'strip multiple different punctuation marks at end'),
    ('strip whitespace then punctuation :', 'strip whitespace then punctuation'),
    ('strip punctuation then whitespace. ', 'strip punctuation then whitespace'),
    ('strip w then p then w : ', 'strip w then p then w'),
    ('(strip full parens)', 'strip full parens'),
    ('(strip full parens with punctuation after).', 'strip full parens with punctuation after'),
    ('(strip full parens with punctuation before.)', 'strip full parens with punctuation before'),
    ('(strip full parens with punctuation before and after.) :', 'strip full parens with punctuation before and after'),
    ('do not strip (partial parens)', 'do not strip (partial parens)'),
    ('do not strip (partial parens).', 'do not strip (partial parens)'),
    ('do not strip (partial parens) :', 'do not strip (partial parens)'),
])
def test_strip_ends(data, expected):
    """
    `strip_ends` should correctly strip whitespace and punctuation from
    both ends of the input data string.
    """
    assert parsers.strip_ends(data) == expected


@pytest.mark.parametrize('data, expected', [
    ('...', ''),
    ('something', 'something'),
    ('something.', 'something.'),
    ('something..', 'something..'),
    ('A big ... something', 'A big something'),
    ('A big... something', 'A big something'),
    ('A big...something', 'A big something'),
    ('A big ...something', 'A big something'),
    ('A big something. ...', 'A big something.'),
    ('A big something ... .', 'A big something.'),
    ('A big something ....', 'A big something.'),
    (' ... something', 'something'),
    ('... something', 'something'),
    ('...something', 'something'),
    ('A big ... something...', 'A big something'),
])
def test_strip_ellipses(data, expected):
    """
    `strip ellipses` should correctly strip ellipses (...) from the
    input data string.
    """
    assert parsers.strip_ellipses(data) == expected


@pytest.mark.parametrize('data, expected', [
    ('This is an example of a title : subtitle / ed. by John Doe.', 'This is an example of a title: subtitle / ed. by John Doe'),
    ('Some test data ... that we have (whatever [whatever]).', 'Some test data that we have (whatever whatever)'),
])
def test_clean(data, expected):
    """
    `clean` should strip ending punctuation, brackets, and ellipses and
    normalize whitespace and punctuation.
    """
    assert parsers.clean(data) == expected


@pytest.mark.parametrize('field_data, exp_forename, exp_surname, exp_family_name', [
    ('100 0#$aThomale, Jason,$d1979-', 'Jason', 'Thomale', ''),
    ('100 1#$aThomale, Jason,$d1979-', 'Jason', 'Thomale', ''),
    ('100 3#$aThomale, Jason,$d1979-', 'Jason', 'Thomale', ''),
    ('100 0#$aJohn,$cthe Baptist, Saint.', 'John', '', ''),
    ('100 0#$aJohn$bII Comnenus,$cEmperor of the East,$d1088-1143.', 'John II Comnenus', '', ''),
    ('100 1#$aByron, George Gordon Byron,$cBaron,$d1788-1824.', 'George Gordon Byron', 'Byron', ''),
    ('100 1#$aJoannes Aegidius, Zamorensis,$d1240 or 41-ca. 1316.', 'Zamorensis', 'Joannes Aegidius', ''),
    ('600 30$aMorton family.', '', 'Morton', 'Morton family'),
    ('600 20$aMorton family.', '', 'Morton', 'Morton family'),
    ('600 20$aMorton family.', '', 'Morton', 'Morton family'),
])
def test_person_name(field_data, exp_forename, exp_surname, exp_family_name, make_field):
    """
    `person_name` should parse a personal name into the expected
    forename, surname, and family name.
    """
    field = make_field(field_data)
    name = parsers.person_name(field)
    assert name['forename'] == exp_forename
    assert name['surname'] == exp_surname
    assert name['family_name'] == exp_family_name


@pytest.mark.parametrize('field_data, expected', [
    ('100 0#$aJohn Paul$bII,$cPope,$d1920-', ['Pope']),
    ('100 0#$aJohn$bII Comnenus,$cEmperor of the East,$d1088-1143.', ['Emperor of the East']),
    ('100 0#$aJohn,$cthe Baptist, Saint.', ['the Baptist', 'Saint']),
    ('100 0#$aJohn,$cthe Baptist,$cSaint.', ['the Baptist', 'Saint']),
    ('100 1#$aWard, Humphrey,$cMrs.,$d1851-1920.', ['Mrs.']),
])
def test_person_titles(field_data, expected, make_field):
    """
    `person_titles` should parse the title portion ($c) of a personal
    name into a list of titles.
    """
    field = make_field(field_data)
    assert parsers.person_titles(field) == expected


@pytest.mark.parametrize('field_data, exp_start_date, exp_start_date_qualifier, exp_end_date, '
                         'exp_end_date_qualifer, exp_date_type, exp_full_dates', [
    ('100 1#$aRodgers, Martha Lucile,$d1947-', 1947, '', '', '', 'dates lived', '1947-'),
    ('100 1#$aLuckombe, Philip,$dd. 1803.', '', '', 1803, '', 'dates lived', 'd. 1803'),
    ('100 1#$aMalalas, John,$dca. 491-ca. 578.', 491, 'circa', 578, 'circa', 'dates lived', 'ca. 491-ca. 578'),
    ('100 1#$aLevi, James,$dfl. 1706-1739.', 1706, '', 1739, '', 'dates flourished', 'fl. 1706-1739'),
    ('100 1#$aJoannes Aegidius, Zamorensis,$d1240 or 41-ca. 1316.', 1240, 'unsure', 1316, 'circa', 'dates lived', '1240 or 41-ca. 1316'),
    ('100 0#$aJoannes,$cActuarius,$d13th/14th cent.', 1200, '', 1399, '', 'approximate centuries', '13th/14th cent.'),
    ('100 0#$aTest,$cTest,$d14th/13th cent. BCE', -1400, '', -1301, '', 'approximate centuries', '14th/13th cent. BCE'),
    ('100 0#$aPiri Reis,$dd. 1554?', '', '', 1554, 'unsure', 'dates lived', 'd. 1554?'),
    ('800 1#$aDangerfield, Rodney,$d1921-', 1921, '', '', '', 'dates lived', '1921-'),
    ('100 1#$aSmith, John,$d1882 Aug. 5-', 1882, '', '', '', 'dates lived', '1882 Aug. 5-'),
    ('100 1#$aSmith, John,$dsomething weird!', '', '', '', '', 'unknown date types', 'something weird!'),
])
def test_person_dates(field_data, exp_start_date, exp_start_date_qualifier, exp_end_date,
                      exp_end_date_qualifer, exp_date_type, exp_full_dates, make_field):
    """
    `person_dates` should correctly parse dates associated with
    personal names.
    """
    field = make_field(field_data)
    dates = parsers.person_dates(field) 
    assert dates['start_date'] == exp_start_date
    assert dates['start_date_qualifier'] == exp_start_date_qualifier
    assert dates['end_date'] == exp_end_date
    assert dates['end_date_qualifier'] == exp_end_date_qualifer
    assert dates['date_type'] == exp_date_type
    assert dates['full_dates'] == exp_full_dates


@pytest.mark.parametrize('forename, surname, titles, dates, expected', [
    ('First', 'Last', [], '', 'First Last'),
    ('First', '', [], '', 'First'),
    ('', 'Last', [], '', 'Last'),
    ('', '', [], '', ''),
])
def test_untbib_person_get_name_straight(forename, surname, titles, dates, expected):
    """
    `untbib_person_get_name_straight` should correctly format a
    person's name in straight (non-inverted) order based on the passed
    untbib person data.
    """
    person = {'forename': forename, 'surname': surname, 'titles': titles, 'full_dates': dates}
    assert parsers.untbib_person_get_name_straight(person) == expected


@pytest.mark.parametrize('forename, surname, titles, dates, expected', [
    ('First', 'Last', [], '',  'Last, First'),
    ('First', '', [], '', 'First'),
    ('', 'Last', [], '', 'Last'),
    ('', '', [], '', ''),
])
def test_untbib_person_get_name_inverted(forename, surname, titles, dates, expected):
    """
    `untbib_person_get_name_inverted` should correctly format a
    person's name in inverted order based on the passed untbib person
    data.
    """
    person = {'forename': forename, 'surname': surname, 'titles': titles, 'full_dates': dates}
    assert parsers.untbib_person_get_name_inverted(person) == expected


@pytest.mark.parametrize('forename, surname, titles, dates, expected', [
    ('First', 'Last', [], '', 'First Last'),
    ('First', '', [], '', 'First'),
    ('', 'Last', [], '', 'Last'),
    ('', '', [], '', ''),
    ('First', 'Last', ['Sir'], '', 'First Last, Sir'),
    ('First', 'Last', ['Sir', 'Baron'], '', 'First Last, Sir, Baron'),
    ('First', 'Last', [], '1900-2000', 'First Last (1900-2000)'),
    ('First', 'Last', ['Sir'], '1900-2000', 'First Last, Sir (1900-2000)'),
])
def test_untbib_person_get_fullname(forename, surname, titles, dates, expected):
    """
    `untbib_person_get_fullname` should correctly format a person's
    name based on the passed untbib person data.
    """
    person = {'forename': forename, 'surname': surname, 'titles': titles, 'full_dates': dates}
    assert parsers.untbib_person_get_fullname(person) == expected
