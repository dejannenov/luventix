import argparse
import configparser


# import sys

def load_config(file_path):
    config = configparser.ConfigParser()
    config.read(file_path)
    return config


def parse_arguments():
    parser = argparse.ArgumentParser(description="Luventix File Utilities")

    parser.add_argument('--dir', default='.', type=str, help="Full path to the directory where to start \
        searching for files. Default is the current directory `.`", required=False)
    parser.add_argument('--xls', default='./samples.xlsx', type=str, help="Full path to the spreadsheet \
        that contains the list of files to search for. Default is `./samples.xlsx`.", required=False)
    parser.add_argument('--output_filename', type=str, default='dataOut.tsv',
        help="Optional full path to output file. Default is `./dataOut.tsv`", required=False)
    parser.add_argument('--log_filename', type=str,
        help="Optional full path to the log file. Default is `./luvutils.log`", required=False)
    parser.add_argument('--missing_files_filename', type=str, default='missing_files.txt',
        help="Optional full path to the file that contains a list of missing files. Default is `./missing_files.txt`",
                        required=False)

    parser.add_argument('--config', type=str, default='./luvConfig.ini', help="Path to optional configuration file. \
        Command line parameters override configuration file settings", required=False)

    # Parse known arguments first to check for the config file
    args, unknown = parser.parse_known_args()

    # If config file is specified, load the config file
    if args.config:
        config = load_config(args.config)
        if 'DEFAULT' in config:
            default_config = config['DEFAULT']
            # Add defaults from config file if they are not already set by command line arguments
            for key, value in default_config.items():
                if not getattr(args, key, None):
                    setattr(args, key, value)

    # Reparse all arguments with possible defaults from config file
    args = parser.parse_args()

    return args


def main():
    args = parse_arguments()

    print(args)
    #print(f"Required Argument: {args.required_arg}")
    #print(f"Optional Argument: {args.optional_arg}")


if __name__ == "__main__":
    main()
