## Make comparison plots on DL2 data for each particle file in directories

import numpy as np
import pandas as pd
from lstchain.io.io import dl2_params_lstcam_key
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import date
import ctaplot

savedir = 'plots'
os.makedirs(savedir, exist_ok=True)
pp = PdfPages(f'compare_lstchain_hipecta_dl2_{date.today()}.pdf')


lstchain_d = {}
hipecta_d = {}
lstchain_d['dir'] = '../20200229_v0.4.4/lstchain'
hipecta_d['dir'] = '.'

# La Palma
lstchain_d['dir'] = '/fefs/aswg/data/mc/DL2/20190415/{particle}/south_pointing/20200316_v0.4.5__EG1/'
# hipecta_d['dir'] = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL2/20190415/{particle}/south_pointing/20200407_vRTA_no_intercept/'
hipecta_d['dir'] = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL2/20190415/gamma/south_pointing/20200411_vRTA_v0.4.5.post117+git62d122d_test_dl1_dl2/'


particles = ['gamma', 'proton', 'electron']

# La Palma
for dic in [lstchain_d, hipecta_d]:
    for particle in particles:
        particle_dir = dic['dir'].format(particle=particle)
        filename = [os.path.join(particle_dir, f) for f in os.listdir(particle_dir) if 'testing' in f][0]
        dic[particle] = pd.read_hdf(filename, key=dl2_params_lstcam_key)
        
        # some rescaling 
        if dic is hipecta_d:
            dic[particle]['reco_energy'] *= 1e3
            dic[particle]['log_mc_energy'] += 3
            dic[particle]['log_reco_energy'] += 3

        
# # laptop where all files are in the same dir
# for dic in [lstchain_d, hipecta_d]:
#     files = [os.path.join(dic['dir'], f) for f in os.listdir(dic['dir']) if f.endswith('.h5')]
#     for f in files:
#         for p in particles:
#             if p in f:
#                 dic[p] = pd.read_hdf(f, key=dl2_params_lstcam_key)


# hipe_all = pd.concat([hipecta_d[p] for p in particles])
# lst_all = pd.concat([lstchain_d[p] for p in particles])
#
# plt.figure()
# ctaplot.plot_roc_curve_gammaness(hipe_all.query('is_good_event == 1').mc_type, hipe_all.query('is_good_event == 1').gammaness, label='hipecta')
# ctaplot.plot_roc_curve_gammaness(lst_all.mc_type, lst_all.gammaness, label='lstchain')
# plt.legend()
# plt.title('ROC')
# pp.savefig()



for p in particles:
    filter_good_events = hipecta_d[p]['is_good_event'] == 1
    hipe = hipecta_d[p][filter_good_events]
    lst = lstchain_d[p]

    if p == 'gamma':
        hipe_sel = hipe[(hipe.gammaness > 0.7) & (hipe.leakage < 0.2) & (hipe.intensity > 200)]
        lst_sel = lst[(lst.gammaness > 0.7) & (lst.leakage < 0.2) & (lst.intensity > 200)]
        plt.figure(figsize=(15,10))
        ctaplot.plot_energy_resolution(hipe_sel.mc_energy, hipe_sel.reco_energy, label='hipecta')
        ctaplot.plot_energy_resolution(lst_sel.mc_energy, lst_sel.reco_energy, label='lstchain')
        plt.legend(fontsize=15)
        plt.title('energy resolution')
        plt.grid()
        plt.ylim(0, 1)
        plt.tight_layout()
        pp.savefig()

        plt.figure(figsize=(15,10))
        ctaplot.plot_energy_bias(hipe_sel.mc_energy, hipe_sel.reco_energy, label='hipecta')
        ctaplot.plot_energy_bias(lst_sel.mc_energy, lst_sel.reco_energy, label='lstchain')
        plt.legend(fontsize=15)
        plt.title('energy bias')
        plt.grid()
        plt.ylim(-1, 1)
        plt.tight_layout()
        pp.savefig()

        plt.figure(figsize=(15,10))
        ctaplot.plot_angular_resolution_per_energy(hipe_sel.reco_alt, hipe_sel.reco_az, hipe_sel.mc_alt, hipe_sel.mc_az, hipe_sel.mc_energy, label='hipecta')
        ctaplot.plot_angular_resolution_per_energy(lst_sel.reco_alt, lst_sel.reco_az, lst_sel.mc_alt, lst_sel.mc_az, lst_sel.mc_energy, label='lstchain')
        plt.legend(fontsize=15)
        plt.title('angular resolution')
        plt.ylim(0, 1)
        plt.grid()
        plt.tight_layout()
        pp.savefig()

        plt.close('all')

    fig, axes = plt.subplots(1, 2, figsize=(15,6))
    fig.suptitle(p)
    ctaplot.plot_migration_matrix(hipe.log_mc_energy, hipe.log_reco_energy, ax=axes[0])
    ctaplot.plot_migration_matrix(lst.log_mc_energy, lst.log_reco_energy, ax=axes[1])
    for ax in axes:
        ax.set_xlabel('log_mc_energy')
        ax.set_ylabel('log_reco_energy')
    axes[0].set_title('hipecta')
    axes[1].set_title('lstchain')
    plt.tight_layout()
    pp.savefig()
    plt.close()

    for feature in ['alt', 'az']:
        fig, axes = plt.subplots(1, 2, figsize=(15,6))
        fig.suptitle(p)
        ctaplot.plot_migration_matrix(hipe[f'mc_{feature}'], hipe[f'reco_{feature}'], ax=axes[0])
        ctaplot.plot_migration_matrix(lst[f'mc_{feature}'], lst[f'reco_{feature}'], ax=axes[1])
        for ax in axes:
            ax.set_xlabel(f'mc_{feature}')
            ax.set_ylabel(f'reco_{feature}')
        axes[0].set_title('hipecta')
        axes[1].set_title('lstchain')
        plt.tight_layout()
        pp.savefig()
        plt.close()


    for feature in ['disp_dx', 'disp_dy', 'src_x', 'src_y']:
        fig, axes = plt.subplots(1, 2, figsize=(15,6))
        fig.suptitle(p)
        ctaplot.plot_migration_matrix(hipe[f'{feature}'], hipe[f'reco_{feature}'], ax=axes[0])
        ctaplot.plot_migration_matrix(lst[f'{feature}'], lst[f'reco_{feature}'], ax=axes[1])
        for ax in axes:
            ax.set_xlabel(f'mc_{feature}')
            ax.set_ylabel(f'reco_{feature}')
        axes[0].set_title('hipecta')
        axes[1].set_title('lstchain')
        plt.tight_layout()
        pp.savefig()
        plt.close()



    for c in set(lst.columns).intersection(set(hipe.columns)):

        fig = plt.figure(figsize=(15,10))
        lst[c].hist(bins=100, histtype='step', label='lstchain', log=True, linewidth=3)
        hipe[c].hist(bins=100, histtype='step', label='hipecta', log=True, linewidth=3)
        plt.legend(fontsize=15)
        plt.title(f'{p} {c}')
        pp.savefig()
        plt.tight_layout()
        plt.close()

pp.close()
