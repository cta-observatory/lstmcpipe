from lstmcpipe.plots.pointings import plot_pointings
import numpy as np
import astropy.units as u
from matplotlib import projections

def test_plot_pointings():
    pointings = np.random.rand(10, 2) * u.rad
    for proj in projections.get_projection_names():
        plot_pointings(pointings, projection=proj, add_grid3d=True, color='black', marker='*', alpha=0.4)
