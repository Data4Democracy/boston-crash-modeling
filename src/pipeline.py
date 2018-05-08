import argparse
import yaml
import os
import subprocess

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)))


def data_transformation(config, DATA_FP, forceupdate=False):
    """
    Transform data from a csv file into standardized crashes and concerns
    according to a config file
    Args:
        config
        DATA_FP - data directory for this city
    """
    # transform data, if the standardized files don't exist
    # or forceupdate
    if not os.path.exists(os.path.join(
            DATA_FP, 'standardized', 'crashes.json')) or forceupdate:
        subprocess.check_call([
            'python',
            '-m',
            'data_transformation.transform_crashes',
            '-d',
            config['name'],
            '-f',
            DATA_FP
        ])
    else:
        print "Already transformed crash data, skipping"

    # There has to be concern data in the config file to try processing it
    if ('concern_files' in config.keys()
        and config['concern_files'] and not os.path.exists(os.path.join(
            DATA_FP, 'standardized', 'concerns.json'))) or forceupdate:
        subprocess.check_call([
            'python',
            '-m',
            'data_transformation.transform_concerns',
            '-d',
            config['name'],
            '-f',
            DATA_FP
        ])
    else:
        if 'concern_files' not in config.keys() or not config['concern_files']:
            print "No concerns defined in config file"
        elif not forceupdate:
            print "Already transformed concern data, skipping"


def data_generation(config_file, DATA_FP, start_year=None, end_year=None,
                    forceupdate=False):
    subprocess.check_call([
        'python',
        '-m',
        'data.make_dataset_osm',
        '-c',
        config_file,
        '-d',
        DATA_FP
    ]
        + (['-s', str(start_year)] if start_year else [])
        + (['-e', str(end_year)] if end_year else [])
    )


def train_model(config_file, DATA_FP):
    subprocess.check_call([
        'python',
        '-m',
        'models.train_model',
        '-c',
        config_file,
        '-d',
        DATA_FP
    ])

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config_file", type=str,
                        help="config file location")
    parser.add_argument('--forceupdate', action='store_true',
                        help='Whether to force update the maps')
    # Can also choose which steps of the process to run
    parser.add_argument('--onlysteps',
                        help="Give list of steps to run, as comma-separated " +
                        "string.  Has to be among 'transformation'," +
                        "'generation', 'model', 'visualization'")

    args = parser.parse_args()
    if args.onlysteps:
        steps = args.onlysteps.split(',')

    # Read config file
    with open(args.config_file) as f:
        config = yaml.safe_load(f)

    DATA_FP = os.path.join(BASE_DIR, 'data', config['name'])

    if not args.onlysteps or 'transformation' in args.onlysteps:
        data_transformation(config, DATA_FP, forceupdate=args.forceupdate)

    start_year = config['start_year']
    if start_year:
        start_year = '01/01/{} 00:00:00Z'.format(start_year)
    end_year = config['end_year']
    if end_year:
        end_year = '01/01/{} 00:00:00Z'.format(end_year)
    if not args.onlysteps or 'generation' in args.onlysteps:
        data_generation(args.config_file, DATA_FP,
                        start_year=start_year,
                        end_year=end_year,
                        forceupdate=args.forceupdate)

    if not args.onlysteps or 'model' in args.onlysteps:
        train_model(args.config_file, DATA_FP)

    # risk map
    # visualize

