"""
Common algebraic functions
"""

import numpy as np

def sigmoid(x, a0, a1):
    """
    Compute the sigmoid function.

    Parameters:
    - x: Input value
    - a0: Sigmoid offset
    - a1: Sigmoid scale

    Returns:
    - Sigmoid value
    """
    return 1.0 / (1.0 + np.exp(-(x-a0)/a1))

def inversegauss(x, a0, a1, a2, a3):
    """
    Compute the inverse Gaussian function.

    Parameters:
    - x: Input value
    - a0: Gaussian center
    - a1: Gaussian width
    - a2: Gaussian amplitude
    - a3: Gaussian offset

    Returns:
    - Inverse Gaussian value
    """
    return a2 - a3 * np.exp(-(x-a0)**2 / (2.0*a1**2))
"""
Common algebraic functions
"""

