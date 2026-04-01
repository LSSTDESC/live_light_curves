'''main file for pipeline'''

from live_light_curves.Util.util import {

}
#import Lightcurver
#import Starred
#import PYCS
#import CCE/HME detection



### query given coordinates

# import sources from live_light_curves.source_list using some json interface
# for each observation:
    # check if any coordinates in sources lay within FOV
    # follow notebooks/tutorials/DP1/300_Science_Demos/307_AGN on RSP (gets cutout)
# initialize live_light_curves.Classes.cutout for each cutout




### run Lightcurver steps 4-6 to get PSF from nearby stars

# pass each newly generated cutout to Lightcurver stamp extraction and PSF modeling
# initialize live_light_curves.Classes.stellar_cutouts with the Lightcurver outputs



### have "Narrow PSF"

# initialize live_light_curves.Classes.narrow_psf so it works with this pipeline



### Lightcurver step 7 for stellar photometry (opt)
# initialize live_light_curves.Classes.stellar_photometry if we want to push stellar light curves


### Starred to get deconvolved sources (requires point source initial positions)
# deconvolve cutouts with computed PSF (this could just be done within the cutout object)
# Q: does this get all sources (e.g. plus stars, host galaxy), or just lensed point sources?


### Starred returns calibrated light curve data point
# load current object light curves and append the new data point



### When enough data is collected, run PYCS3 or SBI to get time delays
# if a source's light curve passes some critical threshold (e.g. in time), run PYCS



### While collecting, run RNN detection to test for imminent HMEs
# if a source's light curve passes a critical threshold, run caustic crossing detection software



### Send alerts when detected
# if an alert is triggered, send the alert



### Update HTML interface
# always send updated light curves to the web interface daily
# perhaps we could be inspired by some code here https://github.com/duxfrederic/lightcurver/blob/main/lightcurver/plotting/plot_curves_template.html













