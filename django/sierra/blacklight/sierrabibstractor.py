"""
Extract bib data (marcfields and fixedfields) from Sierra bib records.
"""
from base import models

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


def extract_fixedfields(bib):
    """
    Extracts fixed field data from the supplied BibRecord object `bib`
    and returns a data dictionary.
    """
    
    locations = []
    for bibloc in bib.bibrecordlocation_set.all():
        try:
            loc = bibloc.location
        except models.Location.DoesNotExist:
            pass
        else:
            locations.append({'code': loc.code, 'name': loc.locationname_set.all()[0].name})

    br_property = bib.bibrecordproperty_set.all()[0]
    fixed = {}
    fixed['record_id'] = bib.record_metadata.get_iii_recnum(False)
    fixed['date_cataloged'] = bib.cataloging_date_gmt
    fixed['date_created'] = bib.record_metadata.creation_date_gmt
    fixed['date_last_updated'] = bib.record_metadata.record_last_updated_gmt
    fixed['bib_type_code'] = br_property.bib_level.code
    fixed['bib_type_name'] = br_property.bib_level.biblevelpropertyname_set.all()[0].name
    fixed['mat_type_code'] = br_property.material.code
    fixed['mat_type_name'] = br_property.material.materialpropertyname_set.all()[0].name
    fixed['language_code'] = bib.language.code
    fixed['language_name'] = bib.language.languagepropertyname_set.all()[0].name
    fixed['suppress_code'] = bib.bcode3
    fixed['country_code'] = bib.country.code
    fixed['country_name'] = bib.country.countrypropertyname_set.all()[0].name
    fixed['is_suppressed'] = bib.is_suppressed
    fixed['locations'] = locations
    return fixed


def extract(bib):
    """
    Extracts all MARC fields (Leader, control fields, variable fields)
    and fixed fields from the supplied BibRecord object `bib`. Returns
    a dict, where `fixedfields` contains the fixed fields and
    `marcfields` contains the marcfieldset list of MARC fields.
    """
    fields = extract_leader(bib)
    fields.extend(extract_controlfields(bib))
    fields.extend(extract_varfields(bib))
    fixed = extract_fixedfields(bib)
    return {'fixedfields': fixed, 'marcfields': fields}
