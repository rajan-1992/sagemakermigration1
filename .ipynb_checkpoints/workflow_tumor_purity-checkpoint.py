import pdb
import argparse
import os
import sys
import openslide
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import sklearn
import pickle as pkl
import numpy as np

from sklearn.model_selection import StratifiedKFold

from DP_lib import img_classifier, perf_eval, util_tumor_purity

import pandas as pd

# set up logging
import logging
logging.basicConfig(format='%(levelname)s:%(message)s', level= logging.INFO)
logging.basicConfig(format='%(levelname)s:%(message)s', level= logging.DEBUG)



def workflow(input_files, model_path= None, output_dir= 'output/test/', bs= 2*256, tile_size= 224):
    '''
    tumor purity workflow.
    
    parameters:
    input_files: list of input files
    model_path: path to model
    output_dir: output directory
    bs: batch size
    tile_size: tile size

    '''
    img_cls_for_segmaps= ['Tumor', 'Stroma', 'Connective tissue',  'Necrosis', 'Lymphocytes', 'Normal', 'RBCs',  'WBCs', 'Liver', 'Glass/Blank']

    # output_TNBC_preds= 'output/multi_preds_cv5_cnn_export7_TNBC_224px/'

    # define files for annotation, model, prediction output, etc.

    db_version= 'export7'

    # img_base_dir= 'output/export/clusters/'

    bioset_file= 'data/GEN1046/GEN1046_meta_bioset_%s.csv' % db_version

    model_base_name= 'model_MLC_%s_bio_c10_lr0.01_stage' % db_version
    
    if model_path is None:
        model_path= model_base_name + "3_fold"

    logging.info('GPU available: %g' % torch.cuda.device_count())
    logging.info('model path: %s' % model_path)
    logging.info('output dir: %s' % output_dir)
    logging.info('reference dataset: %s' % bioset_file)
    
    # print("* Loading reference dataset %s" % bioset_file)
    dat_meta_bioset= pd.read_csv(bioset_file, index_col=0)

    skf= StratifiedKFold(n_splits= 5, shuffle= True, random_state= 123 )

    # NOTE: update this so we do not depend on the original meta data and splits
    print("* Loading model %s" % model_path)
    cv_models, df_cv= img_classifier.get_cv5_models(dat_meta_bioset, skf, 
            model_path) #'model_MLC_export7_bio_c10_lr0.01_stage3_fold')

    vocab= img_classifier.get_vocab(cv_models[0])

    # output_dir= 'output/test/multi_preds_cv5_cnn_export7_batch2_224px/'

    #batch2_files= [
    #    'data/pathology_lab/mirror_Y_drive/1224670B Ovarian Cancer.svs',
    #'data/pathology_lab/mirror_Y_drive/1243341B Ovarian Cancer.svs',
    #'data/pathology_lab/mirror_Y_drive/1243343B Ovarian Cancer.svs',]

    for fname in input_files:
        logging.info("working on %s" % fname)
        img_classifier.make_segmaps(cv_models, [fname], outdir= output_dir, 
            cls= img_cls_for_segmaps, bs= bs, tile_size= tile_size, useGlass= True)

        samp_name= os.path.basename(fname).replace(".svs", '')

        out_halo_file= "{}/{}_halo.annotations".format(output_dir, samp_name)
        pkl_file= "{}/{}.svs.pkl".format(output_dir, samp_name)

        logging.debug(f"{fname} -> {pkl_file} -> {out_halo_file}")

        # pdb.set_trace()

        slide_preds= pkl.load(open(pkl_file,  'rb'))  
        img_classifier.export_halo_xml_from_img(fname, slide_preds['slide_preds'], slide_preds['coord'], out_halo_file, ['Tumor'], tile_size= tile_size, minlen= 1, show= True)
            
def main():
    # add argparse to get the following args:
    # input files, output dir, model path, etc. 
    # option to show file specs

    parser= argparse.ArgumentParser(description= 'workflow for tumor purity')
    parser.add_argument('--show_image_specs', action= 'store_true', help= 'show image specs')
    parser.add_argument('--input_files', nargs= '+', default= [], help= 'input files to process', required= True)
    parser.add_argument('--output_dir', help= 'output directory', default= 'output/workflow_tumor_purity')
    parser.add_argument('--model_path', help= 'path to model')
    # parser.add_argument('--use_glass', action= 'store_true', help= 'use glass')
    parser.add_argument('--bs', type= int, default= 2*256, help= 'batch size')
    parser.add_argument('--tile_size', type= int, default= 224, help= 'tile size')   
    
    args= parser.parse_args()
    # print(args.input_files)
    # print(args.show_image_specs)

    assert len(args.input_files) > 0, "no input files"
    assert args.output_dir is not None, "no output directory"

    input_files= args.input_files
    # if type(input_files) is str:
    #     input_files= [input_files]

    print(input_files)
    # sys.exit()

    if args.show_image_specs:
        print(util_tumor_purity.show_image_specs(input_files))
        sys.exit()
    else:
        workflow(input_files, args.model_path, args.output_dir, args.bs, args.tile_size)

if __name__ == '__main__':
    main()
