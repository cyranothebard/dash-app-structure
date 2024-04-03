import os
import shutil
import pandas as pd

def read_csv_files_and_move_to_archive(input_dir, archive_dir):
    """
    Read all CSV files from a directory into DataFrame and move those files to an archive directory.

    Args:
        input_dir (str): Directory containing CSV files.
        archive_dir (str): Directory where the CSV files will be archived.

    Returns:
        dict: Dictionary containing DataFrames with keys as file names.
        dict: Dictionary containing paths to the archived CSV files with keys as file names.
    """
    dataframes = {}
    archived_files = {}

    # Ensure that the archive directory exists
    os.makedirs(archive_dir, exist_ok=True)

    # Iterate through each file in the input directory
    for file_name in os.listdir(input_dir):
        if file_name.endswith('.csv'):
            file_path = os.path.join(input_dir, file_name)

            # Read CSV data into a DataFrame
            dataframe = pd.read_csv(file_path)
            dataframes[file_name] = dataframe

            # Move the CSV file to the archive directory
            archived_file_path = os.path.join(archive_dir, file_name)
            shutil.move(file_path, archived_file_path)
            archived_files[file_name] = archived_file_path

    return dataframes, archived_files