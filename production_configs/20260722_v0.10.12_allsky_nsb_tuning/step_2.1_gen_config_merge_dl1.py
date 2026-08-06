import os
from pathlib import Path

from lstmcpipe.config.paths_config import PathConfig


class PathConfigMergeTestingEveryNode(PathConfig):
    def __init__(self, prod_id, dec, particle="Gamma", dataset_type="TestingDataset"):
        super().__init__(prod_id)
        self.dec = dec
        self.particle = particle
        self.dataset_type = dataset_type
        self.stages = ["merge_dl1"]

        self.base_dir = (
            f"/fefs/aswg/data/mc/DL1/AllSky/{self.prod_id}/"
            f"{self.dataset_type}/{self.particle}/{self.dec}"
        )

    def _pointing_dirs(self):
        base = Path(self.base_dir)
        if not base.exists():
            raise FileNotFoundError(f"Input base not found: {base}")

        pointings = []
        for d in base.iterdir():
            if not d.is_dir():
                continue
            # Accept both flat and nested DL1 file layouts
            has_h5 = any(d.glob("*.h5")) or any(d.glob("*/*.h5"))
            if has_h5:
                pointings.append(d.name)

        if not pointings:
            raise RuntimeError(f"No node directories with .h5 found under {base}")

        return sorted(pointings)

    def _input_dir(self, pointing):
        return os.path.join(self.base_dir, pointing)

    def _output_file(self, pointing):
        return os.path.join(
            self.base_dir,
            f"dl1_{self.prod_id}_{self.particle}_test_{pointing}_merged.h5",
        )

    @property
    def merge_dl1(self):
        paths = []
        for pointing in self._pointing_dirs():
            # Keep the nested pattern used for all-sky GammaDiffuse and compatible layouts
            paths.append(
                {
                    "input": self._input_dir(pointing),
                    "output": self._output_file(pointing),
                    "options": "--pattern *.h5 --no-image",
                    "extra_slurm_options": {"partition": "long", "time": "06:00:00"},
                }
            )
        return paths


# Example with NSB from environment.
# Keep NSB as string to preserve trailing zeros (e.g. 0.50).
nsb_list = ["0.07", "0.14", "0.22", "0.38", "0.50"]

for nsb_tag in nsb_list:
    prod_id = f"20260722_v0.10.12_allsky_nsb_tuning_{nsb_tag}"

    cfg = PathConfigMergeTestingEveryNode(
        prod_id=prod_id,
        dec="dec_6166",       
        particle="GammaDiffuse",      
        dataset_type="TestingDataset",
    )

    paths = cfg.generate()
    print(f"NSB {nsb_tag}: merge_dl1 entries:", len(paths["merge_dl1"]))
    print("first entry:", paths["merge_dl1"][0] if paths["merge_dl1"] else "NONE")

    cfg.save_yml(f"lstmcpipe_merge_dl1_{prod_id}_dec_6166.yaml", overwrite=True)
