from pathlib import Path
from ruamel.yaml import YAML
import json


def codemeta2citation(codemeta_path='codemeta.json', citation_path='CITATION.cff'):
    codemeta = json.load(open(codemeta_path))
    citation = {'title': codemeta['name'],
                'type': 'software',
                'authors': [],
                'message': 'If you use this software, please cite it using Zenodo from https://doi.org/10.5281/zenodo.6460727',
                'license': 'MIT',
                }
    for author in codemeta['author']:
        citation['authors'].append({
            'family-names': author['familyName'],
            'given-names': author['givenName'],
            'orcid': author['@id'],
            'email': author['email']
        }
        )

    yaml = YAML()
    yaml.dump(citation, open(citation_path, 'w'))


if __name__ == '__main__':
    codemeta_path = Path(__file__).parents[3].joinpath('codemeta.json')
    citation_path = Path(__file__).parents[3].joinpath('CITATION.cff')
    codemeta2citation(codemeta_path, citation_path)
