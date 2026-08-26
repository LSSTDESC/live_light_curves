'''This file contains utilities which connect our objects to the Starred program'''


def initialize_starred_variables(extracted_frames_dict):
    """This starts the Starred process by defining various global variables
    param extracted_frames_dict: dictionary which must contain the following key/value pairs:
        data_roi: np.array shape (N, res, res) for N epochs of res x res data within region of interest
        narrow_psfs: np.array shape (N, upsampled_res, upsampled_res) for N epochs of upsampled_res x upsampled_res arrays representing the narrow psf
    return: dictionary containing parameters for starred fitting processes
    """
    import numpy as np

    data_roi = extracted_frames_dict['data_roi']
    narrow_psfs = extracted_frames_dict['narrow_psfs']

    im_size = data_roi.shape[1]
    im_size_upsampled = narrow_psfs.shape[1]
    epochs = data_roi.shape[0]

    # get the subsampling factor
    subsampling_factor = int(im_size_upsampled / im_size)

    # from Starred tutorial notebook
    sigma_sky_2 = np.asarray(
        [
            np.std(data_roi[ii, int(0.9 * im_size):, int(0.9 * im_size):]) for ii in range(epochs)
        ]
    ) ** 2

    sigma_2 = np.asarray(
        [
            sigma_sky_2[ii] + data_roi[ii].clip(min=0) for ii in range(epochs)
        ]
    )

    # relative scales, max is 1, normalization is 100% of the frame 0 data
    scale = np.nanmax(data_roi)
    normalization = np.nanmax(data_roi[0]) / 100
    data_roi /= normalization
    sigma_2 /= normalization

    offset = (im_size-1)/2

    starred_parameters = {
        'im_size': im_size,
        'im_size_up': im_size_upsampled,
        'epochs': epochs,
        'subsampling_factor': subsampling_factor,
        'scale': scale,
        'normalization': normalization,
        'data_roi': data_roi,
        'sigma_2': sigma_2,
        'offset': offset
    }

    return starred_parameters


def identify_point_sources(extracted_frames_dict, n_sources, fwhm=2):
    """this function searches for point sources in the data provided
    param extracted_frames_dict: dictionary of arrays produced from the output of 
        StandardUtil.extract_frames_from_h5_file
    param n_sources: number of expected point sources
    param fwhm: full width of half max of the PSF in pixels
    return: dict containing initialization parameters and given source names
    """
    import numpy as np
    from starred.deconvolution.deconvolution import setup_model
    from starred.deconvolution.parameters import ParametersDeconv
    from starred.deconvolution.loss import Loss
    from starred.optim.optimization import Optimizer
    from copy import deepcopy

    generic_labels = list('abcdefghijklmnopqrstuvwxyz')
    if n_sources > len(generic_labels):
        raise NotImplementedError("too many sources provided, please update this function")

    seeings = deepcopy(extracted_frames_dict['seeings'])
    data_roi = deepcopy(extracted_frames_dict['data_roi'])
    data_noisemap = deepcopy(extracted_frames_dict['data_noisemap'])
    narrow_psfs = deepcopy(extracted_frames_dict['narrow_psfs'])

    #extract the top 10 percentile of frames based on seeing
    best_percentile = np.percentile(seeings, 0)
    lower_threshold_percentile = np.percentile(seeings, 10)
    selected_indices = np.where(
        (seeings >= best_percentile)*(seeings<lower_threshold_percentile)
    )
    best_data = data_roi[selected_indices]
    best_noise = data_noisemap[selected_indices]
    best_narrow_psfs = narrow_psfs[selected_indices]
    offset = best_data.shape[1]
    upsampling_factor = int(best_narrow_psfs.shape[1]/best_data.shape[1])

    # start identifying point sources based on brightest pixels
    # mask out chosen pixels as they are added
    mask = np.ones_like(best_data[0])
    c_x = []
    c_y = []
    source_names = []

    for source in range(n_sources):
        x, y = np.unravel_index(np.argmax(best_data[0] * mask), best_data[0].shape)
        #amp = best_data[0, x, y]
        # do not select this regions for the next sources by masking it out
        mask[x-fwhm:x+1+fwhm, y-fwhm:y+1+fwhm] = np.zeros((2*fwhm+1, 2*fwhm+1))
        c_x.append(x-offset)
        c_y.append(y-offset)
        source_names.append(generic_labels[source])

    initial_model, k_init, k_up, k_down, k_fixed = setup_model(
        data=best_data,
        sigma_2=best_noise**2,
        s=best_narrow_psfs,
        xs=c_x,
        ys=c_y,
        subsampling_factor=upsampling_factor
    )

    # fix background to optimize point sources
    k_fixed['kwargs_background']['h'] = k_init['kwargs_background']['h']

    params = ParametersDeconv(k_init, k_fixed, k_up, k_down)
    loss = Loss(best_data, initial_model, params, best_noise)
    optim = Optimizer(loss, params, method='l-bfgs-b')

    # 200 iterations should be enough to get the point source locations
    optim.minimize(maxiter=200)

    k_optim_init_positions = params.best_fit_values(as_kwargs=True)
    k_optim_init_positions['source_names'] = source_names

    # We need to take the optimized parameters and the source names
    return k_optim_init_positions


