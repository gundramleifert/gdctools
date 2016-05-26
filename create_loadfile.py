#!/usr/bin/env python
# encoding: utf-8

# Front Matter {{{
'''
Copyright (c) 2016 The Broad Institute, Inc.  All rights are reserved.

gdc_mirror: this file is part of gdctools.  See the <root>/COPYRIGHT
file for the SOFTWARE COPYRIGHT and WARRANTY NOTICE.

@author: Timothy DeFreitas
@date:  2016_05_25
'''

# }}}
from __future__ import print_function

from GDCtool import GDCtool
import translator
import gdc
import logging
import os
import csv

class create_loadfile(GDCtool):

    def __init__(self):
        super(create_loadfile, self).__init__(version="0.1.0")
        cli = self.cli

        desc =  'Create a Firehose loadfile from diced Genomic Data Commons (GDC) data'
        cli.description = desc

        cli.add_argument('-d', '--dice-directory', 
                         help='Root of diced data directory')
        cli.add_argument('-l', '--loadfile-directory', 
                         help='Where generated loadfiles will be placed')
        cli.add_argument('datestamp', nargs='?',
                         help='Dice using metadata from a particular date.'\
                         'If omitted, the latest version will be used')

    def create_loadfiles(self):

        #Iterate over programs/projects in diced root
        diced_root = os.path.abspath(self.options.dice_directory)
        load_root = os.path.abspath(self.options.loadfile_directory)


        for program in immediate_subdirs(diced_root):
            prog_root = os.path.join(diced_root, program)
            projects = immediate_subdirs(prog_root)

            #This dictionary contains all the data for the loadfile. 
            #Keys are the entity_ids, values are dictionaries for the columns in a loadfile
            master_load_dict = dict()

            for project in projects:
                logging.info("Generating loadfile data for " + project)
                proj_path = os.path.join(prog_root, project)
                timestamp = meta.get_timestamp(proj_path, self.options.datestamp)
                # Keep track of the created annotations
                annots = set()
                for annot, reader in get_diced_metadata(proj_path, self.options.datestamp):
                    logging.info("Reading data for " + annot)
                    annots.add(annot)
                    for row in reader:
                        #Add entry for this entity into the master load dict
                        #eid = row['entity_id']
                        samp_id = sample_id(project, row)

                        if samp_id not in master_load_dict:
                            master_load_dict[samp_id] = master_load_entry(project, row)
                        #Filenames in metadata begin with diced root, 
                        filepath = os.path.join(os.path.dirname(diced_root), row['filename'])
                        master_load_dict[samp_id][annot] = filepath

                proj_load_root = os.path.join(load_root, program, project)
                if not os.path.isdir(proj_load_root):
                    os.makedirs(proj_load_root)

                samples_loadfile_name = ".".join([project,timestamp, "Sample", "loadfile", "txt"])
                sset_loadfile_name = ".".join([project, timestamp, "Sample_Set", "loadfile", "txt"])
                samples_loadfile = os.path.join(proj_load_root, samples_loadfile_name)
                sset_loadfile = os.path.join(proj_load_root, sset_loadfile_name)

                logging.info("Writing samples loadfile to " + samples_loadfile)
                write_master_load_dict(master_load_dict, annots, samples_loadfile)
                logging.info("Writing sample set loadfile to " + sset_loadfile)
                write_sample_set_loadfile(samples_loadfile, sset_loadfile)




    def execute(self):
        super(create_loadfile, self).execute()
        opts = self.options
        logging.basicConfig(format='%(asctime)s[%(levelname)s]: %(message)s',
                            level=logging.INFO)
        self.create_loadfiles()

