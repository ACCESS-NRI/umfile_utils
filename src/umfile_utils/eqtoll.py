# Version of the UM eqtoll routine
import numpy as np

def eqtoll(phi_eq,lambda_eq,phi_pole,lambda_pole):

    small = 1e-6

    # Single value versions
    lambda_zero = lambda_pole+180.
    sin_phi_pole = np.sin(np.radians(phi_pole))
    cos_phi_pole = np.cos(np.radians(phi_pole))

    e_lambda = np.atleast_1d(lambda_eq)
    # Put into range -180 to 180
    e_lambda[e_lambda>180.] -= 360.0
    e_lambda[e_lambda<-180.] += 360.0
    
    e_lambda = np.radians(e_lambda)
    e_phi = np.radians(phi_eq)

    # Compute latitude using equation (4.7)
    arg = cos_phi_pole*np.cos(e_lambda)*np.cos(e_phi) + np.sin(e_phi)*sin_phi_pole
    arg = np.clip(arg, -1.0, 1.0)
    a_phi = np.arcsin(arg)
    phi_out = np.degrees(a_phi)

    # Compute longitude using equation (4.8)
    term1 = np.cos(e_phi)*np.cos(e_lambda)*sin_phi_pole - np.sin(e_phi)*cos_phi_pole
    term2 = np.cos(a_phi)
    # Clip should take care of term2==0 case
    arg = np.clip(term1/term2, -1.0, 1.0)
    a_lambda = np.degrees(np.arccos(arg))
    a_lambda = copysign(a_lambda,e_lambda)
    a_lambda = a_lambda+lambda_zero

    a_lambda[term2 < small] = 0.0

    a_lambda[a_lambda >= 360.0] -= 360.0
    a_lambda[a_lambda < 0.0] += 360.0

    return phi_out, a_lambda

def copysign(x,y):
    # Take zero as positive
    s = np.sign(y)
    s = np.where(np.equal(s,0),1,s)  # Set 
    return abs(x)*s
