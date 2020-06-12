# compare DL1 between lstchain and hipecta

import numpy as np
import matplotlib.pyplot as plt
from ctapipe.visualization import CameraDisplay
from ctapipe.instrument import CameraGeometry
from lstchain.io.io import dl1_images_lstcam_key, dl1_params_lstcam_key, dl2_params_lstcam_key
from astropy.table import Table, join, hstack
from datetime import date
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.colors import LogNorm

pp = PdfPages(f'{date.today()}_dl1_compare_lstchain_hipecta.pdf')

# filename_hipecta = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/run1/dl1_gamma_20deg_180deg_run1___cta-prod3-demo-2147m-LaPalma-baseline-mono_off0.4.h5'

filename_hipecta = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL1/20190415/gamma/south_pointing/20200506_vRTA_v0.4.5_tailcuts_6_3_no_intercept/testing/dl1_reorganized_gamma_20deg_180deg_run1___cta-prod3-demo-2147m-LaPalma-baseline-mono_off0.4.h5'
filename_hipecta = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/run1/dl1_recalculated_gamma_20deg_180deg_run1___cta-prod3-demo-2147m-LaPalma-baseline-mono_off0.4.h5'
# filename_lstchain = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/run1/lstchain/dl1_gamma_20deg_180deg_run1___cta-prod3-demo-2147m-LaPalma-baseline-mono_off0.4.simtel.h5'
filename_lstchain = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL1/20190415/gamma/south_pointing/20200529_vRTA_v0.5.1_v00/testing/dl1_reorganized_gamma_20deg_180deg_run1___cta-prod3-demo-2147m-LaPalma-baseline-mono_off0.4.h5'

geom = CameraGeometry.from_name('LSTCam')
geom2 = CameraGeometry.from_name('LSTCam-002')

# hp = Table.read(filename_hipecta, path=dl1_params_lstcam_key)
import pandas as pd
df = pd.read_hdf(filename_hipecta, key=dl1_params_lstcam_key)
hp = Table.from_pandas(df)

hi = Table.read('/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL1/20190415/gamma/south_pointing/20200529_vRTA_v0.5.1_recalculated/dl1_recalculated_gamma_south_pointing_20200529_vRTA_v0.5.1_v00_DL1_t3st1ng_bckp.h5', path=dl1_images_lstcam_key)
# hi = Table.read(filename_hipecta, path=dl1_images_lstcam_key)
hi.rename_column('signal', 'image')
hp['log_intensity'] = np.log10(hp['intensity'])

print(f"{len(hp)} events in hipecta file, {np.count_nonzero(hp['is_good_event'])} well reconstructed")

lp = Table.read(filename_lstchain, path=dl1_params_lstcam_key)
li = Table.read(filename_lstchain, path=dl1_images_lstcam_key)

print(f"{len(lp)} events in lstchain file")

ht = join(hp, hi, keys=['event_id', 'tel_id'])
lt = join(lp, li, keys=['event_id', 'tel_id'])

mega_table = join(lt, ht, keys=['event_id', 'tel_id'], uniq_col_name='{table_name}_{col_name}',
                  table_names=['lstchain', 'hipecta']);

print(f"{len(mega_table)} events in common")

filter = (mega_table['is_good_event'] == 1) & (mega_table['hipecta_n_islands'] == 1) # & (mega_table['lstchain_n_islands'] == 1) #
# filter = np.ones(len(mega_table), dtype=bool)

print(f"Only {np.count_nonzero(filter)} common events well reconstructed by hipecta will be included in the following plots")

selected_events = mega_table[filter]

opt = dict(bins=100, histtype='step', linewidth=3, log=True)

for col_hipe in [c for c in selected_events.columns if 'hipecta_' in c]:
    # for col_hipe in ['hipecta_src_x', 'hipecta_wl']:

    col_lst = col_hipe.replace('hipecta_', 'lstchain_')
    feature_name = col_hipe.replace('hipecta_', '')
    print(feature_name)
    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    both_finite = np.isfinite(selected_events[col_lst]) & np.isfinite(selected_events[col_hipe])

    if np.count_nonzero(both_finite) > 1:
        r = (selected_events[col_lst][both_finite].min(), selected_events[col_lst][both_finite].max())
        axes[0].hist(selected_events[col_lst][both_finite], **opt, range=r, label='lstchain')
        axes[0].hist(selected_events[col_hipe][both_finite], **opt, range=r, label='hipecta')
        axes[0].set_xlabel(feature_name, fontsize=16)
        axes[0].legend(fontsize=16)
        axes[0].grid()

        axes[1].hist2d(selected_events[col_lst][both_finite], selected_events[col_hipe][both_finite], bins=100, range=(r,r), norm=LogNorm())
        axes[1].set_xlabel('lstchain')
        axes[1].set_ylabel('hipecta')
        axes[1].set_title(feature_name)

        plt.tight_layout()
        pp.savefig()
        plt.close()

## pick a few random images to compare
rows = np.random.choice(selected_events, 5)
for row in rows:
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    fig.suptitle(f"event id = row['event_id']")

    for ii, name in enumerate(['lstchain_image', 'lstchain_pulse_time',
                               'hipecta_image', 'hipecta_pulse_time',
                               ]):
        ax = axes.ravel()[ii]
        d = CameraDisplay(geom, row[name], ax=ax)
        d.add_colorbar(ax=ax)
        ax.set_title(name)

    pp.savefig()

rows = np.random.choice(selected_events[selected_events['lstchain_intensity'] > 500], 5)
for row in rows:
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))
    fig.suptitle(f"event id = row['event_id']")

    for ii, name in enumerate(['lstchain_image', 'lstchain_pulse_time',
                               'hipecta_image', 'hipecta_pulse_time',
                               ]):
        ax = axes.ravel()[ii]
        d = CameraDisplay(geom, row[name], ax=ax)
        d.add_colorbar(ax=ax)
        ax.set_title(name)

    pp.savefig()

pp.close()
