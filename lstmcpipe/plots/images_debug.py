# to run this script you need a DL1 debug files of hipeRTA and a DL1 file from lstchain from the same run


import tables
import numpy as np
import matplotlib.pyplot as plt
from ctapipe.visualization import CameraDisplay
from ctapipe.instrument import CameraGeometry
from ctapipe.image import tailcuts_clean
from lstchain.io.io import dl1_images_lstcam_key, dl1_params_lstcam_key
from astropy.table import Table, join, Column, hstack
from ctapipe.io.containers import HillasParametersContainer
from matplotlib.backends.backend_pdf import PdfPages
from datetime import date
import astropy.units as u
from astropy.coordinates import Angle
import argparse


def tailcuts_clean_teltype(image, camera_name='LSTCam', **kwargs):

    return tailcuts_clean(geom, image, **kwargs)


def get_hillas_container(row):
    h = HillasParametersContainer()
    h.x = row['x'] * 28 * u.m
    h.y = row['y'] * 28 * u.m
    h.r = row['r'] * 28 * u.m
    h.phi = Angle(row['phi'] * u.rad)
    h.width = row['width'] * u.m
    h.length = row['length'] * u.m
    h.psi = Angle(row['psi'] * u.rad)
    h.skewness = row['skewness']
    h.kurtosis = row['kurtosis']
    return h



dl1_hipecta_filename = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/run1/dl1_6_3_2_gamma_20deg_180deg_run1___cta-prod3-demo-2147m-LaPalma-baseline-mono_off0.4.h5'
dl1_lstchain_filename = '/fefs/aswg/workspace/thomas.vuillaume/mchdf5/run1/lstchain/GlobalPeakIntegrator/dl1_gamma_20deg_180deg_run1___cta-prod3-demo-2147m-LaPalma-baseline-mono_off0.4.simtel.h5'


def main(dl1_hipecta_filename, dl1_lstchain_filename):

    geom = CameraGeometry.from_name('LSTCam')

    dl1_hipecta = tables.open_file(dl1_hipecta_filename)
    dl1_lstchain = tables.open_file(dl1_lstchain_filename)

    with tables.open_file(dl1_hipecta_filename) as dl1_hipecta:
        hipecta_images = Table(dl1_hipecta.root.dl1.Tel_1.calib_pic.read())
        hipecta_parameters = Table(dl1_hipecta.root.dl1.Tel_1.parameters.read())

    with tables.open_file(dl1_lstchain_filename) as dl1_lstchain:
        simu_table = Table(dl1_lstchain.root.dl1.event.simulation.LST_LSTCam.read())
        lstchain_images = Table(dl1_lstchain.root[dl1_images_lstcam_key].read())


    hipecta = join(hipecta_images, hipecta_parameters, keys='event_id')

    lstchain_table = hstack([lstchain_images, simu_table], join_type='exact')
    lstchain_table.rename_column('tel_id_1', 'tel_id')
    lstchain_table.remove_column('tel_id_2')


    mega_table = join(lstchain_table[lstchain_table['tel_id']==1],
                     hipecta, 
                     uniq_col_name='{table_name}_{col_name}',
                     table_names = ['lstchain', 'hipecta'],
                     keys='event_id'
                    )



    selected_table = mega_table[:30]



    params_cleaning = dict(picture_thresh=6,
                           boundary_thresh=3,
                           keep_isolated_pixels=False,
                           min_number_picture_neighbors=2)




    lstchain_cleaning = np.apply_along_axis(tailcuts_clean_teltype, selected_table['image'], **params_cleaning)
    selected_table.add_column(Column(lstchain_cleaning, dtype=int), name='lstchain_clean_mask')


    with PdfPages(f'compare_lstchain_hipecta_images_{date.today()}.pdf') as pp:

        for ii, row in enumerate(selected_table[:10]):
            print(f"{ii}. event id : {row['event_id']}")
        #     print(row)
            h = get_hillas_container(row)

            image_lstchain = row['image']
            image_hipecta = row['signal']

            clean_mask_ctapipe_on_lstchain = row['lstchain_clean_mask']
            clean_mask_ctapipe_on_hipecta = tailcuts_clean(geom, image_hipecta, **params_cleaning)
            clean_mask_hipecta = row['clean_mask'].astype(bool)

            fig, axes = plt.subplots(2,3, figsize=(12,6))
        #     axes[0,2].remove()
            display = CameraDisplay(geom, image_lstchain, ax=axes[0,0])
            display.add_colorbar(ax=axes[0,0])
            axes[0,0].set_title('lstchain image')
            display = CameraDisplay(geom, clean_mask_ctapipe_on_lstchain, ax=axes[0,1])
        #     display.add_colorbar(ax=axes[0,1])
            display.highlight_pixels(clean_mask_ctapipe_on_lstchain.astype(bool), color='red')
            axes[0,1].set_title('lstchain clean mask')
            display = CameraDisplay(geom, image_hipecta, ax=axes[1,0])
            display.add_colorbar(ax=axes[1,0])
            axes[1,0].set_title('hipecta image')


            display = CameraDisplay(geom, clean_mask_hipecta, ax=axes[1,1])
        #     display.add_colorbar(ax=axes[1,1])
            display.highlight_pixels(clean_mask_ctapipe_on_hipecta, color='red')
            axes[1,1].set_title('hipecta clean mask')
            axes[1,1].text(0.88,0.88,s='cleaning mask\nfrom ctapipe',color='red')
            axes[1,1].text(-1.5, 0.88, s=f'n_islands={row["n_islands"]}', color='black')
            display.overlay_moments(h)


            display = CameraDisplay(geom, row['photo_electron_image'], ax=axes[0,2])
            display.add_colorbar(ax=axes[0,2])
            axes[0,2].set_title('true pe image')
            display.highlight_pixels(clean_mask_ctapipe_on_lstchain.astype(bool), color='red')
            axes[0,2].text(0.88, 0.88, s='cleaning mask\nfrom ctapipe', color='red')

            display = CameraDisplay(geom, row['photo_electron_image'], ax=axes[1,2])
            display.add_colorbar(ax=axes[1,2])
            axes[1,2].set_title('true pe image')
            display.highlight_pixels(clean_mask_hipecta, color='red')
            axes[1,2].text(0.88,0.88,s='cleaning mask\nfrom hipecta',color='red')

            plt.tight_layout()
            pp.savefig(dpi=100)



if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="Reconstruct events")
    parser.add_argument('--dl1_lstchain', '-lst',
                        type=str,
                        dest='dl1_lstchain_filename',
                        help='path to the lstchain DL1 file',
                        default=dl1_lstchain_filename)
    
    parser.add_argument('--dl1_hipecta', '-hipe',
                        type=str,
                        dest='dl1_hipecta_filename',
                        help='path to the hiperta debug DL1 file',
                        default=dl1_hipecta_filename)
    
    args = parser.parse_args()
        
    main(args.dl1_hipecta_filename, args.dl1_lstchain_filename)
