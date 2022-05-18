import matplotlib.pyplot as plt


def plot_pointings(pointings, ax=None, projection=None, **kwargs):
    """
    Produce a scatter plot of the pointings based on parsed pointings paths

    Parameters
    ----------
    pointings: numpy.array
        2D (alt, az)
    training : bool
        Plot training pointings
    testing: bool
        Plot testing pointings
    ax: `matplotlib.pyplot.axis`
    kwargs: dict
        kwargs for `matplotlib.pyplot.scatter`
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

