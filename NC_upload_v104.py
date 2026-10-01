import os, sys, time, glob, requests
import urllib.parse

# Setup for Nextcloud WebDAV URL, credentials, and session
NEXTCLOUD_URL = "https://your_company_name/remote.php/dav/files/your_name"
USERNAME = "Your User Name"
PASSWORD = "Your Password"

# Define local and remote prefixes
local_prefix = r"DirectoryToFindTheFile"
remote_prefix = r"DirectoryToUploadTheFile"

# Create a session for HTTP requests
session = requests.Session()
session.auth = (USERNAME, PASSWORD)

def encode_remote_path(path):
    """Encode remote path to handle special characters, keeping slashes intact."""
    path = path.replace("\\", "/")  # Ensure forward slashes
    return urllib.parse.quote(path, safe='/')  # Encode path for URL

def get_files(local_folder, remote_folder):
    """Get all files recursively, skipping symlink loops."""
    files = glob.glob(os.path.join(local_folder, '**', '*'), recursive=True)
    files_loc = [f for f in files if os.path.isfile(f) and not os.path.islink(f)]
    files_rem = [f.replace(os.path.dirname(local_folder), remote_folder).replace("\\", "/") for f in files_loc]

    files_loc = [f for f in files_loc if not '_archive' in f]
    files_rem = [f for f in files_rem if not '_archive' in f]
    
    return files_loc, files_rem

def get_directories(local_folder, remote_folder):
    """Get all files recursively, skipping symlink loops."""
    files = glob.glob(os.path.join(local_folder, '**', '*'), recursive=True)
    dirs  = [f for f in files if os.path.isdir(f)]
    dirs  = [d.replace(os.path.dirname(local_folder), remote_folder).replace("\\", "/") for d in dirs]
    new_dir = os.path.dirname(dirs[0])
    dirs.insert(0, new_dir)
    
    dirs  = [d for d in dirs if not '_archive' in d]
    
    return dirs

def file_exists(remote_path):
    """Check if the file exists using GET method for files."""
    url = f"{NEXTCLOUD_URL}{encode_remote_path(remote_path)}"
    try:
        response = session.get(url)
        if response.status_code == 200:
            return True
        elif response.status_code == 404:
            return False
        else:
            print(f"Unexpected response: {response.status_code} for {remote_path}")
            return False
    except requests.RequestException as e:
        print(f"Error checking if file exists: {remote_path} - {e}")
        return False

def create_directory(remote_path):
    """Create the remote directory on Nextcloud using WebDAV."""

    encoded_path = encode_remote_path(remote_path)
    
    url = f"{NEXTCLOUD_URL}/{encoded_path}"
    # print(f"Creating/checking directory: {url}")

    try:
        response = session.request("PROPFIND", url)
        if response.status_code == 207:  # Directory exists
            pass
            # print(f"Directory exists: {encoded_path}")
        elif response.status_code == 404:  # Directory does not exist, create it
            response = session.request("MKCOL", url)
            if response.status_code == 201:
                print(f"Created directory: {encoded_path}")
            else:
                print(f"Failed to create directory: {encoded_path}. Status code: {response.status_code}")
        else:
            print(f"Unexpected response: {response.status_code} for {url}")
    except requests.RequestException as e:
        print(f"Error creating directory {encoded_path}: {e}")    

def upload_file_via_webdav(local_file, remote_path):
    """Upload a file to Nextcloud using WebDAV, creating directories if necessary."""

    # Skip upload if the file already exists
    if file_exists(remote_path):
        # print(f"File already exists: {remote_path}. Skipping upload.")
        return

    # Upload the file if its not existing
    print(f"Uploading file: {local_file} -> {remote_path}")

    encoded_remote_path = encode_remote_path(remote_path)
    url = f"{NEXTCLOUD_URL}{encoded_remote_path}"

    with open(local_file, 'rb') as file_data:
        headers = {'OCS-APIRequest': 'true'}
        response = session.put(url, data=file_data, headers=headers)

        # print(f"Response Status Code: {response.status_code}")
        if response.status_code == 201:
            pass
            # print(f"Successfully uploaded: {local_file} -> {remote_path}")
        else:
            print(f"Failed to upload: {local_file} -> {remote_path}. Status code: {response.status_code}")

def main():
    """Main function to upload files and folders."""
    try:
        # parse locally for a file and directory list
        dirs_to_create  = get_directories(local_prefix, remote_prefix)
        files_local, files_to_upload = get_files(local_prefix, remote_prefix)
        
        # create the directories online and dynamically from a local structure
        for dir_ in dirs_to_create:
            create_directory(dir_)

        # upload the files onto the NC directory structure        
        for i, local_file in enumerate(files_local):
            upload_file_via_webdav(local_file, files_to_upload[i])

    except Exception as e:
        print(f"Error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    startTime = time.time()
    print('Starting upload routine ... \n')
    main()
    T_now       = time.time()
    T_elapsed   = T_now - startTime
    TT = time.strftime('%H:%M:%S', time.gmtime(T_elapsed))
    print(f'Execution time NC upload: {TT} hrs')
            