def optimize_starred_fit(extracted_frames_dict, k_optim_init_positions):
    """This runs the optimization process for Starred
    param extracted_frames_dict: dictionary of arrays produced from the output of 
        StandardUtil.extract_frames_from_h5_file
    param k_optim_init_positions: dict of starred parameters optimized purely on 
        translations on the best seeing images 
    param starred_params: starred.deconvolution.parameters.ParametersDeconv object for initialization
    return: starred model and dict of starred kwargs of the optimized fit
    """

    import numpy as np
    from starred.deconvolution.deconvolution import setup_model
    from starred.deconvolution.parameters import ParametersDeconv
    from starred.deconvolution.loss import Loss
    from starred.optim.optimization import Optimizer
    from starred.utils.noise_utils import propagate_noise
    from lightcurver.utilities.starred_utilities import get_flux_uncertainties
    from copy import deepcopy

    # unpack some objects for model setup
    data_roi = deepcopy(extracted_frames_dict['data_roi'])
    data_noisemap = deepcopy(extracted_frames_dict['data_noisemap'])
    narrow_psfs = deepcopy(extracted_frames_dict['narrow_psfs'])

    upsampling_factor = int(narrow_psfs.shape[1]/data_roi.shape[1])

    c_x = deepcopy(k_optim_init_positions['kwargs_analytic']['c_x'])
    c_y = deepcopy(k_optim_init_positions['kwargs_analytic']['c_y'])
    source_names = deepcopy(k_optim_init_positions['source_names'])

    model, k_init, k_up, k_down, k_fixed = setup_model(
        data=data_roi,
        sigma_2=data_noisemap**2,
        s=narrow_psfs,
        xs=c_x,
        ys=c_y,
        subsampling_factor=upsampling_factor
    )

    W = propagate_noise(
        model, 
        data_noisemap**2,
        k_init,
        wavelet_type_list=['starlet'],
        method='SLIT',
        likelihood_type='chi2',
        verbose=False,
        upsampling_factor=upsampling_factor
    )[0]

    parameters = ParametersDeconv(
        kwargs_init=k_init,
        kwargs_fixed=k_fixed,
        kwargs_up=k_up,
        kwargs_down=k_down
    )

    # remove all keys from fixed parameters
    k_fixed = dict()

    # these were decent default parameters from Martin's notebook
    # for general optimization
    loss = Loss(
        data_roi, 
        model, 
        parameters, 
        data_noisemap**2, 
        regularization_terms='l1_starlet',
        regularization_strength_scales=10.,
        regularization_strength_hf=10.,
        regularization_strength_positivity_ps=10.
    )

    optim = Optimizer(loss, parameters, method='adabelief')
    optimiser_optax_option = {
        'max_iterations': 1000,
        'init_learning_rate': 1e-3,
        'schedule_learning_rate': True
    }

    optim.minimize(**optimiser_optax_option)

    k_optim_prior_to_fine_tuning = deepcopy(parameters.best_fit_values(as_kwargs=True))

    # final round of optimization for fine tuning
    kwargs_fixed = {
        'kwargs_analytic': {
            'alpha': k_optim_init_positions['kwargs_analytic']['alpha']
        },
        'kwargs_background': dict(),
        'kwargs_sersic': dict()
    }

    parameters = ParametersDeconv(
        kwargs_init=k_optim_prior_to_fine_tuning,
        kwargs_fixed=kwargs_fixed,
        kwargs_up=k_up,
        kwargs_down=k_down
    )

    # setup for fine-tuning
    loss = Loss(
        data_roi, 
        model,
        parameters,
        data_noisemap**2,
        regularization_terms='l1_starlet',
        regularization_strength_scales=1, 
        regularization_strength_hf=1, 
        regularization_strength_positivity=100.,
        regularization_strength_positivity_ps=100.,
        regularization_strength_pts_source=0.025,
        W=W
    )

    optim = Optimizer(
        loss, 
        parameters,
        method='adabelief'
    )

    optimiser_optax_option = {
        'max_iterations':1000,
        'min_iterations':None,
        'init_learning_rate':5e-4,
        'schedule_learning_rate':0,
        'restart_from_init':True,
        'stop_at_loss_increase':False,
        'progress_bar':True,
        'return_param_history':True
    }

    # diagnostics = (best_fit, logL_best_fit, extra_fields, runtime)
    diagnostics = optim.minimize(**optimiser_optax_option)

    kwargs_final = deepcopy(parameters.best_fit_values(as_kwargs=True))

    all_starred_kwargs = {
        'kwargs_final': kwargs_final,
        'kwargs_up': k_up,
        'kwargs_down': k_down,
        'source_names': source_names
    }

    return model, all_starred_kwargs, diagnostics


