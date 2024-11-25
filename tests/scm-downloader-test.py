import os
import requests

def download_file(repo_url, commit_hash, file_path, save_dir):
    """
    Downloads a specific file from a given GitHub repo and commit hash.
    
    Args:
        repo_url (str): GitHub repository URL.
        commit_hash (str): Commit hash to download the file from.
        file_path (str): Path of the file in the repository to download.
        save_dir (str): Directory to save the downloaded file.
    """
    # Extract owner and repo name from the GitHub URL
    owner, repo = repo_url.rstrip("/").split("/")[-2:]
    # Construct the raw file URL for the specific commit and file
    raw_file_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{commit_hash}/{file_path}"
    
    try:
        # Send a GET request to download the file
        response = requests.get(raw_file_url)
        response.raise_for_status()  # Raise an error for HTTP issues
        
        # Save the file locally
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{repo_url.split('/')[-1].split('-')[-1]}_highlights.scm")
        with open(save_path, "wb") as file:
            file.write(response.content)
        
        print(f"Downloaded: {raw_file_url} -> {save_path}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {raw_file_url}: {e}")

def process_repos_file(repos_file, file_to_download, save_dir):
    """
    Processes the repos.txt file and downloads the specified file for each repo and hash.
    
    Args:
        repos_file (str): Path to the file containing repo URL and commit hash pairs.
        file_to_download (str): File path in the repo to download.
        save_dir (str): Directory to save downloaded files.
    """
    with open(repos_file, "r") as file:
        for line in file:
            if line.strip():  # Skip empty lines
                repo_url, commit_hash = line.split()
                download_file(repo_url, commit_hash, file_to_download, save_dir)

if __name__ == "__main__":
    # Path to the repos.txt file
    repos_file = "/media/aakash/active/_axnet-latest/_git.rxiv/minimark/src/minimark/data/treesitter-grammar_repos.txt"
    # File to download from each repo
    file_to_download = "queries/highlights.scm"
    # Directory to save the downloaded files
    save_dir = "downloaded_files"
    
    # Process the repos.txt file and download the required files
    process_repos_file(repos_file, file_to_download, save_dir)

