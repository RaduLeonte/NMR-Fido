'''Processing'''

import numpy as np

'''
Window functions
'''

def sine_bell(data: np.ndarray, power: float=2.0, start: float=0.5, end: float=1) -> np.ndarray:
    '''
    Applies sine-bell window function (nmrPipe) to given data.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers
    power: float
        power to raise sine function by
    start: float
        starting offset? [0, 1]
    end: float
        ending offset? (-start, 1]

    Returns
    -------
    ndarray
        apodized data
        
    Raises
    ------
    ValueError
        when start and end offsets are outside their allowed ranges
    '''
    
    print("Stub function called: sine_bell")
    return None


def lorentz_to_gaussian(data: np.ndarray) -> np.ndarray:
    '''
    Applies lorentz-to-gaussian window function (nmrPipe) to given data.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers

    Returns
    -------
    ndarray
        apodized data
    '''
    
    print("Stub function called: lorentz_to_gaussian")
    return None


def exponential_multiply(data: np.ndarray) -> np.ndarray:
    '''
    Applies exponential multiply window function to given data.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers

    Returns
    -------
    ndarray
        apodized data
    '''
    
    print("Stub function called: exponential_multiply")
    return None


def squared_sine(data: np.ndarray) -> np.ndarray:
    '''
    Applies squared sine window function to given data.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers

    Returns
    -------
    ndarray
        apodized data
    '''
    
    print("Stub function called: squared_sine")
    return None


'''
Processing
'''

def fourier_transform(data: np.ndarray) -> np.ndarray:
    '''
    Complex fourier transform.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers

    Returns
    -------
    ndarray
        fourier transformed data
    '''
    
    print("Stub function called: fourier_transform")
    return None


def zero_fill(data: np.ndarray, multiplier: int=2, final_size: int=None, pad: int=None) -> np.ndarray:
    '''
    Fills data with zeroes.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers
    multiplier: int
        input data will be filled so the final size will me len(data)*multiplier
    final_size: int
        input data will be filled until the data's length equals this argument
    pad: int
        [pad] many zeroes will be added to the end of the data

    Returns
    -------
    ndarray
        zero-filled data
        
    Raises
    ------
    ValueError
        when multiple filling modes are specified
    '''
    
    print("Stub function called: zero_fill")
    return None


def phase_correction(data: np.ndarray, p0: float=0.0, p1: float=0.0) -> np.ndarray:
    '''
    Adjusts phase of data.
    d'(f) = d(f) * exp( -i*(p0 + p1*f) )
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers
    p0: float
        Zero-th order phase correction term
    p1: float
        First order phase correction term

    Returns
    -------
    ndarray
        phase-corrected data
    '''
    
    print("Stub function called: phase_correction")
    return None


def baseline_correction(data: np.ndarray) -> np.ndarray:
    '''
    Polynomial baseline correction (nmrPipe).
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers
    
    Returns
    -------
    ndarray
        baseline corrected data
    '''
    
    print("Stub function called: baseline_correction")
    return None


'''
Miscellaneous
'''

def transpose(data: np.ndarray) -> np.ndarray:
    '''
    Transposes data.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers

    Returns
    -------
    ndarray
        transposed data
    '''
    
    print("Stub function called: transpose")
    return None


def crop_data(data: np.ndarray) -> np.ndarray:
    '''
    Crops data.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers

    Returns
    -------
    ndarray
        cropped data
    '''
    
    print("Stub function called: crop_data")
    return None


def solvent_filter(data: np.ndarray) -> np.ndarray:
    '''
    Applies solvent filter.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers

    Returns
    -------
    ndarray
        data with solvent filter applied
    '''
    
    print("Stub function called: solvent_filter")
    return None


def linear_prediction(data: np.ndarray) -> np.ndarray:
    '''
    Linear prediction.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of complex numbers

    Returns
    -------
    ndarray
        data with linearly predicted points added
    '''
    
    print("Stub function called: linear_prediction")
    return None


def hilbert_transform(data: np.ndarray) -> np.ndarray:
    '''
    Reconstruct imaginary data using hilbert transform.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of real numbers

    Returns
    -------
    ndarray
        array of complex numbers
    '''
    
    print("Stub function called: hilbert_transform")
    return None


def add_constant(data: np.ndarray, constant: complex) -> np.ndarray:
    '''
    Add a constant to every point.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of real numbers
    constant: complex
        complex number to add

    Returns
    -------
    ndarray
        data with constant added
    '''
    
    print("Stub function called: add_constant")
    return None


def multiply_constant(data: np.ndarray, constant: complex) -> np.ndarray:
    '''
    Multiply every point by a constant.
    
    Parameters
    ----------
    data: np.ndarray
        n-dimensional array of real numbers
    constant: complex
        complex number to multiply data by

    Returns
    -------
    ndarray
        data with constant added
    '''
    
    print("Stub function called: multiply_constant")
    return None