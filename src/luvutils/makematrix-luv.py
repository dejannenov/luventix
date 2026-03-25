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
import csv

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

def read_spreadsheet(spreadsheet_file_full_path, sample_ids_column_number,
                     sample_disease_group_name_column_number, healthy_sample_designator_column_number, sheet_name,
                     samples_disease_names_dict=None, samples_healthy_sample_designator_dict=None):

    # Load the workbook
    wb = openpyxl.load_workbook(spreadsheet_file_full_path, data_only=True)

    # Select the sheet you want to read from
    if sheet_name == "" :
        sheet_name = "Master"
    sheet = wb[sheet_name]

    # Iterate through the rows
    for row in sheet.iter_rows():
        # Extract data from columns, skipping the first row of the spreadsheet
        if row[sample_ids_column_number].row > 1:
            sample_id = str(row[sample_ids_column_number].value)
            sample_id = sample_id.lower().strip()

            sample_id = remove_prefix(sample_id, 'v_')  #the v_ is used by the lab sometimes

            disease_name = str(row[sample_disease_group_name_column_number].value)
            healthy_sample_designator = row[healthy_sample_designator_column_number].value  # 0 for healthy 1 for disease

            samples_disease_names_dict[sample_id] = disease_name
            samples_healthy_sample_designator_dict[sample_id] = healthy_sample_designator

    print(samples_disease_names_dict)
    print(samples_healthy_sample_designator_dict)

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

def generate_matrix2(matching_files, output_filename, root_dir, samples_disease_names_dict, samples_healthy_sample_designator_dict,isolate_standards=True):
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
            sample_id = get_sample_id_from_file_path(file_path, '', '.tsv')
            print(f'\rAdding data to matrix for sample_id = {sample_id}', end='')

            if not sample_id in samples_healthy_sample_designator_dict:
                samples_healthy_sample_designator_dict[sample_id] = -1
            df.insert(0, 'diseasePresentFlag', samples_healthy_sample_designator_dict[sample_id])

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
    # Save the dataframe as a tab-separated  file
    print()
    print(f'Writing matrix data file')
    #convert everything to integers
    num_columns_in_data_frame = data.shape[1]
    #data = data.astype(int)
    #data.iloc[:, 3:num_columns_in_data_frame+1] = data.iloc[:, 3:num_columns_in_data_frame+1].astype(int)
    #data.to_csv(os.path.join(root_dir, output_filename), sep='\t', float_format='%.13f', index=False)
    data.to_csv(os.path.join(root_dir, output_filename), sep='\t', index=False)



    if isolate_standards:
        print(f'Writing matrix data file for standards only')
        # we sample at 50Hz
        # first standard is Isoprpopyl Acetate  C₅H₁₀O₂ at 20ppm expected peak at 3.31 minutes
        # second standard is  Methyl Anthraniliate C₈H₉NO₂. 20ppm expected peak at 10.815 minutes
        # we will retain the data in two windows of 5 seconds before and after the expected peaks
        # window one centered at 3.31 minutes * 60 seconds * 50 samples / second = 9,930 data point
        # window two centered at 10.81 minutes * 60 seconds * 50 samples / second = 32,430 data point
        # number of samples in 5 seconds = 5 * 50 hz = 250 samples
        # window 1 is from (9930 - 250) to (9930 + 250) = 9680 to 10130
        # window 2 is from (32430 - 250) to (32430 + 250) = 32180 to 32680

        # we have three extra columns at the start - sample ID, condition, diseasePresentFlag, so we offset by +3
        # drop data between 3 and 9683
        # drop data between 9684 and 32183
        # drop data between 32683 and num_columns_in_data_frame

        # Remove columns from index start_col to end_col (inclusive of start_col, exclusive of end_col)

        #data = data.drop(data.columns[3:9682], axis=1)
        #data = data.drop(data.columns[10133:32183], axis=1)
        #data = data.drop(data.columns[32683:num_columns_in_data_frame+1], axis=1)

        num_columns_in_data_frame = data.shape[1]
        # Create a list of all column indices to drop
        cols_to_drop = list(range(3, 9682)) + list(range(10133, 32183)) + list(range(32683, num_columns_in_data_frame))
        data = data.drop(data.columns[cols_to_drop], axis=1)


        #now drop the last column as well
        #data_standards = data_standards.drop(data_standards.columns[9680], axis=1)


        data.to_csv(os.path.join(root_dir, 'standards_' + output_filename), sep='\t', index=False)
        print(f'Writing matrix data file in .csv format for standards only')
        data.to_csv(os.path.join(root_dir, output_filename+".csv"), sep=',', index=False)

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

