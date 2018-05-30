"""
Extract item data from Sierra item records.
"""
from base import models


def extract_callnumber(item):
    """
    Extract the callnumber from the provided ItemRecord object, `item`.
    """
    item_cn_tuples = item.get_call_numbers()
    try:
        bib_cn_tuples = (item.bibrecorditemrecordlink_set.all()[0]
                             .bib_record.get_call_numbers())
    except IndexError:
        bib_cn_tuples = []

    cn_string, cn_type = (None, None)
    if len(item_cn_tuples) > 0:
        (cn_string, cn_type) = item_cn_tuples[0]
    elif len(bib_cn_tuples) > 0:
        (cn_string, cn_type) = bib_cn_tuples[0]
    return {'callnumber': cn_string, 'callnumber_type': cn_type}


def extract_checkout_info(item):
    """
    Extract info about the current check out from `item`.
    """
    info = {}
    try:
        checkout = item.checkout_set.all()[0]
    except IndexError:
        return info
    info['due_date'] = checkout.due_gmt
    info['checkout_date'] = checkout.checkout_gmt
    info['overdue_date'] = checkout.overdue_gmt
    info['recall_date'] = checkout.recall_gmt
    info['loan_rule'] = checkout.loanrule_code_num
    info['renewal_count'] = checkout.renewal_count
    info['overdue_count'] = checkout.overdue_count
    return info


def extract_fixedfields(item):
    """
    Extract fixed fields from the provided ItemRecord object, `item`.
    """
    fields = {}
    fields['record_id'] = item.record_metadata.get_iii_recnum(False)
    fields['date_created'] = item.record_metadata.creation_date_gmt
    fields['date_last_updated'] = item.record_metadata.record_last_updated_gmt
    fields['copy_number'] = item.copy_num
    fields['last_checkin'] = item.last_checkin_gmt
    
    try:
        fields['location_code'] = item.location.code
        fields['location_name'] = item.location.locationname_set.all()[0].name
    except models.Location.DoesNotExist:
        fields['location_code'] = 'none'
        fields['location_name'] = 'None'

    fields['gift_stats'] = item.icode1
    fields['suppress_code'] = item.icode2
    fields['last_checkin_stat_group'] = item.checkin_statistics_group.code_num
    fields['last_checkout_stat_group'] = item.checkout_statistic_group.code_num
    fields['status_code'] = item.item_status.code
    fields['status_name'] = item.item_status.itemstatuspropertyname_set.all()[0].name
    fields['itype_code'] = item.itype_id
    fields['itype_name'] = item.itype.itypepropertyname_set.all()[0].name
    fields['price'] = item.price
    fields['checkout_total'] = item.checkout_total
    fields['last_ytd_checkout_total'] = item.last_year_to_date_checkout_total
    fields['ytd_checkout_total'] = item.year_to_date_checkout_total
    fields['internal_use_count'] = item.internal_use_count
    fields['copy_use_count'] = item.copy_use_count
    fields['iuse3_count'] = item.use3_count
    fields['imessage_code'] = item.item_message_code
    fields['opac_message_code'] = item.opac_message_code
    return fields


def extract_varfields(item):
    """
    Extract varfields from the provided ItemRecord object, `item`.
    """
    varfield_tag_mapping = {
        'b': 'barcodes',
        'v': 'volumes',
        'm': 'messages',
        'x': 'x_notes',
        'n': 'n_notes',
        'p': 'public_item_notes'
    }
    fields = {}
    varfields = item.record_metadata.varfield_set.order_by('varfield_type_code', 'occ_num')
    for tag, fieldname in varfield_tag_mapping.iteritems():
        fields[fieldname] = [vf.field_content for vf in varfields if vf.varfield_type_code == tag]
    return fields


def extract(item):
    """
    Extract all fields from the provided ItemRecord object, `item`.
    """
    callnumber = extract_callnumber(item)
    checkout = extract_checkout_info(item)
    varfields = extract_varfields(item)
    fixedfields = extract_fixedfields(item)

    fields = {}

    fields['due_date'] = checkout.get('due_date', None)
    fields['checkout_date'] = checkout.get('checkout_date', None)
    fields['overdue_date'] = checkout.get('overdue_date', None)
    fields['recall_date'] = checkout.get('recall_date', None)
    fields['loan_rule'] = checkout.get('loan_rule', None)
    fields['renewal_count'] = checkout.get('renewal_count', None)
    fields['overdue_count'] = checkout.get('overdue_count', None)

    fields['callnumber'] = callnumber.get('callnumber', None)
    fields['callnumber_type'] = callnumber.get('callnumber_type', None)

    fields.update(fixedfields)
    fields.update(varfields)
    
    return fields
