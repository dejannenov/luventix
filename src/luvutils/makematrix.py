# Start in a directory
# Must have a spreashett named sample-data.xls in the directory
# Look for all file sin the directory and all subdirectories that start with v_
# For each file find the corresponding samples ID in column-1 of the spreadsheet
# From column 2 in the spreadsheet get the disease name
# Produce martins matrix file with samples if in col1, disease name in col2, and healthy/disease flag in col3 - followed by the 28,350 columns of data
# if a sample ID exists in teh spreadsheet but the file cannot be found, then write the missing id to missing-files.txt
# if a file exists but there is no data for it in the spreadsheet, whtn write the missing id in missing-data.txt
# all steps are logged in file full-matrix.log, on windows use powershell with : "Get-Content full-matrix.log –Wait" to minitor
import collections
import json
import logging
import os
import re
import numpy as np
import chardet
import openpyxl
import sys
import pandas as pd
from datetime import datetime
import shutil

#########################################   Utiility Functions #########################################

def remove_prefix(text, prefix):
    """Removes the specified prefix from the beginning of a string.

    Args:
        text (str): The string to remove the prefix from.
        prefix (str): The prefix to remove.

    Returns:
        str: The modified string with the prefix removed, or the original string if the prefix was not found.
    """
    if text.startswith(prefix):
        return text[len(prefix):]
    else:
        return text


def find_files(directory, regex_pattern):
    """Finds all files in a directory (and subdirectories) that match a regular expression.

    Args:
        directory (str): The starting directory to search.
        regex_pattern (str): The regular expression pattern to match filenames against.

    Returns:
        list: A list of file paths that match the pattern.
    """
    matching_files = []
    pattern = re.compile(regex_pattern, flags=re.IGNORECASE)
    for root, _, files in os.walk(directory):
        for file in files:
            if re.search(pattern, file):
                matching_files.append(os.path.join(root, file))  # Full path
    return matching_files



def setup_logging(log_dir, log_filename):
    """Sets up logging.

    Args:
        log_dir (str): The directory where the log will be written.
        log_filename (str): The name of the log file.

    Returns:
        result (int): 0 on success, 1 on error
    """

    try:
        # Create a logs directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            filename=os.path.join(log_dir, log_filename),  # Log file path
            level=logging.INFO,  # Minimum log level to capture (INFO, DEBUG, WARNING, ERROR, CRITICAL)
            format="%(asctime)s - %(levelname)s - %(message)s",  # Log message format
            datefmt="%Y-%m-%d %H:%M:%S"  # Date/time format
        )
    except Exception as e:
        print(f"An error occurred when setting up logging: {e}")
    else:
        return 0
    finally:
        console_handler = logging.StreamHandler(sys.stdout)
        logging.getLogger().addHandler(console_handler)

    # Example logging
    #logging.info("Application started")
    #logging.warning("This is a warning message")
    #logging.error("An error occurred")


#########################################   Read data From Spreadsheet #########################################

def read_spreadsheet(spreadsheet_file_full_path, sample_ids_column_number_one_based,
                     sample_disease_group_name_column_number, healthy_sample_designator_column_number, sheet_name,
                     samples_disease_names_dict=None, samples_healthy_sample_designator_dict=None):

    # Load the workbook
    wb = openpyxl.load_workbook(spreadsheet_file_full_path, data_only=True)

    # Select the sheet you want to read from
    if sheet_name == "" :
        sheet_name = "Sheet1"
    sheet = wb[sheet_name]

    # Iterate through the rows
    for row in sheet.iter_rows():
        # Extract data from columns, skipping the first row of the spreadsheet
        if row[sample_ids_column_number_one_based].row > 1:
            sample_id = str(row[sample_ids_column_number_one_based].value)
            sample_id = sample_id.lower()
            sample_id = remove_prefix(sample_id, 'v_')  #the v_ is used by the lab sometimes

            disease_name = row[sample_disease_group_name_column_number].value
            healthy_sample_designator = row[healthy_sample_designator_column_number].value  # 0 for healthy 1 for disease

            samples_disease_names_dict[sample_id] = disease_name
            samples_healthy_sample_designator_dict[sample_id] = healthy_sample_designator

