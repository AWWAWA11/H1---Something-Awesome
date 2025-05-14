import time
import pickle
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# sets the flags so chrome doesn't get blocked because its a bot :>
setflags = webdriver.ChromeOptions()
setflags.add_argument("--disable-blink-features=AutomationControlled") 
setflags.add_experimental_option("excludeSwitches", ["enable-automation"])  
setflags.add_experimental_option("useAutomationExtension", False) 
driver = webdriver.Chrome(options=setflags)

driver.get('https://www.instagram.com/')


driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})") 
cookies = pickle.load(open("..\\cookies.pkl", "rb")) # load the cookies for the bot account
for cookie in cookies:
    driver.add_cookie(cookie)
initial_url = driver.current_url

time.sleep(3)
driver.refresh()
driver.get('https://www.instagram.com/deakin.outdoors')

time.sleep(10)

target_div = driver.find_element(By.CLASS_NAME, "x1n2onr6") # search for the required divs that holds the images
target_div2 = target_div.find_element(By.CLASS_NAME, "_ac7v")

# Find all <img> elements inside the <div>

index = 0
images = target_div2.find_elements(By.TAG_NAME, "img")
for img in images:
    response = requests.get(img.get_attribute("src"))
    if response.status_code == 200:
        # write the images to disk
        with open(f"image_{index}.jpg", "wb") as file: 
            file.write(response.content)
    else:
        print(f"Failed to download image {index}")
        print(img.get_attribute("src") + "\n\n")
    index+=1

print("Done listing all images!")
time.sleep(10000)
