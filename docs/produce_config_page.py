from pathlib import Path
import yaml
import git
from tabulate import tabulate


def load_config(filename):
    with open(filename, 'r') as f:
        return yaml.safe_load(f)


def add_prod_table(
    production_dir,
    prod_file='productions.rst',
    lstmcpipe_repo_prod_config_url='https://github.com/cta-observatory/lstmcpipe/tree/master/production_configs/',
):
    """

    Parameters
    ----------
    production_dir: pathlib.Path or str
        path to the production configs directory
    prod_file: str
        RST prod file to update
    lstmcpipe_repo_prod_config_url: str
    """

    prod_txt = '\n'

    commit_times = []
    prod_list = []
    for prod_dir in [d for d in Path(production_dir).iterdir() if d.is_dir()]:
        commit = list(git.Repo(root_dir).iter_commits(paths=prod_dir, max_count=1))[0]

        yml_list = [f for f in prod_dir.iterdir() if f.name.endswith('.yml') or f.name.endswith('.yaml')]
        if yml_list:
            try:
                conf = load_config(yml_list[0])
                prod_id = conf['prod_id']
            except:  # noqa
                print(f"Could not load prod id for {prod_dir.name}")
                prod_id = ''
        else:
            print(f"No yml file in {prod_dir}")

        markdowns = list(prod_dir.glob('*.md'))
        readme = open(markdowns[0]).read() if markdowns else ""
        prod_list.append(
            [
                commit.authored_datetime.date(),
                f"`{prod_dir.name} <{lstmcpipe_repo_prod_config_url+prod_dir.name}>`_",
                prod_id,
                readme,
            ]
        )
        commit_times.append(commit.authored_datetime)

    sorted_lists = sorted(zip(commit_times, prod_list))
    prod_list = [prod for _, prod in sorted_lists]

    prod_list.reverse()  # Reverse the ordering to have the most recent first

    prod_txt += tabulate(prod_list, ['Request date', 'Directory name', 'Prod ID', 'readme'], tablefmt='rst')

    with open(prod_file, 'a') as f:
        f.write(prod_txt)


if __name__ == '__main__':
    root_dir = Path(__file__).parent.joinpath('..').resolve()
    prod_dir = root_dir.joinpath('production_configs')

    add_prod_table(prod_dir)
