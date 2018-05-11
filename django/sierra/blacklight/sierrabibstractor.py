"""
Extract lists of fields from Sierra bib records.
"""
from . import marcfieldset as mfs


def extract_leader(bib):
    """
    Extracts the Leader portion of the supplied BibRecord object
    (`bib` argument). Returns a dict field with tag LDR.
    """
    try:
        ldr = bib.record_metadata.leaderfield_set.all()[0]
    except IndexError:
        # Sierra records *should* all have LDRs. But we don't
        # *really* care if they don't, so we'll just skip the LDR
        # if it's not there.
        pass
    data = '#####{}{}{}{}{}22#####{}{}{}4500'.format(
        ldr.record_status_code,
        ldr.record_type_code,
        ldr.bib_level_code,
        ldr.control_type_code,
        ldr.char_encoding_scheme_code,
        ldr.encoding_level_code,
        ldr.descriptive_cat_form_code,
        ldr.multipart_level_code)
    field = mfs.Field({'tag': 'LDR', 'data': data, 'indicators': [None, None],
                       'subfields': [], 'occurrence': 0})
    return mfs.Fieldset([field])


def extract_controlfields(bib):
    """
    Extracts control fields (006, 007, 008) from the supplied
    BibRecord object (`bib` argument). Returns a list of dict
    fields.
    """
    fields = []
    for cf in bib.record_metadata.controlfield_set.all():
        tag = '00{}'.format(cf.control_num)
        data = unicode(cf.get_data())
        field = mfs.Field({'tag': tag, 'data': data,
                           'indicators': [None, None], 'subfields': [],
                           'occurrence': cf.occ_num})
        fields.append(field)
    return mfs.Fieldset(fields)


def _split_field_data_into_subfields(data):
    """
    Splits a Sierra field data string (|aStuff|bMore Stuff) into
    a subfields structure, e.g.:
    ([{'tag': 'a', 'data': 'Stuff'}, {'tag': 'b', 'More Stuff'}])
    """
    subfields = []
    parts = data.split('|')
    if len(parts) > 1:
        subfields = [{'tag': p[0], 'data': p[1:]} for p in parts[1:]]
    return subfields


def extract_varfields(bib):
    """
    Extracts variable fields from the supplied BibRecord object
    (`bib` argument). Returns a list of dict fields.
    """
    fields = []
    for vf in bib.record_metadata.varfield_set.all():
        tag = vf.marc_tag
        data = unicode(vf.field_content)
        occurrence = vf.occ_num
        indicators = [None, None]
        subfields = []

        if int(tag) >= 10:
            indicators = [vf.marc_ind1, vf.marc_ind2]
            subfields = _split_field_data_into_subfields(data)

        field = mfs.Field({'tag': tag, 'indicators': indicators,
                           'subfields': subfields, 'occurrence': occurrence})
        fields.append(field)
    return mfs.Fieldset(fields)


def extract(bib):
    """
    Extracts all fields (Leader, control fields, variable fields)
    from the supplied BibRecord object (`bib` argument). Returns a list
    of dict fields. Note they're not returned in a good sort order; if
    you want them sorted, you'll have to sort them yourself.
    """
    fields = extract_leader(bib)
    fields.extend(extract_controlfields(bib))
    fields.extend(extract_varfields(bib))
    return fields
