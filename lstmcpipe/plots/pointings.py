import matplotlib.pyplot as plt


def plot_pointings(pointings, ax=None, projection=None, **kwargs):
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

    ax.scatter(pointings[:, 0], pointings[:, 1], **kwargs)

    ax.set_xlabel('Azimuth')
    ax.set_ylabel('Altitude')
    ax.legend()
    ax.grid(True)

    return ax

