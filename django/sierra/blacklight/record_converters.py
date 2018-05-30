"""
Contains RecordConverter class and implementations.
"""

from __future__ import unicode_literals
import logging
import collections

from . import sierrabibstractor
from . import sierraitemstractor


# set up logger, for debugging
logger = logging.getLogger('sierra.custom')


class RecordConverter(object):
    """
    Convert data from one format to another.
    """
    def __init__(self, field_converters):
        super(RecordConverter, self).__init__()
        self.field_converters = field_converters

    def convert(self, in_data):
        output = {}
        for fname, convert_field in self.field_converters.iteritems():
            output[fname] = convert_field(in_data)
        return output


class SierraBibToUntbib(object):
    """
    Convert data from a Sierra BibRecord to a Untbib format.
    """
    def __init__(self, bibfield_map=None, itemfield_map=None):
        self.bib_converter = RecordConverter(bibfield_map)
        self.item_converter = RecordConverter(itemfield_map)

    def convert(self, rec):
        extracted_bib = sierrabibstractor.extract(rec)
        bib_fields = self.bib_converter.convert({'bib': extracted_bib})
        bib_fields['items'] = []
        items = [i.item_record for i in rec.bibrecorditemrecordlink_set.all()]
        for item in items:
            extracted_item = sierraitemstractor.extract(item)
            bibitem = {'bib': extracted_bib, 'item': extracted_item}
            bib_fields['items'].append(self.item_converter.convert(bibitem))
        return bib_fields


class UntbibToSolr(object):
    """
    Convert data from a Untbib to a Solr dict format.
    """
    def __init__(self, solrfield_map=None):
        self.solr_converter = RecordConverter(solrfield_map)

    def convert(self, rec):
        return self.solr_converter.convert(rec)