def sample_file_exists_in_set_of_full_file_paths(arr_of_full_file_paths, sample_id):
    #print(f'{sample_id} =========================================================== ')
    for item in arr_of_full_file_paths:
        #print(f"{sample_id} = {os.path.basename(item)} ? {left_trim_after_substring(right_trim_after_substring(os.path.basename(item),'.'),'v_')} ? {item}")

        the_filename = os.path.basename(item)
        the_filename_no_extension = right_trim_after_substring(the_filename,'.')
        the_sample_id_from_the_filename = left_trim_after_substring(the_filename_no_extension,'v_')
        #print(f"{the_filename_no_extension} = trimmed - {the_sample_id_from_the_filename}")
        if the_sample_id_from_the_filename == sample_id:
            #print('================Found One================)')
            return True
    return False

def left_trim_after_substring(text, substring):
    """Left trims a string after the first occurrence of a substring.

    Args:
        text (str): The string to trim.
        substring (str): The substring to trim after.

    Returns:
        str: The trimmed string or the original string if the substring is not found.
    """
    index = text.lower().find(substring.lower())
    if index != -1:  # Substring found
        return text[index + len(substring):]  # Trim from after the substring to the end
    else:  # Substring not found
        return text


def right_trim_after_substring(text, substring):
    """Right trims a string after the first occurrence of a substring.

    Args:
        text (str): The string to trim.
        substring (str): The substring to trim after.

    Returns:
        str: The trimmed string or the original string if the substring is not found.
    """
    index = text.lower().find(substring.lower())
    if index != -1:  # Substring found
        return text[:index]
    else:  # Substring not found
        return text


def data_for_sample_file_exists_in_spreadsheet(samples_disease_names_dict,full_path_to_file):
    the_filename = os.path.basename(full_path_to_file)
    the_filename_no_extension = right_trim_after_substring(the_filename,'.')
    the_sample_id_from_the_filename = left_trim_after_substring(the_filename_no_extension,'v_')
    #if the_sample_id_from_the_filename in samples_disease_names_dict:
    #    print(f"the_sample_id_from_the_filename={the_sample_id_from_the_filename} disease={samples_disease_names_dict[the_sample_id_from_the_filename]}")
    #else:
    #    print(f"not found: {the_sample_id_from_the_filename}")
    return the_sample_id_from_the_filename in samples_disease_names_dict

################################# find samples IDs for which we have data but no files ##############################
def find_missing_files(full_path_to_missing_files_file, samples_disease_names_dict, matching_files, bad_file_list):
    with open(full_path_to_missing_files_file, 'w') as outfile:
        for key in samples_disease_names_dict:
            #print(f"Element at index {index}: {element}")
            if (not sample_file_exists_in_set_of_full_file_paths(matching_files,key)) and (not key in bad_file_list):
                outfile.writelines('v_' + key + '.csv\n')


################################# find samples IDs for which we files but no data ##############################
def find_missing_data(full_path_to_missing_data_file, matching_files=None, samples_disease_names_dict=None):
    with open(full_path_to_missing_data_file, 'w') as outfile:
        for index, element in enumerate(matching_files):
            if not data_for_sample_file_exists_in_spreadsheet(samples_disease_names_dict,element):
                print(f"No data found for file {os.path.basename(element)}")
                outfile.writelines(os.path.basename(element) + '\n')

def remove_substring(text, substring):
    """Removes the first occurrence of a substring from a string.

    Args:
        text: The original string.
        substring: The substring to remove.

    Returns:
        The modified string with the substring removed,
        or the original string if the substring is not found.
    """

    index = text.find(substring)
    if index != -1:  # Substring found
        return text[:index] + text[index + len(substring):]
    else:
        return text

def remove_substring_re(text, substring, ignorecase):
    if ignorecase:
        return re.sub(re.escape(substring), "", text, flags=re.IGNORECASE)
    else:
        return re.sub(re.escape(substring), "", text)


def change_all_filenames_to_lowercase_and_cleanup_names(matching_files):
    for file_path in matching_files:
        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        new_filename = filename.lower()
        new_filename = remove_substring(new_filename,'(1)')
        new_filename = remove_substring_re(new_filename,'copy of', True)
        new_filename = remove_substring(new_filename,' - Copy')
        new_filename = new_filename.replace(' ','')

        #print(f"filename = {filename} new_filename={new_filename}")
        if filename != new_filename:
            new_file_path = os.path.join(directory, new_filename)
            os.rename(file_path, new_file_path)
            logging.info(f"Renamed file [{filename}] to [{new_filename}]")
    return

