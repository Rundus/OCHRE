# --- download_files_from_website.py ---
# --- Author: C. Feltman ---
# DESCRIPTION: downloads all the files from a specific webpage
from tqdm import tqdm
from bs4 import BeautifulSoup
import requests

#######################################
# --- Get a string of all the files ---
#######################################
webpage_url = "http://tid.uio.no/plasma/aurora/nya6/6300/2018/20181208/ut08/"
def find_files():
    soup = BeautifulSoup(requests.get(webpage_url).text)
    hrefs = []
    for a in soup.find_all('a'):
        hrefs.append(a['href'])
    return hrefs

list_of_links = find_files()


#################################################
# --- trim list to only included wanted files ---
#################################################
FileNames = []
for item in list_of_links:
    if '.png' in item:
        FileNames.append(item)

##############################################
# --- Download Files to Destination Folder ---
##############################################
destinationFolderPath = r'C:\Data\TRICEII\all_sky\6300\nyAlesund'

import wget
for item in tqdm(FileNames):
    wget.download(webpage_url + item, destinationFolderPath+'\\' + item)