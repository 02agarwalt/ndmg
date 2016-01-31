#!/usr/bin/env python

# Copyright 2014 Open Connectome Project (http://openconnecto.me)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# run_m2g.py
# Created by Greg Kiar and Will Gray Roncal on 2016-01-27.
# Email: gkiar@jhu.edu, wgr@jhu.edu

from argparse import ArgumentParser
from datetime import datetime
from subprocess import Popen, PIPE
import os.path as op
import ndmg.utils as mgu
import ndmg.register as mgr
import ndmg.track as mgt
import ndmg.graph as mgg
import numpy as np
import nibabel as nb


def pipeline(dti, bvals, bvecs, mprage, atlas, mask, labels, outdir):
    """
    Creates a brain graph from MRI data 
    """
    startTime = datetime.now()
   
    # Create derivative output directories
    dti_name = op.splitext(op.splitext(op.basename(dti))[0])[0]
    label_name = op.splitext(op.splitext(op.basename(labels))[0])[0]
    cmd = "mkdir -p " + outdir + "/reg_dti " + outdir + "/tensors " +\
          outdir + "/fibers " + outdir + "/graphs"
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    p.communicate()

    # Create derivative output file names
    aligned_dti = outdir + "/reg_dti/" + dti_name + "_aligned.nii.gz"
    tensors = outdir + "/tensors/" + dti_name + "_tensors.npz"
    fibers = outdir + "/fibers/" + dti_name + "_fibers.npz"
    graph = outdir + "/graphs/" + dti_name + "_" + label_name + ".graphml"
    print aligned_dti
    print tensors
    print fibers
    print graph

 
    # Creates gradient table from bvalues and bvectors
    print "Generating gradient table..."
    dti1 = outdir + "/tmp/" + dti_name + "_t1.nii.gz"
    gtab = mgu().load_bval_bvec(bvals, bvecs, dti, dti1)
    
    # Align DTI volumes to Atlas
    print "Aligning volumes..."
    mgr().dti2atlas(dti1, gtab, mprage, atlas, aligned_dti, outdir)

    print "Beginning tractography..."
    # Compute tensors and track fiber streamlines
    tens, tracks = mgt().eudx_basic(aligned_dti, mask, gtab,
                                       seed_num=1000000)

    print "Generating graph..."
    # Create graphs from streamlines
    labels_im = nb.load(labels)
    g = mgg(len(np.unique(labels_im.get_data()))-1, labels)
    g.make_graph(tracks)
    g.summary()

    print "Saving derivatives..."
    # Save derivatives to disk
    np.savez(tensors, tens)
    np.savez(fibers, tracks)
    g.save_graph(graph)

    print "Execution took: " + str(datetime.now() - startTime)
    print "Complete!"
    pass


def main():
    parser = ArgumentParser(description="This is an end-to-end connectome \
                            estimation pipeline from sMRI and DTI images")
    parser.add_argument("dti", action="store", help="Nifti DTI image stack")
    parser.add_argument("bval", action="store", help="DTI scanner b-values")
    parser.add_argument("bvec", action="store", help="DTI scanner b-vectors")
    parser.add_argument("mprage", action="store", help="Nifti T1 MRI image")
    parser.add_argument("atlas", action="store", help="Nifti T1 MRI atlas")
    parser.add_argument("mask", action="store", help="Nifti binary mask of \
                        brain space in the atlas")
    parser.add_argument("labels", action="store", help="Nifti labels of \
                        regions of interest in atlas space")
    parser.add_argument("outdir", action="store", help="Path to which \
                        derivatives will be stored")
    result = parser.parse_args()

    # Create output directory
    cmd = "mkdir -p " + result.outdir + " " + result.outdir + "/tmp"
    print "Creating output directory: " + result.outdir
    print "Creating output temp directory: " + result.outdir + "/tmp"
    p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
    p.communicate()

    pipeline(result.dti, result.bval, result.bvec, result.mprage, result.atlas,
            result.mask, result.labels, result.outdir)


if __name__ == "__main__":
    main()