# Could use get_metadata, but since the loadfile generator is separate, it makes sense to divorce them
def get_diced_metadata(project_root, datestamp=None):
    project_root = project_root.rstrip(os.path.sep)
    project = os.path.basename(project_root)

    for dirpath, dirnames, filenames in os.walk(project_root, topdown=True):
        # Recurse to meta subdirectories 
        if os.path.basename(os.path.dirname(dirpath)) == project:
            for n, subdir in enumerate(dirnames):
                if subdir != 'meta': del dirnames[n]

        if os.path.basename(dirpath) == 'meta':
            #If provided, only use the metadata for a given date, otherwise use the latest metadata file
            meta_files =  sorted(filename for filename in filenames \
                                 if datestamp is None or datestamp in filename)
            #Annot name is the parent folder
            annot=os.path.basename(os.path.dirname(dirpath))
            
            if len(meta_files) > 0:
                with open(os.path.join(dirpath, meta_files[-1])) as f:
                    #Return the annotation name, and a dictReader for the metadata
                    yield  annot, csv.DictReader(f, delimiter='\t')

def immediate_subdirs(path):
    return [d for d in os.listdir(path) 
            if os.path.isdir(os.path.join(path, d))]

#TODO: This should come from a config file
def sample_type_lookup(etype):
    '''Convert long form sample types into letter codes.'''
    lookup = {
        "Blood Derived Normal" : ("NB", "10"),
        "Primary Tumor" : ("TP", "01"),
        "Primary Blood Derived Cancer - Peripheral Blood" : ("TB", "03"),
        "Metastatic" : ("TM", "06"),
        "Solid Tissue Normal": ("NT", "11")

    }

    return lookup[etype]

def sample_id(project, row_dict):
    '''Create a sample id from a row dict'''
    if not project.startswith("TCGA-"):
        raise ValueError("Only TCGA data currently supported, (project = {0})".format(project))

    cohort = project.replace("TCGA-", "")
    entity_id = row_dict['entity_id']
    indiv_base = entity_id.replace("TCGA-", "")
    entity_type = row_dict['entity_type']
    sample_type, sample_code = sample_type_lookup(entity_type)

    samp_id = "-".join([cohort, indiv_base, sample_type])
    return samp_id

def master_load_entry(project, row_dict):
    d = dict()
    if not project.startswith("TCGA-"):
        raise ValueError("Only TCGA data currently supported, (project = {0})".format(project))

    cohort = project.replace("TCGA-", "")
    entity_id = row_dict['entity_id']
    indiv_base = entity_id.replace("TCGA-", "")
    entity_type = row_dict['entity_type']
    sample_type, sample_code = sample_type_lookup(entity_type)

    samp_id = "-".join([cohort, indiv_base, sample_type])
    indiv_id = "-".join([cohort, indiv_base])
    tcga_sample_id = "-".join([entity_id, sample_code])

    d['sample_id'] = samp_id
    d['individual_id'] = indiv_id
    d['sample_type'] = sample_type
    d['tcga_sample_id'] = tcga_sample_id

    return d

def write_master_load_dict(ld, annots, outfile):
    _FIRST_HEADERS = ["sample_id", "individual_id", "sample_type", "tcga_sample_id"]
    annots = sorted(annots)
    with open(outfile, 'w') as out:
        #Header line
        out.write("\t".join(_FIRST_HEADERS) + "\t" + "\t".join(annots)+"\n")


        #Loop over sample ids, writing entries in outfile
        #NOTE: requires at least one annot
        for sid in ld:
            this_dict = ld[sid]
            line = "\t".join([this_dict[h] for h in _FIRST_HEADERS]) + "\t"
            line += "\t".join([this_dict.get(a, "__DELETE__") for a in annots]) + "\n"
            out.write(line)

def write_sample_set_loadfile(sample_loadfile, outfile):
    sset_data = "sample_set_id\tsample_id\n"
    with open(sample_loadfile) as slf:
        reader = csv.DictReader(slf, delimiter='\t')
        for row in reader:
            samp_id = row['sample_id']
            #This sample belongs to the cohort sample set
            sset_data += samp_id.split("-")[0] + "\t" + samp_id + "\n"
            #And the type-specific set
            sset_data += samp_id.split("-")[0] + "-" + samp_id.split("-")[-1] + "\t" + samp_id + "\n"

    with open(outfile, "w") as out:
        out.write(sset_data)

if __name__ == "__main__":
    create_loadfile().execute()