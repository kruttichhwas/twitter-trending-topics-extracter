import time
import uuid
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from pymongo import MongoClient
from selenium.webdriver.chrome.service import Service
from flask import Flask, render_template_string, jsonify
from webdriver_manager.chrome import ChromeDriverManager
import json 

client = MongoClient("MONGODB_DATABASE_CONNECTION_LINK")
db = client['twitter_trends']
collection = db['trending_topics']

PROXYMESH_USERNAME = "PROXYMESH_USERNAME"
PROXYMESH_PASSWORD = "PROXYMESHPASSWORD"
PROXY_HOST = "open.proxymesh.com"
PROXY_PORT = "31280"
PROXY = f"{PROXYMESH_USERNAME}:{PROXYMESH_PASSWORD}@{PROXY_HOST}:{PROXY_PORT}" 
TWITTER_URL = "https://x.com/i/flow/login"

options = webdriver.ChromeOptions()
options.add_argument(f'--proxy-server=http://{PROXY}')
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), 
    options=options
)

def fetch_trending_topics():
    try:
        driver.get(TWITTER_URL)
        time.sleep(20)

        driver.find_element(By.XPATH, "//input[@autocomplete='username']").send_keys("TWITTER_EMAIL")
        time.sleep(10)
        driver.find_element(By.XPATH, "//div[@aria-labelledby='modal-header']/div/div/div[2]/div[2]/div/div/div/button[2]").click()
        time.sleep(20)

        try:
            driver.find_element(By.XPATH, "//input[@autocomplete='current-password']").send_keys("TWITTER_PASSWORD")
        except:
            driver.find_element(By.XPATH, "//input[@data-testid='ocfEnterTextTextInput']").send_keys("TWITTER_USERNAME")
            time.sleep(10)
            driver.find_element(By.XPATH, "//button[@data-testid='ocfEnterTextNextButton']").click()
            time.sleep(20)


        driver.find_element(By.XPATH, "//input[@autocomplete='current-password']").send_keys("TWITTER_PASSWORD")
        time.sleep(10)
        driver.find_element(By.XPATH, "//button[@data-testid='LoginForm_Login_Button']").click()
        time.sleep(30)

        trends = []
        trends.append(driver.find_element(By.XPATH, "//div[@aria-label='Timeline: Trending now']/div/div[3]//span").text)
        trends.append(driver.find_element(By.XPATH, "//div[@aria-label='Timeline: Trending now']/div/div[4]/div/div/div/div[2]//span[@class='css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3']").text)
        trends.append(driver.find_element(By.XPATH, "//div[@aria-label='Timeline: Trending now']/div/div[5]/div/div/div/div[2]//span[@class='css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3']").text)
        trends.append(driver.find_element(By.XPATH, "//div[@aria-label='Timeline: Trending now']/div/div[6]/div/div/div/div[2]//span[@class='css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3']").text)
        trends.append(driver.find_element(By.XPATH, "//div[@aria-label='Timeline: Trending now']/div/div[7]/div/div/div/div[2]//span[@class='css-1jxf684 r-bcqeeo r-1ttztb7 r-qvutc0 r-poiln3']").text)

        unique_id = str(uuid.uuid4())
        driver.get("https://api64.ipify.org?format=json")
        ip_address = json.loads(driver.find_element("tag name", "body").text)["ip"]

        record = {
            "_id": unique_id,
            "trend1": trends[0] if len(trends) > 0 else "",
            "trend2": trends[1] if len(trends) > 1 else "",
            "trend3": trends[2] if len(trends) > 2 else "",
            "trend4": trends[3] if len(trends) > 3 else "",
            "trend5": trends[4] if len(trends) > 4 else "",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip_address": ip_address
        }
        collection.insert_one(record)

        return record
    except Exception as e:
        print("Error fetching trends:", e)
        return None
    finally:
        driver.quit()

app = Flask(__name__)

@app.route('/')
def home():
    return render_template_string('''
        <h1>Twitter Trending Topics</h1>
        <button onclick="fetchResults()">Click here to run the script</button>
        <div id="results"></div>
        <script>
            async function fetchResults() {
                const response = await fetch('/run-script');
                const data = await response.json();
                document.getElementById('results').innerHTML = `
                    <p>These are the most happening topics as on ${data.timestamp}:</p>
                    <ul>
                        <li>${data.trend1}</li>
                        <li>${data.trend2}</li>
                        <li>${data.trend3}</li>
                        <li>${data.trend4}</li>
                        <li>${data.trend5}</li>
                    </ul>
                    <p>The IP address used for this query was ${data.ip_address}.</p>
                    <p>Here’s a JSON extract of this record from the MongoDB:</p>
                    <pre>${JSON.stringify(data, null, 2)}</pre>
                    <button onclick="fetchResults()">Click here to run the query again</button>
                `;
            }
        </script>
    ''')

@app.route('/run-script')
def run_script():
    result = fetch_trending_topics()
    if result:
        return jsonify(result)
    return jsonify({"error": "Failed to fetch trends"})

if __name__ == '__main__':
    app.run(debug=True)
