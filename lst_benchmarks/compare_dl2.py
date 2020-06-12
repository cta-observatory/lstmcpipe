## Make comparison plots on DL2 data for each particle file in directories

import numpy as np
import pandas as pd
from lstchain.io.io import dl2_params_lstcam_key
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from datetime import date
import ctaplot
from lstchain.io.io import read_simu_info_merged_hdf5
import astropy.units as u

savedir = 'plots'
os.makedirs(savedir, exist_ok=True)
pp = PdfPages(f'{date.today()}_dl2_compare_lstchain_hipecta.pdf')


lstchain_d = {}
hipecta_d = {}
lstchain_d['dir'] = '../20200229_v0.4.4/lstchain'
hipecta_d['dir'] = '.'

# La Palma

lstchain_dir_id = '20200527_v0.5.1_global'
hipecta_dir_id = '20200529_vRTA_v0.5.1_recalculated'

# lstchain_d['dir'] = '/fefs/aswg/data/mc/DL2/20190415/{particle}/south_pointing/20200316_v0.4.5__EG1/'
lstchain_d['dir'] = os.path.join('/fefs/aswg/data/mc/DL2/20190415/{particle}/south_pointing/', lstchain_dir_id)
# hipecta_d['dir'] = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL2/20190415/{particle}/south_pointing/20200407_vRTA_no_intercept/'
# hipecta_d['dir'] = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL2/20190415/{particle}/south_pointing/20200410_vRTA_v0.4.5.post117+git62d122d_tailcuts_6_3_no_intercept/'
hipecta_d['dir'] = os.path.join('/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL2/20190415/{particle}/south_pointing/', hipecta_dir_id)


filename_simu = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/DL2/20190415/gamma/south_pointing/20200529_vRTA_v0.5.1_v00/dl2_gamma_south_pointing_20200529_vRTA_v0.5.1_v00_DL1_testing.h5'

particles = ['gamma', 'proton', 'electron']

# La Palma
for dic in [lstchain_d, hipecta_d]:
    for particle in particles:
        particle_dir = dic['dir'].format(particle=particle)
        filename = [os.path.join(particle_dir, f) for f in os.listdir(particle_dir) if 'testing' in f][0]
        dic[particle] = {}
        dic[particle]['filename'] = filename
        dic[particle]['simu_info'] = read_simu_info_merged_hdf5(filename_simu)
        dic[particle]['events'] = pd.read_hdf(filename, key=dl2_params_lstcam_key)
        
        # some rescaling 
#         if dic is hipecta_d:
#             dic[particle]['events']['reco_energy'] *= 1e3
#             dic[particle]['events']['log_mc_energy'] += 3
#             dic[particle]['events']['log_reco_energy'] += 3

        
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


common_filters = ['gammaness > 0.1', 'intensity > 200', 'tel_id==1', 'r<1']
print(common_filters)

