#!/usr/bin/env python

# ------------------------------------------------------------------------------------------------------
# Author of package: Sarah White (sarahwhite.astro@gmail.com) and Sphe Makhathini (sphemakh@gmail.com)
# Based on a mosaicking script by Paolo Serra (paolo80serra@gmail.com)
# ------------------------------------------------------------------------------------------------------

from MosaicSteward import make_mosaic
from argparse import ArgumentParser
import MosaicSteward
import os
import sys

log = MosaicSteward.log

# So that error handling is compatible with Python 2 as well as Python 3
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

def main(argv):

    parser = ArgumentParser(description="Run make_mosaic over the targets")

    parser.add_argument("-i", "--input",
                        help="The directory that contains the (2D or 3D) images and beams.")
    parser.add_argument("-m", "--mosaic-type",
                        help="State 'continuum' or 'spectral' as the type of mosaic to be made.")
    parser.add_argument("-d", "--domontage", action="store_true",
                        help="Use montage for regridding the images and beams.")
    parser.add_argument("-u", "--uniform-resolution", action="store_true",
                        help="Convolve all images and beams to a uniform resolution before mosaicking.")
    parser.add_argument("-h", "--hpbw-mode", default="auto",
                        help="State 'auto' or 'override' for determining the uniform resolution (HPBW) to be used (if enabled)."
                             "The default is 'auto', meaning that the maximum HPBW across the input images will be found and used.")
    parser.add_argument("-s", "--set-hpbw", type=float,
                         help="Set the HPBW (in arcsec) to use for uniform resolution, if wishing to override the 'auto' setting.")
    parser.add_argument("-c", "--cutoff", type=float, default=0.1,
                         help="The cutoff in the primary beam to use (assuming a Gaussian at the moment)."
                              "E.g. The default of 0.1 means going down to the 10 percent level for each pointing.")
    parser.add_argument("-n", "--name", default="mymosaic",
                        help="The prefix to be used for output files.")
    parser.add_argument("-t", "--target-images", action="append",
                         help="The filenames of each target/pointing image to be mosaicked. A suffix of 'image.fits' is expected, and this is replaced by 'pb.fits' in order to locate the corresponding beams (which are also required as input).")
    parser.add_argument("-o", "--output",
                         help="The directory for all output files.")

    args = parser.parse_args(argv)
    input_dir = args.input
    mosaic_type = args.mosaic_type
    hpbw_mode = args.hpbw_mode
    specified_hpbw = args.set_hpbw
    cutoff = args.cutoff
    outname = args.name
    output_dir = args.output

    if args.target_images: 
        log.info('Target images = {}'.format(" ".join(args.target_images)))
        images = args.target_images
    else:
        log.error(
            "Must specify the (2D or 3D) images to be mosaicked, each prefixed by '-t '.")
        raise LookupError("Must specify the (2D or 3D) images to be mosaicked, each prefixed by '-t '.")

    # Throw an error if the user provides only one image
    if len(images) < 2:
        log.error('At least two images must be specified for mosaicking')
        raise ValueError('At least two images must be specified for mosaicking')

    beams = [tt.replace('image.fits', 'pb.fits') for tt in images]
    imagesR = [tt.replace('image.fits', 'imageR.fits') for tt in images]
    beamsR = [tt.replace('image.fits', 'pbR.fits') for tt in images]

    for tt in images:
        try:
            open(input_dir+'/'+tt)
        except FileNotFoundError:
            log.error('File {0:s} does not exist'.format(input_dir+'/'+tt))
            raise FileNotFoundError('File {0:s} does not exist'.format(input_dir+'/'+tt))

    for bb in beams:
        try:
            open(input_dir+'/'+bb)
        except FileNotFoundError:
            log.error('File {0:s} does not exist'.format(input_dir+'/'+bb)) 
            raise FileNotFoundError('File {0:s} does not exist'.format(input_dir+'/'+bb))

    log.info('All images and beams found on disc')

    # Stage where uniform-resolution is 'applied' (if enabled)
    if args.uniform_resolution:
    
        if hpbw_mode = 'auto':

            #hpbw_to_use = make_mosaic.find_largest_BMAJ()

        else:

            hpbw_to_use = specified_hpbw

        #make_mosaic.generate_corrective_gaussian_and_convolve()
    
        # Need to ensure that the *convolved* images and primary beams are going to be passed to make_mosaic 

    else:
        log.info(
                "Will use the 'native' synthesised beams of the input images, with no convolution to a single resolution before mosaicking. If uniform resolution across the input images is desired, before mosaicking, please enable 'uniform-resolution' and re-run this worker (with consideration of the related settings).")
    
        
    # Ready for re-gridding
    if args.domontage:
        make_mosaic.use_montage_for_regridding(
            input_dir, output_dir, mosaic_type, images, beams, imagesR, beamsR, outname)
    else:
        log.info(
                "Will use mosaic header {0:s}.hdr and regridded images and beams available on disc. WARNING: We assume that the user is happy with the resolution used for these existing, regridded images. If not, please re-run this worker after enabling 'uniform-resolution' and 'domontage' (in order to redo the regridding).".format(outname))

    make_mosaic.check_for_regridded_files(output_dir, imagesR, beamsR)


    # Now to mosaic
    make_mosaic.make_mosaic_using_beam_info(input_dir, output_dir, mosaic_type, outname, imagesR, beamsR, cutoff, images)

    # Move the log file to the output directory
    os.system('mv log-make_mosaic.txt '+output_dir+'/')

    return 0