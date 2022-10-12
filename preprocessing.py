
import pandas as pd
import os
import sys
import boto3
import sagemaker
import argparse
from pathlib import Path
import subprocess

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
parser.add_argument('--download', nargs='+', default= [])
parser.add_argument('--dryrun', action='store_true')

args, _ = parser.parse_known_args()

################################################
### download additional input files
# s3_download(args.download, '/opt/ml/processing/input/downloads')
for i in args.download:
    cmd= "aws s3 cp {} {} --recursive --quiet".format(i, '/opt/ml/processing/input/downloads')
    run_cmd(cmd)

################################################
### check input directory to make sure files were copied from s3

input_dir= '/opt/ml/processing/input'
dir_out= "/opt/ml/processing/outputs"

print('\n')

print('** checking input directory:', input_dir)


list_files(input_dir)    

################################################
### main workflow starts here
################################################

todo= []
for i in args.input:
    newfile= '{}.csv'.format(i)
    print('adding output file', newfile)
    todo.append(newfile)

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

# get TCGA files

print("getting TCGA file list from S3...")
all_tcga_files= sagemaker.s3.S3Downloader.list('s3://gmb-ds-dbgap/data/Digital_pathology/TCGA/')
all_tcga_files= [i for i in all_tcga_files if i.endswith('.svs')]
dat_TCGA= pd.DataFrame()
dat_TCGA['File']= all_tcga_files
dat_TCGA['Cancer']= dat_TCGA['File'].replace(".*TCGA/", "", regex= True).replace("/.*", '', regex= True)
dat_TCGA['Image']= dat_TCGA['File'].transform(lambda x: os.path.basename(x))


print("generating output files")

ofile= os.path.join(dir_out, 'all_TCGA.csv')

dat_TCGA.to_csv(ofile)

# directly uploading to s3
sagemaker.s3.S3Uploader.upload(ofile, 's3://gmb-ds-dbgap/test_dir/sagemaker_upload')

# write some random files
for i in outfiles:
    fname= os.path.join(dir_out, i)
    print('writing to ', fname)
    dat.to_csv(fname)

### example output directory
print('\n')
print('** checking processing directory:')
list_files('/opt/ml/processing/')    

# all files under /opt/ml/processing/outputs will be automatically copied to the sagemaker s3 bucket
