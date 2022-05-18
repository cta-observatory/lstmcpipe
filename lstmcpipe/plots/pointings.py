import mpl_toolkits
import matplotlib.pyplot as plt
import numpy as np


def plot_pointings(pointings, ax=None, projection=None, add_grid3d=False, **kwargs):
    """
    Produce a scatter plot of the pointings

    Parameters
    ----------
    pointings: 2D array of `astropy.quantities` or numpy array in rad
    ax : `matplotlib.pyplot.Axis`
    projection: str or None
        'aitoff' | 'hammer' | 'lambert' | 'mollweide'
    kwargs: dict
        kwargs for `matplotlib.pyplot.scatter`

    Returns
    -------
    ax: `matplotlib.pyplot.axis`
    """
    if ax and projection:
        raise ValueError("ax and projection are exclusive")
        
    if ax is None:
        fig = plt.gcf()
        ax = fig.add_subplot(111, projection=projection)
    elif isinstance(ax, mpl_toolkits.mplot3d.axes3d.Axes3D):
        projection='3d'
        
    if projection == '3d':
        r = 1.
        if add_grid3d:
            az, alt = np.mgrid[0:2.01*np.pi:(1/10)* np.pi/2., 0:np.pi/2.:(1/10)* np.pi/4.]
            X = r * np.cos(az) * np.cos(alt)
            Y = r * np.sin(az) * np.cos(alt)
            Z = r * np.sin(alt)
            ax.plot_surface(X, Y, Z, cmap=plt.cm.YlGnBu_r, alpha=.1)
        r *= 1.01
        az = pointings[:,0]
        alt = pointings[:,1]
        X = r * np.cos(az) * np.cos(alt)
        Y = r * np.sin(az) * np.cos(alt)
        Z = r * np.sin(alt)

        ax.scatter(X, Y, Z, **kwargs)

        box_ratio=1.03
        ax.set_xlim3d([-r*box_ratio, r*box_ratio])
        ax.set_ylim3d([-r*box_ratio, r*box_ratio])
        ax.set_zlim3d([-r*box_ratio, r*box_ratio])
        
    else:
        ax.scatter(pointings[:, 0], pointings[:, 1], **kwargs)
        ax.set_xlabel('Azimuth')
        ax.set_ylabel('Altitude')
        
        
    ax.legend()
    ax.grid(True)

    return ax

