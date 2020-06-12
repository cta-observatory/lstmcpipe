# plot RF features importance

import numpy as np
import matplotlib.pyplot as plt
# from ctaplot.plots import plot_feature_importance
import json
from lstchain.reco.dl1_to_dl2 import joblib
import os
from matplotlib.backends.backend_pdf import PdfPages
from datetime import date


def plot_feature_importance(feature_keys, feature_importances, ax=None, **kwargs):
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
    ax.bar(np.array(feature_keys)[sort_mask], np.array(feature_importances)[sort_mask], **kwargs)
    for t in ax.get_xticklabels():
        t.set_rotation(45)
    ax.set_title("Feature importances")

    return ax

    

def plot_feat(model_dir, axes=None, **kwargs):
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
    
    if axes is None:
        fig, axes = plt.subplots(3, 1, figsize=(10, 30))
    
    plot_feature_importance(regression_features, reg_disp.feature_importances_, ax=axes[0], **kwargs)
    axes[0].set_title('DISP reconstruction features importance')
    
    plot_feature_importance(regression_features, reg_energy.feature_importances_, ax=axes[1], **kwargs)
    axes[1].set_title('ENERGY reconstructure features importance')

    plot_feature_importance(classification_features, classif.feature_importances_, ax=axes[2], **kwargs)
    axes[2].set_title('gamma/hadron classification features importance')
    
    if 'label' in kwargs:
        for ax in axes:
            ax.legend(fontsize=15)
    
    return axes


models_directory_hipecta = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/models/20190415/south_pointing/20200506_vRTA_v0.4.5_tailcuts_6_3_no_intercept'

models_directory_lstchain = '/fefs/aswg/data/models/20190415/south_pointing/20200316_v0.4.5__EG1/'



pp = PdfPages(f'{date.today()}_models_compare_lstchain_hipecta.pdf')


axes = plot_feat(models_directory_hipecta, label='hipecta')
axes = plot_feat(models_directory_lstchain,
          axes=axes,
          fill=False,
          label='lstchain',
          linewidth=4
         )


pp.savefig()
pp.close()