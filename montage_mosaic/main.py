#!/usr/bin/env python

# ---------------------------------------------------------------------------------------------
# Author of package: Sarah White (sarahwhite.astro@gmail.com)
# Based on a mosaicking script by Paolo Serra (paolo80serra@gmail.com)
# --------------------------------------------------------------------------------------------- 

from montage_mosaic import make_mosaic
from argparse import ArgumentParser
import montage_mosaic
import os
import sys

log = montage_mosaic.log


def main(argv):

    parser = ArgumentParser(description="Run make_mosaic over the targets")

    parser.add_argument("-m", "--mosaic_type",
                        help="State 'continuum' or 'spectral' as the type of mosaic to be made.")
    parser.add_argument("-d", "--domontage", action="store_true",
                        help="Use montage for regridding the cubes and beams.")
    parser.add_argument("-c", "--cutoff", default=0.1, type=float,
                         help="The cutoff in the primary beam to use (assuming a Gaussian at the moment). E.g. The default of 0.1 means going down to the 10% level for each pointing.")
    parser.add_argument("-o", "--outname", default="mymosaic",
                        help="The prefix to be used for output files.")
    parser.add_argument("-t", "--target_images", action="append",
                        help="The names of each target/pointing image to be mosaicked. A suffix of 'image.fits' is expected.")

    args = parser.parse_args(argv)
    cutoff = args.cutoff
    outname = args.outname

    if args.target_images: 
        log.info('Target images = {}'.format(" ".join(args.target_images)))
        images = args.target_images
    else:
        log.error(
            "Must specify the cubes/images to be mosaicked, each prefixed by '-t '.")

    #print('Up to here 1')  # To aid de-bugging

    beams = [tt.replace('image.fits', 'pb.fits') for tt in images]
    imagesR = [tt.replace('image.fits', 'imageR.fits') for tt in images]
    beamsR = [tt.replace('image.fits', 'pbR.fits') for tt in images]

    for tt in images:
        if not os.path.exists(tt):
            # Should exit automatically
            log.error('File {0:s} does not exist'.format(tt))

    for bb in beams:
        if not os.path.exists(bb):
            # Should exit automatically
            log.error('File {0:s} does not exist'.format(bb))

    log.info('All images and beams found on disc')
    #print('Up to here 2')  # To aid de-bugging

    if args.domontage:
        make_mosaic.use_montage_for_regridding(
            images, beams, imagesR, beamsR, outname)
    else:
        log.info(
            'Will use mosaic header {0:s}.hdr and regridded images and beams available on disc'.format(outname))
    #print('Up to here 3')  # To aid de-bugging

    make_mosaic.check_for_regridded_files(imagesR, beamsR)
    #print('Up to here 4')  # To aid de-bugging

    make_mosaic.make_mosaic_using_beam_info(outname, imagesR, beamsR, cutoff)
    #print('Up to here 5')  # To aid de-bugging

    return 0