"""
Exporters module for catalog-api `blacklight` app.
"""

from __future__ import unicode_literals
import logging
import subprocess
import os
import re
import shlex
import sys, traceback

import pysolr

from django.conf import settings

from export import exporter
from export.basic_exporters import BibsToSolr, BibsDownloadMarc
from export.sierra2marc import S2MarcBatch
import record_converters


# set up logger, for debugging
logger = logging.getLogger('sierra.custom')


class BaseBibsDownloadMarc(BibsDownloadMarc):
    """
    This is a base exporter class for converting Sierra data to MARC
    records, to be used with a BaseSolrMarcBibsToSolr class.

    Subclass and specify a different s2marc_batch_class to change how
    Sierra records are converted to MARC.
    """

    s2marc_batch_class = S2MarcBatch

    def export_records(self, records, vals={}):
        log_label = self.__class__.__name__
        batch = type(self).s2marc_batch_class(records)
        out_recs = batch.to_marc()
        try:
            if 'marcfile' in vals:
                marcfile = batch.to_file(out_recs, vals['marcfile'])
            else:
                vals['marcfile'] = batch.to_file(out_recs, append=False)
        except IOError as e:
            self.log('Error', 'Error writing to output file: {}'.format(e), 
                     log_label)
        else:
            for e in batch.errors:
                self.log('Warning', 'Record {}: {}'.format(e.id, e.msg),
                         log_label)
            if 'success_count' in vals:
                vals['success_count'] += batch.success_count
            else:
                vals['success_count'] = batch.success_count
        return vals


class BaseSolrMarcBibsToSolr(BibsToSolr):
    """
    This is a base exporter class for creating bib exporters that run
    via SolrMarc.

    Subclass and specify the `cores` class attr so that the `bibs` dict
    element points to the correct Solr core and the `bib2marc_class`
    to point to a BaseBibsDownloadMarc subclass, if needed.
    """
    
    bib2marc_class = BaseBibsDownloadMarc
    cores = {'bibs': 'SPECIFY_SOLR_CORE_HERE'}

    @classmethod
    def solr_url(cls, ctype):
        host, port = settings.SOLR_HOST, settings.SOLR_PORT
        return 'http://{}:{}/solr/{}'.format(host, port, cls.cores[ctype])

    @classmethod
    def solr_conn(cls, ctype):
        return pysolr.Solr(cls.solr_url(ctype))

    def export_records(self, records, vals={}):
        log_label = type(self).__name__
        bibs_solr_url = type(self).solr_url('bibs')
        bibs_indprop = '{}_index.properties'.format(type(self).cores['bibs'])
        jarfile = ('{}/../../solr/solrmarc/StanfordSearchWorksSolrMarc.jar'
                   '').format(settings.PROJECT_DIR)
        config_file = settings.SOLRMARC_CONFIG_FILE
        filedir = settings.MEDIA_ROOT
        if filedir[-1] != '/':
            filedir = '{}/'.format(filedir)
        bib_converter = self.bib2marc_class(
            self.instance.pk, self.export_filter, self.export_type,
            self.options
        )
        ret_vals = bib_converter.export_records(records, vals={})
        filename = ret_vals['marcfile']
        filepath = '{}{}'.format(filedir, filename)

        cmd = ('java -Xmx1g -Dsolr.hosturl="{}" '
               '-Dsolrmarc.indexing.properties="{}" '
               '-jar "{}" {} {}').format(bibs_solr_url, bibs_indprop, jarfile,
                                         config_file, filepath)

        try:
            output = subprocess.check_output(shlex.split(cmd),
                                             stderr=subprocess.STDOUT,
                                             shell=False,
                                             universal_newlines=True)
            output = output.decode('unicode-escape')
        except subprocess.CalledProcessError as e:
            error_lines = e.output.split("\n")
            for line in error_lines:
                self.log('Error', line)
            self.log('Error', 'Solrmarc process did not run successfully.',
                     log_label)
        else:
            error_lines = output.split("\n")
            del(error_lines[-1])
            if error_lines:
                for line in error_lines:
                    line = re.sub(r'^\s+', '', line)
                    if re.match(r'^WARN', line):
                        self.log('Warning', line, log_label)
                    elif re.match(r'^ERROR', line):
                        self.log('Error', line, log_label)

        os.remove(filepath)
        return vals

    def get_record_id(self, record):
        return 'base.bibrecord.{}'.format(record.id)

    def delete_records(self, records, vals={}):
        bibs_solr = type(self).solr_conn('bibs')
        log_label = type(self).__name__
        for r in records:
            try:
                bibs_solr.delete(id=self.get_record_id(r), commit=False)
            except Exception as e:
                ex_type, ex, tb = sys.exc_info()
                logger.info(traceback.extract_tb(tb))
                self.log('Error', 'Record {}: {}'
                         ''.format(str(r), e), log_label)
        return vals

    def final_callback(self, vals={}, status='success'):
        bibs_solr = type(self).solr_conn('bibs')
        log_label = type(self).__name__
        self.log('Info', 'Committing updates to Solr...', log_label)
        bibs_solr.commit()