def process_fluxes(
    model, 
    extracted_frames_dict, 
    all_starred_kwargs
):
    '''This function processes the model and extracted frames to get 
    the flux of each point source object
    param model: Starred model of the system
    param extracted_frames_dict: dictionary of arrays produced from the output of 
        StandardUtil.extract_frames_from_h5_file
    param all_starred_kwargs: dict containing kwarg dicts of the parameters 
        for the final fit of Starred
    return: dictionary containing all source fluxes
    '''

    from lightcurver.utilities.starred_utilities import get_flux_uncertainties
    from lightcurver.utilities.lightcurves_postprocessing import convert_flux_to_magnitude
    
    import numpy as np
    import pandas as pd

    data_roi = extracted_frames_dict['data_roi']
    data_noisemap = extracted_frames_dict['data_noisemap']
    narrow_psfs = extracted_frames_dict['narrow_psfs']
    source_names = all_starred_kwargs['source_names']

    flux_uncertainties = get_flux_uncertainties(
        kwargs=all_starred_kwargs['kwargs_final'],
        kwargs_up=all_starred_kwargs['kwargs_up'],
        kwargs_down=all_starred_kwargs['kwargs_down'],
        data=data_roi,
        noisemap=data_noisemap,
        model=model
    )

    flux_values = all_starred_kwargs['kwargs_final']['kwargs_analytic']['a']
    scale = np.nanmax(data_roi)

    fluxes = dict()
    
    # some relative error in flux measurements
    rel_norm_errs = 0.005

    for jj, source_label in enumerate(source_names):
        curve = flux_values[jj::len(source_names)]
        d_curve_hessian = flux_uncertainties[jj::len(source_names)]*scale
        norm_abs_errs = np.array(curve)*rel_norm_errs
        d_curve = (norm_abs_errs**2 + d_curve_hessian**2)**0.5
        fluxes[f'{source_label}_flux'] = np.array(curve)
        fluxes[f'{source_label}_d_flux'] = d_curve

    fluxes['mjd'] = extracted_frames_dict['times_mjd']
    fluxes['zeropoint'] = np.ones_like(d_curve) * extracted_frames_dict['zeropoints']

    fluxes = pd.DataFrame(fluxes)

    magnitude_dataframe = convert_flux_to_magnitude(fluxes)

    return magnitude_dataframe


def convert_mags_dataframe_to_light_curve(
        magnitude_dataframe,
        all_starred_kwargs, 
        band
    ):
    '''This takes in the magnitudes that were processed by Starred and 
    lightcurver, and converts them into a portable light curve object
    param magnitude_dataframe: output of process_fluxes(), a pandas DataFrame 
        object which contains all times, magnitudes, and magnitude_errors
    param all_starred_kwargs: kwargs from the starred fit in optimize_starred_fit(), 
        a dictionary which contains model parameters and source nmaes
    return: dict containing the data in the expected format for the LightCurve object
    '''

    # prepare light curve data to append to light curve
    light_curve_data = dict()
    for ps in all_starred_kwargs['source_names']:
        light_curve_data[f'image_{ps}'] = {
            f'{band}_time': magnitude_dataframe['mjd'].tolist(),
            f'{band}_mag': magnitude_dataframe[f'{ps}_mag'].tolist(),
            f'{band}_mag_err': magnitude_dataframe[f'{ps}_d_mag'].tolist()
        }

    return light_curve_data




















