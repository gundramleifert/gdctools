#!/usr/bin/env python

import csv
import os
from ..common import safeMakeDirs, map_blank_to_na, writeCsvFile
from ..meta import tcga_id, diced_file_path, diced_file_path_partial

def process(file_dict, infile, outdir):
    # Should only produce one file
    filepath = diced_file_path(outdir, file_dict)
    filepath_partial = diced_file_path_partial(outdir, file_dict)
    _tcga_id = tcga_id(file_dict)
    rawfile = open(infile, 'r')
    csvfile = csv.reader(rawfile, dialect='excel-tab')

    csvfile_with_ids = tsv2idtsv(csvfile, _tcga_id)
    csvfile_with_NAs = map_blank_to_na(csvfile_with_ids)

    safeMakeDirs(outdir)
    writeCsvFile(filepath_partial, csvfile_with_NAs)
    os.rename(filepath_partial, filepath)

    rawfile.close()

def tsv2idtsv(csvfile, sampleName):
    header = next(csvfile)
    yield ['SampleId'] + header

    for row in csvfile:
        yield [sampleName] + row