class BaseNonSolrmarcBibsToSolr(exporter.Exporter):
    """
    Export Bibs from the Sierra DB and load into Solr; no Solrmarc.

    This is a base class for building Export processes to load Bib
    records from Sierra into Solr, WITHOUT using Solrmarc (or Haystack,
    for that matter).

    The simplest way to use this is to subclass it, then override the
    class attributes `cores`, `sierrabib_to_untbib`, and
    `untbib_to_solr`.

    `cores` is a dictionary defining the solr core(s) to load records
    into.

    `sierrabib_to_untbib` is a record converter object that will
    convert a Sierra BibRecord object to a dict that can then be passed
    to `untbib_to_solr`.

    `untbib_to_solr` is another record converter object that will
    convert the dict created by the `sierrabib_to_untbib` conversion
    into a data dict that you can pass to pysolr to load.

    The record converter classes shown in the class definition below
    are placeholders, but they're good default choices to use--just
    pass the appropriate parameters specifying various field mappings
    to instantiate them. Or you can use different classes.
    """

    cores = {'bibs': 'SPECIFY_SOLR_CORE_HERE'}
    sierrabib_to_untbib = record_converters.SierraBibToUntbib(
        bibfield_map={
            # specify bib field mapping here
        },
        itemfield_map={
            # specify item field mapping here
        }
    )
    untbib_to_solr = record_converters.UntbibToSolr(
        solrfield_map={
            # specify solr field mapping here
        }
    )

    max_rec_chunk = 1000
    model_name = 'BibRecord'
    deletion_filter = [
        {
            'deletion_date_gmt__isnull': False,
            'record_type__code': 'b'
        }
    ]
    prefetch_related = [
        'record_metadata__varfield_set',
        'record_metadata__controlfield_set',
        'record_metadata__leaderfield_set',
        'bibrecorditemrecordlink_set',
        'bibrecorditemrecordlink_set__item_record',
        'bibrecorditemrecordlink_set__item_record__record_metadata',
        'bibrecordproperty_set',
        'bibrecordproperty_set__material__materialpropertyname_set'
    ]
    select_related = ['record_metadata']

    @classmethod
    def solr_url(cls, ctype):
        host, port = settings.SOLR_HOST, settings.SOLR_PORT
        return 'http://{}:{}/solr/{}'.format(host, port, cls.cores[ctype])

    @classmethod
    def solr_conn(cls, ctype):
        return pysolr.Solr(cls.solr_url(ctype))

    def format_error_msg(self, error, record=None):
        msg = error
        if record is not None:
            record_id = self.get_record_id(record)
            msg = '{}: {}'.format(record_id, msg)
        return msg

    def export_records(self, records, vals={}):
        log_label = type(self).__name__
        bibs_solr = type(self).solr_conn('bibs')
        cls = type(self)
        solr_records = []
        for rec in records:
            try:
                untbib = self.sierrabib_to_untbib.convert(rec)
            except Exception as e:
                msg = self.format_error_msg('Bib conversion error: {}'.format(e), rec)
                self.log('Error', msg, log_label)
            try:
                solr_dict = self.untbib_to_solr.convert(untbib)
            except Exception as e:
                msg = self.format_error_msg('Solr conversion error: {}'.format(e), rec)
                self.log('Error', msg, log_label)
            else:
                solr_records.append(solr_dict)
        try:
            bibs_solr.add(solr_records, commit=False)
        except Exception as e:
            self.log('Info', solr_records, log_label)
            msg = self.format_error_msg('Indexing error: {}'.format(e))
            self.log('Error', msg, log_label)
        return vals

    def delete_records(self, records, vals={}):
        log_label = type(self).__name__
        bibs_solr = type(self).solr_conn('bibs')
        for rec in records:
            record_id = self.get_record_id(rec)
            try:
                bibs_solr.delete(id=record_id, commit=False)
            except Exception as e:
                msg = self.format_error_msg(e, record)
                self.log('Error', msg, log_label)
        return vals
    
    def get_record_id(self, record):
        try:
            return record.record_metadata.get_iii_recnum(False)
        except AttributeError:
            return record.get_iii_recnum(False)

    def final_callback(self, vals={}, status='success'):
        log_label = type(self).__name__
        bibs_solr = type(self).solr_conn('bibs')
        self.log('Info', 'Committing updates to Solr...', log_label)
        bibs_solr.commit()


class BibsToBlacklightStaging(exporter.Exporter):
    """
    This is a temporary placeholder.

    Once our Blacklight staging/beta site is up, this will become the
    primary Exporter class for loading bib records into our Blacklight
    Solr instance (blacklight-staging), which has yet to be created.

    Changes made and features created using an exporters_* file should
    be incorporated into this class to be deployed on staging.

    """
    pass