def replace_character_in_files(matching_files, old_char: str, new_char: str):
    """
    Replaces every occurrence of a specified character with another character in the input file.

    :param input_file: The path to the input text file.
    :param output_file: The path to the output text file.
    :param old_char: The character to be replaced.
    :param new_char: The character to replace with.
    """
    file_counter = 0
    total_files = len(matching_files)
    for file_path in matching_files:
        file_counter += 1
        print(f'\rReplaced characters in file {os.path.basename(file_path)} [{file_counter} of {total_files}]', end='')
        with open(file_path, 'r') as infile:
            # Read the entire content of the file
            content = infile.read()

        # Replace all occurrences of old_char with new_char
        modified_content = content.replace(old_char, new_char)

        # Write the modified content to the output file
        with open(file_path, 'w') as outfile:
            outfile.write(modified_content)

def remove_rows(matching_files, ranges: list):
    """
    Removes rows in specified ranges from a text file.

    :param input_file: The path to the input file to read.
    :param output_file: The path to the output file to write.
    :param ranges: A list of tuples, where each tuple (m, n) represents a row range to remove.
    """
    file_counter = 0
    total_files = len(matching_files)
    for file_path in matching_files:
        file_counter += 1
        print(f'\rRemoving unwanted rows, file {os.path.basename(file_path)} [{file_counter} of {total_files}]', end='')
        with open(file_path, 'r') as infile:
            # Read all lines from the input file
            lines = infile.readlines()

        # Filter out lines within the specified ranges
        result_lines = [
            line for idx, line in enumerate(lines, start=1)
            if not any(m <= idx <= n for m, n in ranges)
        ]

        # Write the remaining lines to the output file
        with open(replace_file_extension(file_path, ".tsv"), 'w') as outfile:
            outfile.writelines(result_lines)

# Example usage:
# remove_rows('input.txt', 'output.txt', [(5, 10), (15, 20)])

def replace_file_extension(file_path: str, new_extension: str) -> str:
    """
    Replaces the last file extension of the given file path, allowing for file names with multiple periods.

    :param file_path: The full path of the file.
    :param new_extension: The new file extension, e.g., '.txt'.
    :return: The file path with the replaced extension.
    """
    # Ensure new_extension starts with a dot
    if not new_extension.startswith('.'):
        new_extension = '.' + new_extension

    # Separate the directory, base filename, and final extension
    directory, filename = os.path.split(file_path)
    base_name, _ = filename.rsplit('.', 1)

    # Construct the new file path
    new_file_path = os.path.join(directory, base_name + new_extension)
    return new_file_path



def remove_columns(matching_files, columns_to_remove: list):
    """
    Removes specified columns from a tab-separated text file.

    :param input_file: The path to the input file.
    :param output_file: The path to the output file.
    :param columns_to_remove: A list of column indices to remove (0-based).
    """
    file_counter = 0
    total_files = len(matching_files)
    for file_path in matching_files:
        temp_file_path = file_path + '.tmp'
        file_counter += 1
        print(f'\rRemoving columns, file {os.path.basename(file_path)} [{file_counter} of {total_files}]', end='')
        with open(file_path, 'r') as infile, open(temp_file_path, 'w', newline='') as tempfile:
            reader = csv.reader(infile, delimiter='\t')
            writer = csv.writer(tempfile, delimiter='\t')

            for row in reader:
                # Remove the specified columns from each row
                new_row = [value for index, value in enumerate(row) if index not in columns_to_remove]
                writer.writerow(new_row)

        # Replace the original file with the modified file
        os.replace(temp_file_path, file_path)

# Example usage:
# remove_columns('input.tsv', 'output.tsv', [1, 3])  # Removes the 2nd and 4th columns (0-based index)

def main():


