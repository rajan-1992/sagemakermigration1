# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/1046 segmap analysis - export 7.ipynb (unless otherwise specified).

__all__ = ['count_classes', 'quant_TILs', 'summarize_TME', 'make_TME_table', 'get_cluster_examples']

# Cell

# export

import glob
import pandas as pd
import numpy as np
import pickle as pkl
import seaborn as sns
import matplotlib.pyplot as plt
import scipy


# Cell

def count_classes(preds, vocab, verbose= True):
    '''
    count the number of tiles in each image class

    preds: predictions (scores, class predictions, binary predictions)
    vocab: image class labels

    '''

    cnt= {}
    for i in vocab:
        cnt[i]= np.asarray([ i in j for j in preds])
       # if verbose:
       #     print("{} -> {}".format(i, sum(cnt[i])))
    cnt['Non-background']= np.asarray([ 'Glass/Blank' not in j for j in preds])
    return cnt

# Cell

def quant_TILs(preds, vocab, threshold= .5, verbose= False):
    '''
    quantify TILs using predicted scores rather than binary calls

    threshold: min score for making a tumor call

    NOTE: we need vocab to be in the same order as the score matrix columns
    '''

    tumor_idx= vocab.index('Tumor')
    lymph_idx= vocab.index('Lymphocytes')

    if verbose:
        print('tumor index= {}, lymph index= {}'.format(tumor_idx, lymph_idx))

    # TIL_scores= (preds[:, tumor_idx]> .5) * (preds[:, lymph_idx]> .85) * preds[:, lymph_idx]

    TIL_scores= (preds[:, tumor_idx]> threshold)  * preds[:, lymph_idx]

    num_tumor= (preds[:, tumor_idx]> threshold).sum()
    return float(TIL_scores.sum()), int(num_tumor)

# Cell

def summarize_TME(counts, show= False):
    '''
    summarize the TME composition from tile counts in various image classes

    counts:
    show:
    '''
    cnt= {}
    for i in counts.keys():
        cnt[i]= [sum(counts[i])]
        if show:
            print("* {} -> {}".format(i, cnt[i][0]))


    # other items
    num_tumor= counts['Tumor'].sum()
    num_TIL_tumor= (counts['Tumor'] & counts['Lymphocytes']).sum()
    num_TIL_stroma= (counts['Stroma'] & counts['Lymphocytes']).sum()
    num_necrosis_tumor= (counts['Tumor'] & counts['Necrosis']).sum()


    pct_TIL_tumor= num_TIL_tumor/num_tumor*100
    pct_TIL_stroma= num_TIL_stroma/num_tumor*100
    pct_necrosis_tumor= num_necrosis_tumor/num_tumor*100

    out= pd.DataFrame(cnt)
    out['TIL in tumor']= [num_TIL_tumor]
    out['TIL in tumor (%)']= [pct_TIL_tumor]

    out['TIL in stroma']= [num_TIL_stroma]
    out['TIL in stroma (%)']= [pct_TIL_stroma]

    out['Necrosis in tumor']= [num_necrosis_tumor]
    out['Necrosis in tumor (%)']= [pct_necrosis_tumor]

    if show:
        print("TIL in tumor: {} ({:.2f}%)".format(num_TIL_tumor, pct_TIL_tumor))
        print("TIL in stroma: {} ({:.2f}%)".format(num_TIL_stroma, pct_TIL_stroma))
        print("Necrosis in tumor: {} ({:.2f}%)|".format(num_necrosis_tumor, pct_necrosis_tumor))
    return out

# Cell

import os

def make_TME_table(files, vocab, threshold= .5):
    all_counts= pd.DataFrame()
    for i in files:
        print('loading {}'.format(i))
        samp= os.path.basename(i).replace('.pkl','')
        dat_pred= pkl.load(open(i, 'rb'))

        quant_TIL, quant_tumor= quant_TILs(dat_pred[0][0], vocab, threshold= threshold)

        cnt_classes= count_classes(dat_pred[0][1], vocab)

        cc=summarize_TME(cnt_classes)
        cc['File']=[i]
        cc['Sample']=[samp]
        cc['Tumor (quant)']= quant_tumor
        cc['TIL in tumor (quant)']= quant_TIL
        cc['TIL in tumor (quant %)']= np.float16(quant_TIL)/ np.float16(quant_tumor) * 100
        cc['Tumor purity (% tiles)']= cc['Tumor']/ cc['Non-background']

        all_counts= all_counts.append(cc)
    return all_counts

# Cell

import os
from tqdm import tqdm

def get_cluster_examples(images, kmeans, n= 25, out= 'output/export/clusters', rnd= True, titles= False, run= False, **kwargs):
    '''
    export cluster examples and return the mapping between target and source images

    cid: cluster ID
    dataset:
    kmeans:
    n: number of samples per cluster
    rnd: randomly select from cluster images; otherwise take the first few images
    titles: show file index as title
    run: execute the image exporting commands

    '''

    if not os.path.exists(out):
        os.mkdir(out)
        print("creating output directory: {}".format(out))

    print("{} clusters found".format(kmeans.n_clusters))

    all_idx = np.array([*range(len(images))])

    all_cmd= []
    all_source= []
    all_target= []

    for cid in tqdm(range(kmeans.n_clusters)):
        print("exporting cluster {}".format(cid))
        to_do_idx= all_idx[kmeans.labels_== cid]
        if rnd:
            np.random.seed(0)
            to_do_idx= np.random.choice(to_do_idx, size= n)
        else:
            to_do_idx= to_do_idx[:n]

        example_imgs= [images[i][0] for i in to_do_idx ]
        print("{} images found for cluster {}".format(len(example_imgs), cid))

        # cmd= ["cp {} {}".format() for i in exampl

        source_img= ["{}".format(j) for i, j in enumerate(example_imgs)]
        target_img= ["{}/example_cluster{}_image{}.png".format(out, cid, i) for i, j in enumerate(example_imgs)]

        cmd= ["cp {} {}/example_cluster{}_image{}.png".format(j, out, cid, i) for i, j in enumerate(example_imgs)]

        all_cmd.append(cmd)
        all_source.append(source_img)
        all_target.append(target_img)

    print("Total: {} images".format(len(all_cmd)))

    if run:
        for i in tqdm(list(np.concatenate(all_cmd))):
            os.system(i)
    return all_cmd, all_source, all_target