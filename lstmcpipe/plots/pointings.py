import mpl_toolkits
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import astropy.units as u


def plot_pointings(pointings, ax=None, projection='polar', add_grid3d=False, **kwargs):
    """
    Produce a scatter plot of the pointings

    Parameters
    ----------
    pointings: 2D array of `astropy.quantities` or numpy array in rad
    ax : `matplotlib.pyplot.Axis`
    projection: str or None
        '3d' | 'aitoff' | 'hammer' | 'lambert' | 'mollweide' | 'polar' | 'rectilinear'
    add_grid3d: bool
        add a 3D grid in case of projection='3d'
    kwargs: dict
        kwargs for `matplotlib.pyplot.scatter`

    Returns
    -------
    ax: `matplotlib.pyplot.axis`
    """
    
    if ax and projection:
        if not isinstance(ax, matplotlib.projections.get_projection_class(projection)):
            raise ValueError(f"ax of type {type(ax)} and projection {projection} are exclusive")
        
    if ax is None:
        fig = plt.gcf()
        ax = fig.add_subplot(111, projection=projection)
    
    elif isinstance(ax, mpl_toolkits.mplot3d.axes3d.Axes3D):
        projection = '3d'
    elif isinstance(ax, matplotlib.projections.polar.PolarAxes):
        projection = 'polar'
        
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
        
    elif projection == 'polar':
        ax.scatter(pointings[:, 0], np.pi/2.*u.rad - pointings[:, 1], **kwargs)
        ax.set_xlabel('Azimuth')
        rticks_deg = [10, 30, 50, 70, 90]
        ax.set_rticks(np.deg2rad(rticks_deg), labels=[f'{r}°' for r in rticks_deg])
        ax.set_rmax(np.pi/2.)
        ax.set_rlabel_position(20)
        
        
    else:
        ax.scatter(pointings[:, 0], pointings[:, 1], **kwargs)
        ax.set_xlabel('Azimuth')
        ax.set_ylabel('Altitude')
        
        
    ax.legend()
    ax.grid(True)
    ax.set_axisbelow(True)

    return ax

