"""
Contains Sierra field data conversion functions and RecordConverter.
"""

from __future__ import unicode_literals
import logging
import collections

# set up logger, for debugging
logger = logging.getLogger('sierra.custom')


class RecordConverter(object):
    """
    Convert data from one format to another, w/converters and parsers.
    """

    def __init__(self, field_converters, parsers=None):
        super(RecordConverter, self).__init__()
        self.field_converters = field_converters
        if parsers is not None:
            Parsers = collections.namedtuple('Parsers', parsers.keys())
            self.parsers = Parsers(**parsers)

    def convert(self, input):
        output = {}
        for fname, convert_field in self.field_converters.iteritems():
            output[fname] = convert_field(input, self.parsers)
        return output


# Conversion functions

def fieldset_to_main_author(fieldset, parsers):
    pass


def fieldset_to_contributors(fieldset, parsers):
    pass


def itemrecord_to_barcode(bibitem, parsers):
    pass


def itemrecord_to_location(bibitem, parsers):
    pass


def itemrecord_to_callnumber(bibitem, parsers):
    pass


def untbib_to_main_author_search(untbib, parsers):
    pass


def untbib_to_main_author_display(untbib, parsers):
    pass