def write_dict_to_json_file(data, filename):
    """Writes a dictionary to a JSON file.

    Args:
        data (dict): The dictionary to be written.
        filename (str): The name of the file to write to.
    """
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)  # indent for pretty-printing (optional)

def fix_encoding_to_ascii(matching_files):
    file_counter = 0
    total_files = len(matching_files)
    for file_path in matching_files:
        # check the encoding on the file
        file_counter += 1
        with open(file_path, 'rb') as file:
            print(f'\rChecking encoding for file {os.path.basename(file_path)} [{file_counter} of {total_files}]'.ljust(120), end='')
            raw_data = file.read()
        # Use chardet for robust detection
        result = chardet.detect(raw_data)
        encoding = result['encoding']
        # Print with confidence level
        #print(f"{os.path.basename(file_path)} encoding: {encoding} (Confidence: {result['confidence']})")
        #print(f'\rEncoding file {os.path.basename(file_path)}', end='')
        #logging.debug(f"{os.path.basename(file_path)} encoding: {encoding} (Confidence: {result['confidence']})")
        if encoding == 'UTF-16':
            print(f"File {os.path.basename(file_path).ljust(120)} is UTF-16. Converting to ASCII.")
            with open(file_path, 'r', encoding='UTF-16') as file:
                data = file.read()
            with open(file_path, 'w', encoding='ASCII') as file:
                file.write(data)
    print()
    return
def generate_matrix(matching_files, output_filename, root_dir=None):
    data = []
    for file_path in matching_files:
        #print(os.path.basename(file_path))
        #print(file_path)
        with open(file_path, 'r') as infile:
            #data.append(np.loadtxt(infile, delimiter='\t', usecols=1))
            try:
                data.append(np.loadtxt(infile, delimiter='\t', usecols=1))
            except:
                print(f"error reading file:{file_path}")
                logging.info(f"error reading file:{file_path}")
           #print(np.array(data).shape)
        infile.close()
    np_data = np.array(data)
    np.savetxt(os.path.join(root_dir, output_filename), np_data, delimiter='\t', fmt='%.12f')

def generate_matrix2(matching_files, output_filename, root_dir, samples_disease_names_dict, samples_healthy_sample_designator_dict):
    data = pd.DataFrame()
    file_counter = 0
    total_files = len(matching_files)
    for file_path in matching_files:
        file_counter += 1
        print(f'\rReading data file {os.path.basename(file_path)} [{file_counter} of {total_files}]', end='')
        try:
            # read data directly into a dataframe
            #df = pd.read_csv(file_path, delimiter='\t', header=None)
            df = pd.read_csv(file_path, delimiter='\t', usecols=[1], header=None).transpose()
            # insert the value in the first column
            sample_id = get_sample_id_from_file_path(file_path, 'v_', '.csv')

            if not sample_id in samples_healthy_sample_designator_dict:
                samples_healthy_sample_designator_dict[sample_id] = -1
            df.insert(0, 'healthyFlag', samples_healthy_sample_designator_dict[sample_id])

            if not sample_id in samples_disease_names_dict:
                samples_disease_names_dict[sample_id] = 'NA'
            df.insert(0, 'condition', samples_disease_names_dict[sample_id])

            df.insert(0, 'sampleID', sample_id)
            # append to the main dataframe
            data = pd.concat([data,df], ignore_index=True)
        except Exception as e:
            print(f"error reading file:{file_path}")
            logging.exception(f"error reading file:{file_path}")

    # sort the data frame by condition
    data = data.sort_values(by='condition')
    # Save the dataframe as a tab-separated csv file
    print()
    print(f'Writing matrix data file')
    data.to_csv(os.path.join(root_dir, output_filename), sep='\t', float_format='%.13f', index=False)

def get_sample_id_from_file_path(file_path, prefix, file_extension):
    filename = os.path.basename(file_path)
    sample_id = left_trim_after_substring(filename,prefix)
    sample_id = right_trim_after_substring(sample_id, file_extension)
    return sample_id


