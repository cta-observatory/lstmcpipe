import json
import os

# Directory path
directory = '.'

# Iterate over all directories starting with 'NSB-'
for root, dirs, files in os.walk(directory):
    if root.startswith(os.path.join(directory, 'NSB-')):
        # Iterate over all JSON files in the directory
        for file in files:
            if file.endswith('.json'):
                file_path = os.path.join(root, file)

                # Open the JSON file
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Modify the 'n_estimators' values
                data['random_forest_energy_regressor_args']['n_estimators'] = 50
                data['random_forest_disp_regressor_args']['n_estimators'] = 50

               # Write the modified data back to the JSON file
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=4) 