for p in particles:
    filter_good_events = hipecta_d[p]['events']['is_good_event'] == 1
    hipe = hipecta_d[p]['events'][filter_good_events]
    lst = lstchain_d[p]['events']
    
    print(f"{len(hipecta_d[p]['events'])} events in hipecta file and {len(hipe)} good events")
    
    for f in common_filters:
        hipe = hipe.query(f)
        lst = lst.query(f)
        
    print(f"{len(hipe)} events in hipecta after common filters")
    print(f"{len(lst)} events in lstchain after common filters")

    if p == 'gamma':
        hipe_sel = hipe[(hipe.intensity > 200)
                        & (hipe.gammaness > 0.6)
#                         & (hipe.leakage < 0.2) 
#                         & (hipe.n_islands==1)
                        #&
#                         (hipe.wl > 0.2) &
#                         (hipe.wl < 0.98) &
#                         (hipe.skewness > 0) &
#                         (hipe.r < 0.6)
                       ]
        lst_sel = lst[(lst.intensity > 200) 
                      & (lst.gammaness > 0.7) 
#                       & (lst.leakage < 0.2) 
#                       & (lst.n_islands==1)
#                       & (lst.wl > 0.2)
#                       & (lst.wl < 0.98)
#                       & (lst.r < 0.6) 
#                       & (lst.skewness > 0)
                     ]
        
        print(f"{len(hipe_sel)} events in hipecta after specific filters")
        print(f"{len(lst_sel)} events in lstchain after specific filters")
        
        text = f"{len(hipecta_d[p]['events'])} events in hipecta file and {len(hipe)} good events\n"
        text += f"common filters:\n{common_filters}\n"
        text += f"{len(hipe)} events in hipecta after common filters\n"
        text += f"{len(lst)} events in lstchain after common filters\n"
        text += f"{len(hipe_sel)} events in hipecta after specific filters\n"
        text += f"{len(lst_sel)} events in lstchain after specific filters\n"
        
        firstPage = plt.figure(figsize=(11.69,8.27))
        firstPage.clf()
        firstPage.text(0.2,0.5, text, transform=firstPage.transFigure, size=11, ha="center")
        pp.savefig()
        plt.close()
        
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
        
    
    plt.figure(figsize=(15,10))
    simu_info = hipecta_d[p]['simu_info']
    ctaplot.plot_effective_area_per_energy_power_law(simu_info.energy_range_min.to(u.TeV).value,
                                                     simu_info.energy_range_max.to(u.TeV).value,
                                                     simu_info.shower_reuse * simu_info.num_showers,
                                                     simu_info.spectral_index,
                                                     hipe.query('tel_id==1').reco_energy,
                                                     np.pi*(simu_info.max_scatter_range.to(u.m)**2-simu_info.min_scatter_range.to(u.m)**2).value,
                                                     linestyle='--',
                                                     label = 'hipecta'
                                                    )
    ctaplot.plot_effective_area_per_energy_power_law(simu_info.energy_range_min.to(u.TeV).value,
                                                     simu_info.energy_range_max.to(u.TeV).value,
                                                     simu_info.shower_reuse * simu_info.num_showers,
                                                     simu_info.spectral_index,
                                                     hipe_sel.query('tel_id==1').reco_energy,
                                                     np.pi*(simu_info.max_scatter_range.to(u.m)**2-simu_info.min_scatter_range.to(u.m)**2).value,
                                                     label = 'hipecta specific selection'
                                                    )
    
    simu_info = lstchain_d[p]['simu_info']
    ctaplot.plot_effective_area_per_energy_power_law(simu_info.energy_range_min.to(u.TeV).value,
                                                     simu_info.energy_range_max.to(u.TeV).value,
                                                     simu_info.shower_reuse * simu_info.num_showers,
                                                     simu_info.spectral_index,
                                                     lst.query('tel_id==1').reco_energy,
                                                     np.pi*(simu_info.max_scatter_range.to(u.m)**2-simu_info.min_scatter_range.to(u.m)**2).value,
                                                     label = 'lstchain',
                                                     linestyle='--'
                                                    )
    ctaplot.plot_effective_area_per_energy_power_law(simu_info.energy_range_min.to(u.TeV).value,
                                                     simu_info.energy_range_max.to(u.TeV).value,
                                                     simu_info.shower_reuse * simu_info.num_showers,
                                                     simu_info.spectral_index,
                                                     lst_sel.query('tel_id==1').reco_energy,
                                                     np.pi*(simu_info.max_scatter_range.to(u.m)**2-simu_info.min_scatter_range.to(u.m)**2).value,
                                                     label = 'lstchain specific selection'
                                                    )
    
    print(simu_info.spectral_index)
    
    ctaplot.plot_effective_area_cta_performance('north', color='black')
    plt.legend(fontsize=18)
    plt.grid()
    plt.tight_layout()
    pp.savefig()   
    plt.close()

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
        opt = dict(bins=100, histtype='step', log=True, linewidth=3)
        lst[c].hist(label='lstchain', **opt)
        hipe[c].hist(label='hipecta', **opt)

        mc_c = c.replace('reco_', 'mc_')
        if  mc_c in set(lst.columns) and mc_c != c:
            lst[mc_c].hist(**opt, label='MC', color='black', linestyle='--')

                
        plt.legend(fontsize=15)
        plt.title(f'{p} {c}')
        pp.savefig()
        plt.tight_layout()
        plt.close()

pp.close()
