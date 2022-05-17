import matplotlib.pyplot as plt


def plot_pointings(pointings, fig=None, projection=None, **kwargs):
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
    fig = plt.gcf() if fig is None else fig
    ax = fig.add_subplot(111, projection=projection)

    ax.scatter(pointings[:, 0], pointings[:, 1], **kwargs)

    ax.set_xlabel('Azimuth')
    ax.set_ylabel('Altitude')
    ax.legend()

    return fig
