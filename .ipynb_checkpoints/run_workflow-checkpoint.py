
import pandas as pd
import os
import sys
import boto3
import sagemaker
import argparse
from pathlib import Path
import subprocess
import logging

### setup
os.environ['AWS_DEFAULT_REGION'] = 'eu-central-1'

### utility functions
def list_files(dirname):
    path = Path(dirname) # '/home/janbodnar/Documents/prog/python/')

    for e in path.rglob('*'):
        print(e)
        
def run_cmd(cmd, dryrun= False, check= True):
    print(cmd)
    if dryrun is not True:
        # print("exec")
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        out, err= p.communicate()
        if err is not None:
            err= err.decode('UTF-8')
        if out is not None:
            out= out.decode('UTF-8')
        p_status = p.wait()

        print(out)
        
        if p_status != 0:
            print("** Non-zero status returned! **")
            if err is not None:
                print(err)
            if check:
                assert p_status==0, "Command execution failed. Abort!"
        # subprocess.run(cmd, shell= True, check= check)
            
### parse arguments
parser = argparse.ArgumentParser()

parser.add_argument('--input', nargs='+', default= [])
parser.add_argument('--app-data', type= str, default= None)
parser.add_argument('--download', nargs='+', default= [])
parser.add_argument('--show_image_specs', action= 'store_true', help= 'show image specs')
parser.add_argument('--base_dir', default= '/opt/ml/processing/')
parser.add_argument('--dryrun', action='store_true')

args, _ = parser.parse_known_args()

logging.basicConfig(level=logging.INFO)
logging.info("Tumor purity workflow")
logging.info("input: %s" % args.input)
logging.info("app-data: %s" % args.app_data)
logging.info("base_dir: %s" % args.base_dir)
logging.info("download: %s" % args.download)


################################################
### download additional input files
# s3_download(args.download, '/opt/ml/processing/input/downloads')

#for i in args.download:
#    cmd= "aws s3 cp {} {} --recursive --quiet".format(i, '/opt/ml/processing/input/downloads')
#    run_cmd(cmd)

# DOWNLOAD_DIR= '/opt/ml/processing/input/downloads'
BASE_DIR= args.base_dir
DOWNLOAD_DIR= BASE_DIR+ '/input/downloads'

to_process= []
if args.input:
    for i in args.input:
        if i.startswith('s3://'):
            local_input= DOWNLOAD_DIR+ "/"+ os.path.basename(i)
            logging.info("downloading {} to {}".format(i, local_input))
            to_process.append(local_input)
            
            if not os.path.exists(local_input):
                sagemaker.s3.S3Downloader.download(i, local_path= DOWNLOAD_DIR)
            else:
                logging.info("file exists. skipped.")

logging.info("to process: %s" % to_process)    

if args.app_data:
    app_file= args.app_data
    local_app= DOWNLOAD_DIR+ "/"+ os.path.basename(app_file)
    
    logging.info("downloading {} -> {}".format(app_file, local_app))
    if os.path.exists(local_app):
        logging.info("%s already exists. skipped." % local_app)
    else:
        sagemaker.s3.S3Downloader.download(app_file, local_path= DOWNLOAD_DIR)
    
        cmd= "tar xfz %s" % local_app
        run_cmd(cmd)
    
################################################
### check input directory to make sure files were copied from s3

input_dir= BASE_DIR+ "/input"
dir_out= BASE_DIR + "/output_workflow"

logging.info('Checking input directory: %s' % input_dir)

list_files(input_dir)    

if not os.path.isdir(dir_out):
    os.makedirs(dir_out)
    logging.info("Creating output directory: %s" % dir_out)
################################################
### main workflow starts here
###
### NOTE:
###    * Plug in real workflow here
################################################

out_specs_file= dir_out + "/summary_image_specs.csv"
# input_files=" ".join(args.input)
input_files= " ".join([ "'{}'".format(i) for i in to_process])
if args.show_image_specs:
    logging.info("extracting image specs")
    cmd= "python workflow_tumor_purity.py --input {} --output_dir {} --show_image_specs --output_file {}".format(input_files, dir_out, out_specs_file)
    logging.info(cmd)
    run_cmd(cmd)
else:
    logging.info("running tumor purity workflow")
    cmd= "python workflow_tumor_purity.py --input {} --output_dir {} ".format(input_files, dir_out)
    logging.info(cmd)
    run_cmd(cmd)

################################################
### fake workflow here
################################################
todo= []
#for i in args.input:
#    newfile= '{}.csv'.format(i)
#    print('adding output file', newfile)
#    todo.append(newfile)

if args.dryrun:
    print('dryrun')
    sys.exit()

#    sys.exit()


# sagemaker.Session(boto3.session.Session())

#
dat= pd.DataFrame({'num_legs': [2, 4, 8, 0],
                   'num_wings': [2, 0, 0, 0],
                   'num_specimen_seen': [10, 2, 1, 8]},
                  index=['falcon', 'dog', 'spider', 'fish'])

# dat.to_csv()

outfiles= ['abc.csv','A2.csv','A3.csv','blahblah.csv']+ todo

# write some random files
for i in outfiles:
    fname= os.path.join(dir_out, i)
    print('writing to ', fname)
    dat.to_csv(fname)
    
# get TCGA files

print("getting TCGA file list from S3...")
all_tcga_files= sagemaker.s3.S3Downloader.list('s3://gmb-ds-dbgap/data/Digital_pathology/TCGA/')
all_tcga_files= [i for i in all_tcga_files if i.endswith('.svs')]
dat_TCGA= pd.DataFrame()
dat_TCGA['File']= all_tcga_files
dat_TCGA['Cancer']= dat_TCGA['File'].replace(".*TCGA/", "", regex= True).replace("/.*", '', regex= True)
dat_TCGA['Image']= dat_TCGA['File'].transform(lambda x: os.path.basename(x))


logging.info("generating output files")
logging.info("output directory: %s" % dir_out)

ofile= os.path.join(dir_out, 'all_TCGA.csv')

dat_TCGA.to_csv(ofile)

###############################################
# end of workflow - upload results
###############################################
# directly uploading to s3
logging.info("uploading results to dedicated s3")
sagemaker.s3.S3Uploader.upload(ofile, 's3://gmb-ds-dbgap/test_dir/sagemaker_upload')



### example output directory
if False:
    print('\n')
    print('** checking processing directory:')
    list_files(BASE_DIR)    

# all files under /opt/ml/processing/outputs will be automatically copied to the sagemaker s3 bucket
