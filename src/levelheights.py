# UM hybrid height scheme, assuming height_gen_smooth option.
# Code from setcona
# Ignore Earth_radius term to get height above MSL.

# In the UM, dimensions are r_theta_levels(0:model_levels), r_rho_levels(1:model_levels)
# To keep the relative arragement intact, add an extra value at the start of r_rho_levels
# here

import f90nml
import numpy as np

def setvertlevs(vfile, orog, verbose=False):

    vertlevs = f90nml.read(vfile)['vertlevs']
    if verbose:
        print("VERTLEVS", vertlevs)

    eta_theta_levels  = np.array(vertlevs['eta_theta']) # (0:model_levels)
    eta_rho_levels = np.array([-1e20] + vertlevs['eta_rho'])  # (1:model_levels)
    z_top_of_model = vertlevs['z_top_of_model']
    first_constant_r_rho_level = vertlevs['first_constant_r_rho_level']
    if verbose:
        print("eta_rho", eta_rho_levels)

    ashape = (len(eta_theta_levels),) + orog.shape
    if verbose:
        print("ASHAPE", ashape)

    r_theta_levels = np.zeros(ashape)
    r_rho_levels = np.zeros(ashape)
    r_rho_levels[0] = np.nan

    r_ref_theta = eta_theta_levels * z_top_of_model
    r_ref_rho = eta_rho_levels * z_top_of_model
    #  set bottom level, ie: orography
    r_theta_levels[0] = orog[:] # + Earth_radius

    #  For constant levels set r to be a constant on the level
    if len(orog.shape) == 2:
        r_theta_levels[first_constant_r_rho_level:] = r_ref_theta[first_constant_r_rho_level:,np.newaxis,np.newaxis]
        r_rho_levels[first_constant_r_rho_level:] = r_ref_rho[first_constant_r_rho_level:,np.newaxis,np.newaxis]
    else:
        r_theta_levels[first_constant_r_rho_level:] = r_ref_theta[first_constant_r_rho_level:,np.newaxis]
        r_rho_levels[first_constant_r_rho_level:] = r_ref_rho[first_constant_r_rho_level:,np.newaxis]


    #  Case( height_gen_smooth )
    # A smooth quadratic height generation
    for k in range(1, first_constant_r_rho_level):
        r_rho_levels[k] = eta_rho_levels[k] * z_top_of_model + \
          orog * (1.0 - eta_rho_levels[k]/eta_rho_levels[first_constant_r_rho_level])**2
        r_theta_levels[k] = eta_theta_levels[k] * z_top_of_model + \
          orog * (1.0 - eta_theta_levels[k]/eta_rho_levels[first_constant_r_rho_level])**2

    return r_theta_levels, r_rho_levels

if __name__ == '__main__':
    orog = np.arange(0,6000,1000.)
    r_theta_levels, r_rho_levels = setvertlevs('vertlevs_G3', orog, verbose=True)
    dr0 = r_theta_levels[1:,0] - r_theta_levels[:-1,0]
    drx = r_theta_levels[1:,-1] - r_theta_levels[:-1,-1]
