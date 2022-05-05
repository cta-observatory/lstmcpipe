# Full AllSky production

## lstchain config

from
https://github.com/cta-observatory/cta-lstchain/blob/1f3cf1f5b30ead161a4bcac760e00ada719655a8/lstchain/data/lstchain_standard_config.json



## lstmcpipe config

Constructed by modifying paths_config `PathConfigAllSky`:
```
class PathConfigAllSky(PathConfig):
    """
    Standard paths configuration for a prod5_trans_80 MC production
    """

    def __init__(self, prod_id, dec):
        super().__init__(prod_id)
        self.prod_id = prod_id
        self.base_dir = os.path.join("/fefs/aswg/data/mc/{data_level}/AllSky/{prod_id}/{particle}/", dec, "{pointing}")
        # self.base_dir = os.path.join("/fefs/aswg/workspace/thomas.vuillaume/data/mc/{data_level}/AllSky/{prod_id}/{particle}/", dec, "/sim_telarray/{pointing}/output")
        self.training_dir = \
            os.path.join("/home/georgios.voutsinas/ws/AllSky/TrainingDataset/{particle}/", dec, "/sim_telarray/{pointing}/output/")
        self.testing_dir = "/home/georgios.voutsinas/ws/AllSky/TestDataset/sim_telarray/{pointing}/output_v1.4/"

        self.training_particles = ['GammaDiffuse', 'Protons']
        self.testing_particles = ['Crab']

        self.paths = {}
        self.stages = ['r0_to_dl1', 'merge_dl1', 'train_pipe', 'dl1_to_dl2', 'dl2_to_irfs']

```
