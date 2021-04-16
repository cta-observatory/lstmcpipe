# DL1 to DL2 onsite (La Palma cluster)


import argparse
import calendar
import lstchain
from lstchain.io.data_management import *


parser = argparse.ArgumentParser(description="MC R0 to DL1")


parser.add_argument('input_dir', type=str,
                    help='path to the files directory to analyse',
                   )

parser.add_argument('path_models', action='store', type=str,
                    help='path to the trained models',
                    )

parser.add_argument('--config_file', '-conf', action='store', type=str,
                    dest='config_file',
                    help='Path to a configuration file. If none is given, a standard configuration is applied',
                    default=None
                    )

today = calendar.datetime.date.today()
default_prod_id = f'{today.year:04d}{today.month:02d}{today.day:02d}_v{lstchain.__version__}_v00'

parser.add_argument('--prod_id', action='store', type=str,
                    dest='prod_id',
                    help="Production ID",
                    default=default_prod_id,
                   )

args = parser.parse_args()


def main():

    input_dir = args.input_dir
    output_dir = input_dir.replace('DL1', 'DL2')
    output_dir = os.path.join(output_dir, args.prod_id)
    
    job_logs = os.path.join(output_dir, 'JOB_LOGS')
    
    check_and_make_dir(output_dir)
    check_and_make_dir(job_logs)

    print(f"Output dir: {output_dir}")

#     file_list = [os.path.join(input_dir, f) for f in os.listdir(args.input_dir) if f.startswith('dl1_')]
    file_list = [os.path.join(input_dir, f) for f in os.listdir(args.input_dir)]

    query_continue(f"{len(file_list)} jobs,  ok?")

    for ii, file in enumerate(file_list):
        base_cmd = 'conda activate cta; '
        base_cmd += f'lstchain_mc_dl1_to_dl2 -f {file} -p {args.path_models} -o {output_dir}'
        if args.config_file is not None:
            base_cmd += f' -conf {args.config_file}'
        jobe = os.path.join(job_logs, f'job{ii}.e')
        jobo = os.path.join(job_logs, f'job{ii}.o')

        cmd = f'sbatch -e {jobe} -o {jobo} --wrap "{base_cmd}"' 
        # print(cmd)
        os.system(cmd)


if __name__ == '__main__':
    main()