def check_file_for_bad_data(matching_files, expected_cols, expected_rows, expected_separator, root_dir, bad_files_filename):
    if matching_files is None or len(matching_files) == 0:
        raise ValueError("matching_files cannot be null or empty")

    if expected_cols is None or expected_cols < 1:
        raise ValueError("expected_cols cannot be null or less than 1")

    if expected_rows is None or expected_rows < 1:
        raise ValueError("expected_rows cannot be null or less than 1")

    if expected_separator is None or expected_separator == "":
        raise ValueError("expected_separator cannot be null or empty")

    if root_dir is None or root_dir == "":
        raise ValueError("root_dir cannot be null or empty")

    if bad_files_filename is None or bad_files_filename == "":
        raise ValueError("bad_files_filename cannot be null or empty")

    bad_files = []
    file_counter = 0
    total_files = len(matching_files)
    for file_path in matching_files:
        file_counter += 1
        print(f'\rChecking for data shape, file {os.path.basename(file_path)} [{file_counter} of {total_files}]', end='')

        with open(file_path, 'r') as file:
            line_count = sum(1 for _ in file)  # Efficient line counting
            if line_count != expected_rows:
                bad_files.append(file_path)
                #print(f"\nFile '{file_path}' has {line_count} lines. Expected {expected_rows}.")
                logging.info(f"File '{file_path}' has {line_count} lines. Expected {expected_rows}.")
                file.close()
                #os.rename(file_path, file_path + ".rowcount.bad")

                try:
                    source_file = file_path
                    destination_file = os.path.join(root_dir, bad_files_filename)
                    shutil.copy2(source_file, destination_file)
                    print(f"File copied successfully from '{source_file}' to '{destination_file}'")
                except FileNotFoundError:
                    print(f"Error: Source file '{source_file}' not found.")
                except PermissionError:
                    print(f"Error: Permission denied to write to '{destination_file}'.")
                except Exception as e:
                    print(f"An unexpected error occurred: {e}")

                continue

        field_counts_ok = True
        with open(file_path, 'r') as file:
            #print(f"Looking for field count = {expected_cols} in file {file}")
            line_number = 0
            for line in file:
                line_number += 1
                #print(f'\rChecking line {line_number} of {expected_rows}'.ljust(120), end='')
                fields = line.strip().split(expected_separator)
                field_counts = len(fields)
                if field_counts != expected_cols:
                    field_counts_ok = False
                    bad_files.append(file_path)
                    #print()
                    #print(f"File '{file_path}' has {field_counts} fields on line {line_number}. Expected {expected_cols}.")
                    logging.info(f"File '{file_path}' has {field_counts} fields on line {line_number}. Expected {expected_cols}.")

        if not field_counts_ok:
            file.close()
            os.rename(file_path, file_path + ".colcount.bad")


    print()

    with open(os.path.join(root_dir, bad_files_filename), 'w') as file:
        for item in bad_files:
            file.write("%s\n" % item)

    logging.info(f"Wrote a list of {len(bad_files)} files with bad (not conforming to shape data)  to {bad_files_filename}")


def update_bad_files_list_from_renamed_bad_files(bad_files_filename,root_dir):
    pattern_str = r".*\.(bad)$"
    bad_matching_files = find_files(root_dir, pattern_str)

    if bad_files_filename is None:
        raise ValueError("bad_files_filename cannot be null")

    if root_dir is None:
        raise ValueError("root_dir cannot be null")

    if bad_matching_files is None:
        raise ValueError("bad_matching_files cannot be null")

    with open(os.path.join(root_dir, bad_files_filename), 'a') as file:
        for file_path in bad_matching_files:  # bad_files in file:
            file.write("%s\n" % file_path)

    return bad_matching_files


    ################################# main ##############################
# use full paths to all files

def main():


