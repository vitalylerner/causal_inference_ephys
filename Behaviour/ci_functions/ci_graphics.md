# Psychometric plots
## Part of the offline analysis of behavioural data in Causal Inference experiments 
Author: Vitaly Lerner vlerner@ur.rochester.edu

Args:
- P (list): A dataset prepared by ci_analysis 

Returns:
- bokeh row: A row of figures containing the plotted curves.

Raises:
- None.

This function takes a list of data points and plots psychometric curves based on the data.
It generates a row of figures, each figure representing a psychometric curve.

The function performs the following steps:
1. Preprocess the data points by removing any None values.
2. Set up the figure parameters such as width, height, and toolbar location.
3. Build a panel for all plots together separated by CAT3 but before separation by CAT2.
4. If there is a separation by CAT2, build a panel for each CAT2.
5. Decorate each panel using the parameters defined in the configuration file (graphics.xls).
6. Plot the data points and confidence intervals.
7. If available, plot the fitted curves.
8. Add statistics labels to the figure.
9. Set the x-range of the figure.
10. Return the row of figures.

Note:
- The function assumes that the data points are in a specific format with required attributes.
- The function uses various parameters and configurations defined in the class instance.

Example usage:
```python
from bokeh.plotting import output_file, show
from ci_functions.ci_analysis import ci_analysis
from ci_functions.ci_graphics import ci_graphics

cia = ci_analysis()
cig = ci_graphics()
P = cia.build_psychometric(...)
F = cig.plot_psychometric_curves(P)
output_file("psychometric_curves.html")
show(F)
```
