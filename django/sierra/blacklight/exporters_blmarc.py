"""
Exporters module for catalog-api `blacklight` app, bl-marc version.
"""

from __future__ import unicode_literals
import logging

import pysolr

from django.conf import settings

from base import models
from utils import helpers
from export import exporter
from .exporters import BaseNonSolrmarcBibsToSolr
from . import record_converters
from . import field_converters


# set up logger, for debugging
logger = logging.getLogger('sierra.custom')


class BibsToBlacklightMarc(BaseNonSolrmarcBibsToSolr):
    """
    Export Bibs from the Sierra DB and load into Solr; no Solrmarc.

    For Blacklight, bl-marc Solr version.
    """
    cores = {'bibs': 'bl-marc'}
    sierrabib_to_untbib = record_converters.SierraBibToUntbib(
        bibfield_map={
            'record_id': field_converters.sierrabib_to_record_id,
            'person_author': field_converters.sierrabib_to_person_author,
            'contributors': field_converters.sierrabib_to_contributors,
        },
        itemfield_map={
            'barcode': field_converters.itemrecord_to_barcode,
            'location': field_converters.itemrecord_to_location,
            'callnumber': field_converters.itemrecord_to_callnumber,
        }
    )
    untbib_to_solr = record_converters.UntbibToSolr(
        solrfield_map={
            'id': field_converters.untbib_to_id,
            'person_author_search_fullname_forms': field_converters.untbib_to_person_author_search_fullname_forms,
            'person_author_search_bestname': field_converters.untbib_to_person_author_search_bestname,
            'person_author_display': field_converters.untbib_to_person_author_display,
            'person_author_facet': field_converters.untbib_to_person_author_facet,
            'callnumbers_display': field_converters.untbib_to_callnumbers_display,
            'callnumbers_normalized': field_converters.untbib_to_callnumbers_normalized,
        }
    )