#root_dir = "G:\\DejanFiles\\Active Projects\\Vetabolics\\Master Tracking Spreadsheet, Data Files and Results"
    #root_dir = "G:\\DejanFiles\\Active Projects\\Vetabolics\\fileprep"
    root_dir = "C:\\git-repos\\2024-first-model\\gc_data\\blinds\\20241122-HSA-Blind-Rerun-of-20241101"
    root_dir = r"C:\Users\dejan\Documents\luventix\OneDrive - Luventix Inc\Documents - Exec\Product Development\2024\Trials\Observational\Data\Raw Data - All Files\20250509 Luventix CRC Blinds"
    print(f"root_dir={root_dir}")


    log_file = timestamp_prefix + "-full-matrix.log"
    spreadsheet_file = "sample-data.xlsx"
    bad_files_filename = timestamp_prefix + "-bad-files.txt"

    file_extensions_of_files_with_data = "csv" #can be "csv|tsv|txt"
    filename_start_string = ""
    #filename_start_string = "V_"
    missing_files_filename = timestamp_prefix + "-missing-files.txt"
    missing_data_filename = timestamp_prefix + "-missing-data.txt"
    output_filename = timestamp_prefix + "-descMatrixV3.tsv"

    samples_disease_names_dict = {}
    samples_healthy_sample_designator_dict = {}
    matching_files=[]

    #====================  SETUP LOGGING ========================================#
    setup_logging(root_dir, log_file)
    logging.info("Application started & log file opened. win powershell: `Get-Content full-matrix.log –Wait`")
    logging.info(f"root_dir={root_dir}")

    #====================  READ THE SPREADSHEET ========================================#
    spreadsheet_file_full_path = os.path.join(root_dir, spreadsheet_file)
    logging.info("Opening spreadsheet " + spreadsheet_file_full_path)

    read_spreadsheet(spreadsheet_file_full_path, 0, 1,
                     2, "", samples_disease_names_dict, samples_healthy_sample_designator_dict)
    logging.info("Spreadsheet Read.")

    ###############################  set regex file pattern ############################
    pattern_str = r".*"+filename_start_string + ".*\\.(" + file_extensions_of_files_with_data +")$"
    logging.info(f"Searching for files that match re pattern = {pattern_str }")
    logging.info(f"The regex finds files that have {filename_start_string} somewhere in the name and "
                    + f"end with one of these extensions: {file_extensions_of_files_with_data}")

    matching_files = find_files(root_dir, pattern_str)
    logging.info("Found " + str(len(matching_files)) +" files")


    logging.info("Renaming files to lowercase and cleanining up `(1)` and `copy of` in names.")
    change_all_filenames_to_lowercase_and_cleanup_names(matching_files)
    logging.info("Changed all filenames to lowercase and cleaned-up names.")

    logging.info(f"Searching for files that match re pattern = {pattern_str }")
    matching_files = find_files(root_dir, pattern_str)
    logging.info("Found " + str(len(matching_files)) +" files")
    #print(matching_files)

    logging.info("Checking file encoding.")
    fix_encoding_to_ascii(matching_files)
    logging.info("All files encoded to ASCII.")

    ##################### check data quiality for each file ############################
    expected_cols = 2
    expected_rows = 38250
    logging.info(f"Checking each file for {expected_cols} columns and {expected_rows} rows.")
    check_file_for_bad_data(matching_files,expected_cols,expected_rows,'\t', root_dir, bad_files_filename)
    logging.info("Checked Files for bad data")


    ##################### make sure that multiple passes produce the same bad-file.txte ############################
    logging.info("Updating bad-files.txt from previously flagged (renamed .bad) files.")
    bad_filepaths_list = update_bad_files_list_from_renamed_bad_files(bad_files_filename,root_dir)
    bad_file_list = []
    for file_path in bad_filepaths_list:
        bad_file_list.append(get_sample_id_from_file_path(file_path, 'v_','.csv'))
    print (bad_file_list)
    logging.info("Done updating bad-files.txt.")


    #############  Now we will use only the files that have good data ################
    matching_files = find_files(root_dir, pattern_str)
    logging.info("Found " + str(len(matching_files)) +" GOOD DATA files")

    count_of_files_found = len(matching_files)
    matching_files = list(dict.fromkeys(matching_files)) #this removes duplicates form the list
    count_of_unique_files_found = len(matching_files)
    duplicates_count = count_of_files_found - count_of_unique_files_found
    logging.info("Found " + str(count_of_unique_files_found) + " unique files and ["
                 + str(duplicates_count) +"] duplicates")

    logging.info("Checking for missing files. Data in the spreadsheet and corresponding file found.")
    find_missing_files(os.path.join(root_dir, missing_files_filename),samples_disease_names_dict,matching_files, bad_file_list)
    logging.info("Checked for missing files. Wrote missing-files.txt")

    logging.info("Checking for missing data. Files found that don't have data in the spreadsheet.")
    find_missing_data(os.path.join(root_dir, missing_data_filename),matching_files,samples_disease_names_dict)
    logging.info("Checked for missing data. Wrote missing-data.txt")

    #generate_matrix(matching_files, output_filename, root_dir)
    logging.info(f"Start generating matrix file {output_filename}")
    generate_matrix2(matching_files, output_filename, root_dir, samples_disease_names_dict, samples_healthy_sample_designator_dict)
    logging.info(f"Generated matrix file {output_filename}")
    logging.info(f"===================== END ========================\n")

if __name__ == '__main__':
    # Get the current date and time and Format it into the desired string
    timestamp_prefix = datetime.now().strftime('%Y%m%d%H%M')
    main()
