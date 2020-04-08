# plot RF features importance

import numpy as np
import matplotlib.pyplot as plt
# from ctaplot.plots import plot_feature_importance
import json
from lstchain.reco.dl1_to_dl2 import joblib
import os
from matplotlib.backends.backend_pdf import PdfPages
from datetime import date


def plot_feature_importance(feature_keys, feature_importances, ax=None):
    """
    Plot features importance after model training (typically from scikit-learn)

    Parameters
    ----------
    feature_keys: list of string
    feature_importances: `numpy.ndarray`
    ax: `matplotlib.pyplot.axes`

    Returns
    -------
    ax
    """
    ax = plt.gca() if ax is None else ax

    sort_mask = np.argsort(feature_importances)[::-1]
    ax.bar(np.array(feature_keys)[sort_mask], np.array(feature_importances)[sort_mask])
    for t in ax.get_xticklabels():
        t.set_rotation(45)
    ax.set_title("Feature importances")

    return ax


def plot_feat(model_dir, pp, title):
    config_filename = \
    [os.path.join(model_dir, f) for f in os.listdir(model_dir) if f.endswith('.json') or f.endswith('.conf')][0]
    print(f"config file = {config_filename}")

    reg_disp_filename = os.path.join(model_dir, 'reg_disp_vector.sav')
    reg_energy_filename = os.path.join(model_dir, 'reg_energy.sav')
    classif_filename = os.path.join(model_dir, 'cls_gh.sav')

    reg_disp = joblib.load(reg_disp_filename)
    reg_energy = joblib.load(reg_energy_filename)
    classif = joblib.load(classif_filename)

    with open(config_filename) as file:
        config = json.load(file)

    regression_features = config['regression_features']
    classification_features = config['classification_features']

    plt.figure(figsize=(15, 10))
    plot_feature_importance(regression_features, reg_disp.feature_importances_, ax=None)
    plt.title(f'{title} DISP reconstruction features importance')
    plt.tight_layout()
    pp.savefig()
    plt.close()

    plt.figure(figsize=(15, 10))
    plot_feature_importance(regression_features, reg_energy.feature_importances_, ax=None)
    plt.title(f'{title} ENERGY reconstructure features importance')
    plt.tight_layout()
    pp.savefig()
    plt.close()

    plt.figure(figsize=(15, 10))
    plot_feature_importance(classification_features, classif.feature_importances_, ax=None)
    plt.title(f'{title} gamma/hadron classification features importance')
    plt.tight_layout()
    pp.savefig()
    plt.close()


models_directory_hipecta = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/models/20190415/south_pointing/20200402_vRTA_tailcuts_6_3/'
models_directory_lstchain = '/fefs/aswg/data/models/20190415/south_pointing/20200316_v0.4.5__EG1/'

pp = PdfPages(f'compare_lstchain_hipecta_models_{date.today()}.pdf')

for model_dir, title in zip([models_directory_hipecta, models_directory_lstchain],
                            ['hipecta', 'lstchain']
                            ):
    plot_feat(model_dir, pp, title)

pp.close()