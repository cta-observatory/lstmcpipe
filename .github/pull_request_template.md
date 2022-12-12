<!---  
You may leave this message, it will be commented out in your PR.
- if you are requesting a new config to be processed, please use the New Prod Config template
- if you are proposing changes to lstmcpipe library delete the template and describe your PR as usual
--->

<!---  
New Prod Config template
Add Prod_ID and fill the template
Your Pull Request must include the following files placed in directory `production_configs/prod_id`:
- lstmcpipe config file
- lstchain config
- readme.md

Add label `new_prod_config`
---> 

# New Prod config

Self check-list:

- [ ] I have checked the lstchain config, in particular for:
  - [ ] `az_tel` instead of `sin_az_tel` if data to be analyzed have been produced with lstchain <= v0.9.7
  - [ ] "increase_nsb" and "increase_psf" are provided in "image_modifier" (if used)
- [ ] I have checked the environment in the lstmcpipe config and it is the one used to analyse DL>1 data
- [ ] I have provided the command (in README), or script (in additionnal .py file) used to produce the lstmcpipe config

## Prod_ID

## Short description of the config

## Why this config is needed 
