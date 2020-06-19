#!/usr/bin/env python

# ------------------------------------------------------------------------------------------------------
# Author of package: Sarah White (sarahwhite.astro@gmail.com) and Sphe Makhathini (sphemakh@gmail.com)
# Based on a mosaicking script by Paolo Serra (paolo80serra@gmail.com) 
# and a convolving script by Landman Bester (landman.bester@gmail.com)
# ------------------------------------------------------------------------------------------------------

from MosaicSteward import make_mosaic, image_convolver
from argparse import ArgumentParser
import MosaicSteward
import os
import sys
import multiprocessing

log = MosaicSteward.log

# So that error handling is compatible with Python 2 as well as Python 3
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

def main(argv):

    parser = ArgumentParser(description="Run make_mosaic over the targets")

    parser.add_argument("-i", "--input",
                        help="The directory that contains the (2D or 3D) images "
                             "and beams.")
    parser.add_argument("-m", "--mosaic-type",
                        help="State 'continuum' or 'spectral' as the type of "
                             "mosaic to be made.")
    parser.add_argument("-d", "--domontage", action="store_true",
                        help="Use montage for regridding the images and beams.")
    parser.add_argument("-ci", "--convolve-images", action="store_true",
                        help="Convolve all images and beams before mosaicking.")
    parser.add_argument("-pm", "--psf-mode", default="auto",
                        help="If 'convolve-images' is enabled, then 'psf-mode' "
                             "dictates how the psf, used for convolution, is "
                             "determined/applied. \n"
                             "Options are 'auto' (for each freq channel, apply "
                             "the largest psf found across the input images), "
                             "'uniform' (find the largest psf across the input "
                             "images and apply this same psf to all freq channels), "
                             "and 'scaled' (similar to 'auto' but where a 1/freq "
                             "function is fitted to the bmaj values, in order to "
                             "identify and exclude outliers). \n"
                             "The default setting is 'auto'.")
    parser.add_argument("-pp", "--psf-pars", default=None, nargs='+', type=float,
                        help="If 'psf-mode' is set to 'uniform', then the default psf "
                             "(based on the largest psf across the input images) "
                             "can be overridden by setting psf parameters here. \n"
                             "These should be specified as: bmaj bmin bpa (in units "
                             "of arcsec, arcsec, deg). These values will be used for "
                             "enforcing uniform resolution across all images.")
    parser.add_argument("-cp", "--circ-psf", action="store_true",
                        help="Pass this flag in order to convolve with a circularised "
                             "psf instead of an elliptical one.")
    parser.add_argument("-ncpu", '--ncpu', default=0, type=int,
                        help="Number of threads to use for convolution. \n"
                             "Default of zero means use all threads.")
    parser.add_argument("-c", "--cutoff", type=float, default=0.1,
                        help="The cutoff in the primary beam to use (assuming a "
                             "Gaussian at the moment). \n"
                             "E.g. The default of 0.1 means going down to the "
                             "10 percent level for each pointing.")
    parser.add_argument("-n", "--name", default="mymosaic",
                        help="The prefix to be used for output files.")
    parser.add_argument("-t", "--target-images", action="append",
                        help="The filenames of each target/pointing image to be "
                             "mosaicked. A suffix of 'image.fits' is expected, and "
                             "this is replaced by 'pb.fits' in order to locate the "
                             "corresponding beams (which are also required as input).")
    parser.add_argument("-o", "--output",
                        help="The directory for all output files.")

    args = parser.parse_args(argv)
    input_dir = args.input
    mosaic_type = args.mosaic_type
    psf_mode = args.psf_mode
    cutoff = args.cutoff
    outname = args.name
    output_dir = args.output

    log.info("COMMAND LINE INPUT: MosaicSteward {0:s}".format(" ".join(argv)))

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


    ## Stage where images are convolved (if convolve-images is enabled)
    
    # Multiprocessing to speed up convolution
    if not args.ncpu:
        args.ncpu = multiprocessing.cpu_count()
    log.info("Using {0:d} threads".format(args.ncpu))

    if args.convolve_images:

        log.info("Images are to be convolved before mosaicking them together.")
     
        if psf_mode == 'auto':

            log.info("The 'psf-mode' parameter has been set to 'auto'.")
            ### COME BACK TO THIS LATER ONCE 'UNIFORM' IS WORKING

            if args.psf_pars is not None:
                log.info("WARNING: The values set via 'psf-pars' are being ignored. They are only used "
                         "if 'psf-mode' has been set to 'uniform'.")

        elif psf_mode == 'uniform':    

            log.info("The 'psf-mode' parameter has been set to 'uniform'.")

            if args.psf_pars is None:
                
                log.info("WARNING: If wishing to override the default psf determined for the 'uniform' setting, "
                         "the user must specify the psf parameters to be used for convolution via 'psf-pars'.")
                log.info("Proceeding with the largest psf found amongst (all channels of) all input images.")
                psf_to_use = make_mosaic.find_largest_BMAJ(input_dir, images, mosaic_type, 'images')
                psf_to_use_arcsec = psf_to_use*3600.0   # Since BMAJ is (or should be) in units of deg

                ### To simplify things for the moment, have the 'uniform' setting being to convolve with cicularised beam
                beampars = tuple([psf_to_use, psf_to_use, 0.0])  ### CHECK I'VE SET THIS UP RIGHT

            else:

                log.info("Proceeding with the psf parameters specified via 'psf-pars'.")
                beampars = tuple(args.psf_pars)

            print("Checking beampars")
            print(beampars)
            print(beampars[0])

            psf_to_use_arcsec = beampars[0]  # User is asked to pass this value in units of arcsec  ### CHECK THAT I GET A SINGLE VALUE
            psf_to_use = psf_to_use_arcsec/3600.0  # Need to pass this to convolve_image in units of deg

            log.info(
                    "The input images will be convolved so that they have a uniform resolution of "
                    "{0:f} arcsec (for each freq channel, if the images are cubes)".format(psf_to_use_arcsec))

        elif psf_mode == 'scaled':

            log.info("The 'psf-mode' parameter has been set to 'scaled'.")
            ### CODE UP THIS OPTION LAST
        
            if args.psf_pars is not None:
                log.info("WARNING: The values set via 'psf-pars' are being ignored. They are only used "
                         "if 'psf-mode' has been set to 'uniform'.")

        else:

            log.error("{0:s} is not a valid option for psf-mode".format(psf_mode))
            raise ValueError("{0:s} is not a valid option for psf-mode".format(psf_mode))

        if args.circ_psf:  # For each of the psf-modes it should be possible to force the psf to be circular
            log.info("WARNING: Enabling circularised beam. User must set circ-psf to 'False' if they want the "
                     "automatically-determined 'bmin' and 'bpa' values (or those set through psf-pars) to be used.")
            beampars[1] = beampars[0]  # If BPA is varying a lot over the input images, then best to set bmin to bmaj
            beampars[2] = 0.0  # pa of psf set to zero



        log.info("Psf paramters to be used: emaj = {0:.3f}, emin = {0:.3f}, PA = {0:.3f}".format(beampars[0], beampars[1], beampars[2])) ### CHECK FORMATTING

        for image in images:
            image_convolver.convolve_image(input_dir, image, beampars, args.ncpu)
    
        ### Need to ensure that the primary beams and *convolved* images are going to be passed to make_mosaic 

    else:

        log.info(
                "Will use the 'native' synthesised beams (i.e. psfs) of the input images, with no convolution "
                "to a common resolution before mosaicking. If convolution of the input images (before "
                "mosaicking) is desired, please enable 'convolve-images' and re-run (with consideration "
                "of the related settings, e.g. 'psf-mode').")
    
        
    ## Ready for re-gridding
    if args.domontage:
        make_mosaic.use_montage_for_regridding(
            input_dir, output_dir, mosaic_type, images, beams, imagesR, beamsR, outname)
    else:
        log.info(
                "Will use mosaic header {0:s}.hdr and regridded images and beams available on disc. "
                "WARNING: We assume that the user is happy with the resolution used for these existing, "
                "regridded images. If not, please re-run this worker after enabling 'uniform-resolution' "
                "and 'domontage' (in order to redo the regridding).".format(outname))

    make_mosaic.check_for_regridded_files(output_dir, imagesR, beamsR)


    ## Now to mosaic
    make_mosaic.make_mosaic_using_beam_info(input_dir, output_dir, mosaic_type, outname, imagesR, beamsR, cutoff, images)

    ## Move the log file to the output directory
    os.system('mv log-make_mosaic.txt '+output_dir+'/')

    return 0
