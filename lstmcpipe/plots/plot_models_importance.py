# plot RF features importance

import numpy as np
import matplotlib.pyplot as plt
import os

from lstchain.visualization.plot_dl2 import plot_models_features_importances

import argparse

parser = argparse.ArgumentParser(description='Plot features importances from trained random forests models')
parser.add_argument('models_path',
                    help='path to the trained models')
parser.add_argument('--config_file', 
                    '-cf',
                    default=None,
                    help='Path to the config file. Optional.'
                    
                   ),

args = parser.parse_args()


if __name__ == '__main__':
    
    axes = plot_models_features_importances(args.models_path, config_file=args.config_file)

    plt.savefig(os.path.join(args.models_path, 'features_importances.png'))

    
