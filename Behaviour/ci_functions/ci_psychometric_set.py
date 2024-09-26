"""
Causal Inference behavioral data analysis
Can be generalized to other psychometric data.

Organizes psychometric plots data and fits psychometric curves.
Not plotting

@Author: Vitaly Lerner
@Email:  vlerner@ur.rochester.edu
"""
    
import numpy as np
from scipy.optimize import curve_fit
from ci_functions.ci_algebra import sigmoid, inversegauss


class ci_psychometric_set:
    """
    Causal Inference (but not only) psychometric plots data.

    Stores data and graphic parameters for a set of psychometric curves
    grouped together.

    Attributes
    ----------
    plots : dict
        A dictionary containing the plots data.
    fits : dict
        A dictionary containing the fitted parameters for each plot.
    name : str
        The name of the psychometric set.
    xaxis_label : str
        The label for the x-axis.
    xaxis_label_visible : bool
        A flag indicating whether the x-axis label is visible.
    yaxis_label : str
        The label for the y-axis.
    yaxis_label_visible : bool
        A flag indicating whether the y-axis label is visible.
    meta : dict
        Additional metadata for the psychometric set.

    Methods
    -------
    fit(func)
        Fits the psychometric curves using the specified function.
    __init__(plots, meta={}, name="", x_label="", x_label_visible=False, y_label="", y_label_visible=False)
        Initializes the ci_psychometric_set object.

    """

    plots = {}
    fits = {}
    name = ""
    xaxis_label = ""
    xaxis_label_visible = False
    yaxis_label = ""
    yaxis_label_visible = False
    meta = None

    def fit(self, func):
        """
        Fits the psychometric curves using the specified function.

        Parameters
        ----------
        func : str
            The name of the function to use for fitting. Valid options are 'sigmoid' and 'inversegauss'.

        Returns
        -------
        None

        """
        ks = list(self.plots.keys())
        fits = {}
        if func == 'sigmoid':
            c_f = sigmoid
            bounds = ([-2.0, 0.001], [2.0, 10.0])
        elif func == 'inversegauss':
            c_f = inversegauss
            bounds = ([-2.0, 0.001, 0.5, 0.3], [2.0, 10.0, 1.05, 1.05])
        for k in ks:
            p = self.plots[k]
            x = p.xmean
            if len(x) > 3:
                y = p.y
                rng = ~np.isnan(x + y)
                x = x[rng]
                y = y[rng]
                ylow = p.y95low[rng]
                yhi = p.y95high[rng]
                try:
                    popt, pcov = curve_fit(c_f, x, y, bounds=bounds)
                    poptlow, pcov = curve_fit(c_f, x, y)
                    popthi, pcov = curve_fit(c_f, x, y)
                    fits[k] = {'function': func, 'p_mean': popt, 'p_lo': poptlow, 'p_hi': popthi}
                except RuntimeError:
                    xx = np.array(list(x) * 3)
                    yy = np.array(list(y) + list(ylow) + list(yhi))
                    popt, pcov = curve_fit(c_f, xx, yy, bounds=bounds)
                    poptlow = popt
                    popthi = popt
                    fits[k] = {'function': func, 'p_mean': popt, 'p_lo': poptlow, 'p_hi': popthi}
                    pass
        self.fits = fits

    def __init__(self, plots: dict, meta: dict = {}, name: str = "",
                 x_label: str = "", x_label_visible: bool = False,
                 y_label: str = "", y_label_visible: bool = False):
        """
        Initializes the ci_psychometric_set object.

        Parameters
        ----------
        plots : dict
            A dictionary containing the plots data.
        meta : dict, optional
            Additional metadata for the psychometric set. The default is {}.
        name : str, optional
            The name of the psychometric set. The default is "".
        x_label : str, optional
            The label for the x-axis. The default is "".
        x_label_visible : bool, optional
            A flag indicating whether the x-axis label is visible. The default is False.
        y_label : str, optional
            The label for the y-axis. The default is "".
        y_label_visible : bool, optional
            A flag indicating whether the y-axis label is visible. The default is False.

        Returns
        -------
        None

        """
        self.plots = plots
        self.name = name
        self.y_label = y_label
        self.y_label_visible = y_label_visible
        self.x_label = x_label
        self.x_label_visible = x_label_visible
        self.meta = meta

    def __str__(self):
        """
        Casts the object to a string for displaying.

        Returns
        -------
        str
            The string representation of the object.

        """
        s = self.name
        s += f' {len(self.plots)} plots'
        return s