#root_dir = "G:\\DejanFiles\\Active Projects\\Vetabolics\\Master Tracking Spreadsheet, Data Files and Results"
    #root_dir = "G:\\DejanFiles\\Active Projects\\Vetabolics\\fileprep"
    #root_dir = "C:/Users/dejan/Documents/luventix/OneDrive - Luventix Inc/Documents - Exec/Product Development/2024/Trials/Observational/Data/Raw Data - All Files/Full Full Data Set"
    #root_dir = "C:/Users/dejan/Documents/luventix/OneDrive - Luventix Inc/Documents - Exec/Product Development/2024/Trials/Observational/Data/Raw Data - All Files/20250320 SIBO 200-200"
    root_dir = r"C:\Users\dejan\Documents\luventix\OneDrive - Luventix Inc\Documents - Exec\Product Development\2024\Trials\Observational\Data\Raw Data - All Files\Full Full Data Set"

    print(f"root_dir={root_dir}")


    log_file = timestamp_prefix + "-matrix.log"
    #spreadsheet_file = "C:/Users/dejan/Documents/luventix/OneDrive - Luventix Inc/Documents - Exec/Product Development/2024/Trials/Observational/Data/2024 Luventix Observational Study Master Sample List.xlsx"
    spreadsheet_file = "C:/Users/dejan/Documents/luventix/OneDrive - Luventix Inc/Documents - Exec/Product Development/2024/Trials/Observational/Data/Raw Data - All Files/Full Full Data Set/2024 Luventix Observational Study Master Sample List Neg-Pos per Disease.xlsx"
    bad_files_filename = timestamp_prefix + "-bad-files.txt"

    file_extensions_of_files_with_data = "csv" #can be "csv|tsv|txt"
    filename_start_string = ""
    #filename_start_string = "V_"
    missing_files_filename = timestamp_prefix + "-missing-files.txt"
    missing_data_filename = timestamp_prefix + "-missing-data.txt"
    output_filename = timestamp_prefix + "-luv-descMatrixV3.tsv"

    samples_disease_names_dict = {}
    samples_healthy_sample_designator_dict = {}
    #matching_files=[]

    #====================  SETUP LOGGING ========================================#
    setup_logging(root_dir, log_file)
    logging.info("Application started & log file opened. win powershell: `Get-Content full-matrix.log –Wait`")
    logging.info(f"root_dir={root_dir}")


    # if we have already generated the cleaned-up .tsv files - go directly to generating the matrix
    only_generate_matrix = False

    if only_generate_matrix:
        logging.info(f"NO FILE PRE-PROCESSING NEEDED. We are going directly to generating the matrix.")
    else:
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

        ##################### remove uwanted rows - keep 38,250 rows - and rename the files to .tsv############################
        remove_rows(matching_files, [(1, 2), (38253, 114756)] )
        logging.info("Removed two unwanted header rows from " + str(len(matching_files)) +" files")

        # the new extension is tsv
        pattern_str = r".*"+filename_start_string + ".*\\.(" + 'tsv' + ")$"
        matching_files = find_files(root_dir, pattern_str)

        ##################### replace all commas with TABs ############################
        replace_character_in_files(matching_files,",","\t")
        logging.info("Replaced commas with TABs " + str(len(matching_files)) +" files")

        ##################### remove the second columns ############################
        remove_columns(matching_files, [1])
        logging.info("Removed the second column from " + str(len(matching_files)) +" files")

        logging.info("Checking file encoding.")
        fix_encoding_to_ascii(matching_files)
        logging.info("All files encoded to ASCII.")

        ##################### check data quality for each file ############################
        expected_cols = 2
        expected_rows = 38250
        logging.info(f"Checking each file for {expected_cols} columns and {expected_rows} rows.")
        check_file_for_bad_data(matching_files,expected_cols,expected_rows,'\t', root_dir, bad_files_filename)
        logging.info("Checked Files for bad data")


        ##################### make sure that multiple passes produce the same bad-file.txt ############################
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
        matching_files = list(dict.fromkeys(matching_files)) #this removes duplicates from the list
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
    isolate_standards = True
    pattern_str = r".*"+filename_start_string + ".*\\.(" + 'tsv' + ")$"
    matching_files = find_files(root_dir, pattern_str)
    generate_matrix2(matching_files, output_filename, root_dir, samples_disease_names_dict, samples_healthy_sample_designator_dict, isolate_standards)
    logging.info(f"Generated matrix file {output_filename}")
    logging.info(f"===================== END ========================\n")

if __name__ == '__main__':
    # Get the current date and time and Format it into the desired string
    timestamp_prefix = datetime.now().strftime('%Y%m%d%H%M')
    main()
