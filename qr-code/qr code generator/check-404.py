from pyzbar.pyzbar import decode
from PIL import Image
import os
import requests
from urllib.parse import urlparse
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Function to extract URLs from QR codes in images
def extract_urls_from_qr(directory):
    urls = []
    for root, dirs, files in os.walk(directory):
        for file_name in files:
            if file_name.endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(root, file_name)
                img = Image.open(img_path)
                decoded_objects = decode(img)
                for obj in decoded_objects:
                    if obj.data:
                        url = obj.data.decode('utf-8')
                        # Ensure URL starts with 'http://' or 'https://'
                        if not urlparse(url).scheme:
                            url = 'https://' + url
                        urls.append(url)
    return urls

# Function to check URLs for 404 status and return results
def check_urls_for_404(urls):
    url_status_list = []
    count_404 = 0  # Counter for 404 errors

    for url in urls:
        try:
            response = requests.head(url, allow_redirects=True)
            if response.status_code == 404:
                status = "404 Error"
                count_404 += 1  # Increment 404 counter
            else:
                status = f"Active (Status: {response.status_code})"
        except requests.RequestException as e:
            status = f"Error: {e}"

        # Print the status of each URL as it's checked
        print(f"Checking {url}: {status}")

        # Append URL and its status to the list
        url_status_list.append({"URL": url, "Status": status})
    
    return url_status_list, count_404  # Return the results and the 404 count

# Main function to process a specific folder or all subdirectories
def process_folders(qr_directory, process_all=True, specific_subfolder=None):
    all_results = []
    total_404_count = 0

    if process_all:
        # Loop through all subdirectories inside the main directory
        for subfolder in os.listdir(qr_directory):
            subfolder_path = os.path.join(qr_directory, subfolder)
            
            if os.path.isdir(subfolder_path):  # Ensure it's a directory
                print(f"\nProcessing folder: {subfolder}")

                urls = extract_urls_from_qr(subfolder_path)
                if urls:
                    print(f"Found {len(urls)} URLs in {subfolder}. Checking for 404 status...")
                    url_status_list, count_404 = check_urls_for_404(urls)

                    # Track all results and total 404 count
                    all_results.extend(url_status_list)
                    total_404_count += count_404
                else:
                    print(f"No URLs found in {subfolder}.")
    elif specific_subfolder:
        subfolder_path = os.path.join(qr_directory, specific_subfolder)
        if os.path.isdir(subfolder_path):  # Ensure it's a valid directory
            print(f"\nProcessing folder: {specific_subfolder}")

            urls = extract_urls_from_qr(subfolder_path)
            if urls:
                print(f"Found {len(urls)} URLs in {specific_subfolder}. Checking for 404 status...")
                url_status_list, count_404 = check_urls_for_404(urls)

                # Track all results and total 404 count
                all_results.extend(url_status_list)
                total_404_count += count_404
            else:
                print(f"No URLs found in {specific_subfolder}.")
        else:
            print(f"Folder '{specific_subfolder}' not found. Please check the folder name.")

    # Save the results to an Excel file
    if all_results:
        df = pd.DataFrame(all_results)
        output_file = os.path.join(SCRIPT_DIR, 'qr_code_results.xlsx')
        df.to_excel(output_file, index=False)
        print(f"\nResults saved to {output_file} in the current directory.")
        print(f"Total 404 Errors Found: {total_404_count}")
    else:
        print("\nNo URLs were found.")

# Main directory containing all subdirectories
qr_directory = os.path.join(SCRIPT_DIR, 'qrs')

# Get user choice for processing
user_choice = input("Do you want to process all folders (1) or a specific folder (2)? ").strip().upper()

if user_choice == "1":
    # Process all folders
    process_folders(qr_directory, process_all=True)
elif user_choice == "2":
    # Get user input for the specific subfolder
    specific_subfolder = input("Enter the vendor id to process (not case sensitive): ").upper()
    process_folders(qr_directory, process_all=False, specific_subfolder=specific_subfolder)
else:
    print("Invalid option. Please enter 'A' for all folders or 'S' for a specific folder.")
