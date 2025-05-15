import time
import pickle
import requests
import hashlib
import os
import json
import http.server
import socketserver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup

def hash_image(file_path, hash_algorithm="md5"):
    hash_func = hashlib.new(hash_algorithm)
    with open(file_path, "rb") as file:
        while chunk := file.read(8192):  # read in 8KB chunks
            hash_func.update(chunk)
    return hash_func.hexdigest()

def hash_images_in_folder(folder_path, output_file, hash_algorithm="md5"):
    image_hashes = []

    # iterate through all files in the folder
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(".jpg"):  # only process .jpg files
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                image_hash = hash_image(file_path, hash_algorithm)
                image_hashes.append({"filename": filename, "hash": image_hash})
                
    # save hashes to JSON 
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(image_hashes, file, indent=4)

# sets the flags so chrome doesn't get blocked because its a bot :>
setflags = webdriver.ChromeOptions()
setflags.add_argument("--disable-blink-features=AutomationControlled") 
setflags.add_experimental_option("excludeSwitches", ["enable-automation"])  
setflags.add_experimental_option("useAutomationExtension", False) 
driver = webdriver.Chrome(options=setflags)

accounts = ['https://www.instagram.com/deakin.outdoors', 'https://www.instagram.com/deakinenviroclub/', 
            'https://www.instagram.com/deakincyber/', 'https://www.instagram.com/yourdusa/']

driver.get('https://www.instagram.com/')

driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
cookies = pickle.load(open("..\\cookies.pkl", "rb")) # load the cookies for the bot account
for cookie in cookies:
    driver.add_cookie(cookie)

time.sleep(3)
driver.refresh()

account_index = 0
captions = {}
for account in accounts: # goes through each accout page
    index = 0
    got_six_images = False
    driver.get(account)

    time.sleep(10)

    posts = driver.find_element(By.CLASS_NAME, "x1n2onr6") # search for the required divs that holds the images
    rows = posts.find_elements(By.CLASS_NAME, "_ac7v")     # the divs have strange names...probably an obfuscation technique to stop web scraping

    for row in rows: # instagram breaks up the posts into rows of three
        images = row.find_elements(By.TAG_NAME, "img")
        for img in images: # go through each post in each row
            response = requests.get(img.get_attribute("src"))
            if response.status_code == 200: # download the post
                with open(f"downloaded_images\\{account_index}{index}.jpg", "wb") as file: 
                    file.write(response.content)
                    captions[f"{account_index}{index}.jpg"] = img.get_attribute("alt")
                    index += 1
            else:
                print(f"Failed to download image {index}")
                print(img.get_attribute("src") + "\n\n")
            if index == 6:
                got_six_images = True
                break
        if got_six_images: # once we get the last six posts we move to the next account
            break
    account_index += 1
            
print('Downloaded last six posts')

# takes a hash digest of each post. If the hash has changed we know they have posted something new.
hash_images_in_folder("downloaded_images", "downloaded_images\\new_image_hashes.json", "md5")

# load the old hashes and new hashes for comparison
new_hashes = json.load(open("downloaded_images\\new_image_hashes.json", "r", encoding="utf-8"))
if os.path.exists("old_image_hashes.json"):
    old_hashes = json.load(open("old_image_hashes.json", "r", encoding="utf-8"))
    # gets the hashes that differ between files with a one liner
    new_posts = [hash_value for hash_value in new_hashes if hash_value["hash"] not in [old_hash["hash"] for old_hash in old_hashes]]
else:
    new_posts = new_hashes

# parse the new posts into a html file for presentation
with open(f"downloaded_images\\index.html", "r", encoding="utf-8") as website:
    soup = BeautifulSoup(website, "html.parser")
    gallery = soup.find("div", class_="gallery")
    gallery.clear()
    for post in new_posts:
        # creates image tag
        image = soup.new_tag("img")
        image.attrs['src'] = post['filename']
        
        #creates <p> tag
        caption_tag = soup.new_tag("p")    
        caption_tag.string = captions.get(post['filename'])

        gallery.append(image)
        gallery.append(caption_tag)
        website.close()
with open(f"downloaded_images\\index.html", "w", encoding="utf-8") as website:
    website.write(str(soup))

# start a web server so we can access the new posts :)
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="downloaded_images", **kwargs)

with socketserver.TCPServer(("", 8000), CustomHandler) as httpd:
    print(f"Serving new instagram posts on port 8000")
    httpd.serve_forever()