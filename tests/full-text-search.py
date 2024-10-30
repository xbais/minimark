import subprocess
import os
from tqdm import tqdm

def safe_decode(byte_data):
    """Safely decode bytes to a string, using 'utf-8' with error handling."""
    try:
        return byte_data.decode('utf-8')
    except UnicodeDecodeError:
        # If an error occurs, decode using 'latin-1' as fallback or ignore errors.
        return byte_data.decode('latin-1', errors='ignore')
        
def search_with_ripgrep(directory, keyword):
    try:
        # Use 'ripgrep' to enumerate files recursively in the directory.
        # This command will list all files and directories without executing the search initially.
        print('Getting files')
        result = subprocess.run(['rg', '-l', keyword, directory], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print('decoding the output')
        # Decode output and split into lines
        files = result.stdout.decode('utf-8').strip().split('\n')
        print('filtering files')
        # Filter out any empty strings from the list of files
        files = [f for f in files if f]
        
        # If no files are found, return
        if not files:
            print("No files matched the specified keyword.")
            return
        print('searching keyword in files')
        # Create a tqdm progress bar
        with tqdm(total=len(files), desc="Searching files", unit="file") as pbar:
            for file in files:
                print('==> File : ', file)
                # Print out the results for matched lines in each file
                search_result = subprocess.run(['rg', keyword, file], stdout=subprocess.PIPE)
                if search_result.stdout:
                    print(safe_decode(search_result.stdout).strip()) # .decode('utf-8')
                
                pbar.update(1)  # Update progress bar by one file
                print('---\n\n')
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    # Set the directory and keyword
    folder_path = input("Enter the folder path: ")
    search_keyword = input("Enter the keyword to search for: ")
    
    if os.path.isdir(folder_path):
        search_with_ripgrep(folder_path, search_keyword)
    else:
        print("The specified path is not a valid directory.")
