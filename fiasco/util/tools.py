"""
Numerical tools
"""
import numpy as np
from scipy.interpolate import splrep, splev
import astropy.units as u

__all__ = ['vectorize_where', 'vectorize_where_sum', 'burgess_tully_descale',
           'burgess_tully_descale_vectorize']


def vectorize_where(x_1, x_2):
    """
    Find indices of one array in another

    Parameters
    ----------
    x_1 : array-like
        Array to search through
    x_2 : array-like
        Values to search for
    """
    return np.vectorize(lambda a, b: np.where(a == b)[0], excluded=[0])(x_1, x_2)


def vectorize_where_sum(x_1, x_2, y, axis=None):
    """
    Find all occurences of one array in another and sum over a third

    Parameters
    ----------
    x_1 : array-like
        Array to search through
    x_2 : array-like
        Values to search for
    y : array-like
    axis : `int`, optional
        Axis to sum over
    """
    unit = None
    if isinstance(y, u.Quantity):
        unit = y.unit
        y = y.value
    if len(y.shape) == 2:
        signature = '()->(n)'
    elif len(y.shape) == 1:
        signature = '()->()'
    else:
        raise ValueError('y cannot have dimension greater than 2')
    collect = np.vectorize(lambda a, b, c: c[np.where(a == b)].sum(axis=axis),
                           excluded=[0, 2], signature=signature)
    return u.Quantity(collect(x_1, x_2, y), unit)


def burgess_tully_descale(x, y, energy_ratio, c, scaling_type):
    """
    Convert scaled Burgess-Tully parameters to physical quantities. For more details see
    [1]_.

    Parameters
    ----------
    x : `~astropy.units.Quantity`
    y : `~astropy.units.Quantity`
    energy_ratio : `~astropy.units.Quantity`
        Ratio of temperature to photon energy
    c : `~astropy.units.Quantity`
        Scaling constant
    scaling_type : `int`

    Returns
    -------
    upsilon : `~numpy.NDArray`
        Descaled collision strength or cross-section

    References
    ----------
    .. [1] Burgess, A. and Tully, J. A., 1992, A&A, `254, 436 <http://adsabs.harvard.edu/abs/1992A%26A...254..436B>`_
    """
    nots = splrep(x, y, s=0)
    if scaling_type == 1:
        x_new = 1.0 - np.log(c) / np.log(energy_ratio + c)
        upsilon = splev(x_new, nots, der=0) * np.log(energy_ratio + np.e)
    elif scaling_type == 2:
        x_new = energy_ratio / (energy_ratio + c)
        upsilon = splev(x_new, nots, der=0)
    elif scaling_type == 3:
        x_new = energy_ratio / (energy_ratio + c)
        upsilon = splev(x_new, nots, der=0) / (energy_ratio + 1.0)
    elif scaling_type == 4:
        x_new = 1.0 - np.log(c) / np.log(energy_ratio + c)
        upsilon = splev(x_new, nots, der=0) * np.log(energy_ratio + c)
    elif scaling_type == 5:
        # dielectronic
        x_new = energy_ratio / (energy_ratio + c)
        upsilon = splev(x_new, nots, der=0) / energy_ratio
    elif scaling_type == 6:
        # protons
        x_new = energy_ratio / (energy_ratio + c)
        upsilon = 10**splev(x_new, nots, der=0)
    else:
        raise ValueError('Unrecognized BT92 scaling option.')

    return upsilon


def burgess_tully_descale_vectorize(x, y, energy_ratio, c, scaling_type):
    """
    Vectorized version of `burgess_tully_descale`
    """
    # Try the fast way; fall back to slower method if x and y are not true matrices
    # This can happen because the scaled temperatures may have a variable number of points
    try:
        func = np.vectorize(burgess_tully_descale, signature='(m),(m),(n),(),()->(n)')
        return func(x, y, energy_ratio, c, scaling_type)
    except ValueError:
        return np.array(list(map(burgess_tully_descale, x, y, energy_ratio, c, scaling_type)))
