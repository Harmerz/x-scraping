# app.py
from flask import Flask, jsonify
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import requests
import json
from pymongo import MongoClient
import time

# Connect to the MongoDB server
client = MongoClient("mongodb://localhost:27017/")

# Select the database
db = client["pustakadata"]
# Select the collection
collection = db["tweet"]

app = Flask(__name__)


@app.route("/")
def Tweets():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    # Example: Load a webpage
    driver.get(
        "https://cse.google.com/cse?cx=70b71d1f848434f92#gsc.tab=0&gsc.q=kompascom&gsc.sort=date"
    )
    print("Test")
    time.sleep(3)

    # Execute JavaScript to retrieve network data
    network_data = driver.execute_script("return window.performance.getEntries();")
    print("Test 2")

    # Close the browser
    driver.quit()
    print(network_data)
    # Define the pattern you want to match
    pattern = "https://cse.google.com/cse/element/v1"

    # Iterate over the array to find the object with the desired name
    found_string = None
    for obj in network_data:
        if pattern in obj.get("name"):
            found_string = obj.get("name")
            break

    # Check if the string was found
    if found_string:
        print("String found:", found_string)
    else:
        print("String not found")

    response = requests.get(found_string)
    if response.status_code == 200:
        print("Request successful")
    else:
        print("Request failed with status code:", response.status_code)

    start_index = response.text.find("{")
    end_index = response.text.rfind("}") + 1
    json_string = response.text[start_index:end_index]
    json_data = json.loads(json_string)

    results_info = []

    for result in json_data["results"]:
        og_description = result["richSnippet"]["metatags"].get("ogDescription")
        url = result.get("url")
        for item in result["richSnippet"]["socialmediaposting"]:
            date_published = item.get("datePublished", "Default Date")
        additional_name = result["richSnippet"]["person"].get("additionalname")
        identifier = result["richSnippet"]["socialmediaposting"].get("identifier")

        interaction_counts = []
        if "interactioncounter" in result["richSnippet"]:
            for interaction_counter in result["richSnippet"]["interactioncounter"]:
                user_interaction_count = interaction_counter.get("userinteractioncount")
                interaction_url = interaction_counter.get("url")
                interaction_name = interaction_counter.get("name")
                if user_interaction_count:
                    if interaction_url and (
                        "/retweets" in interaction_url
                        or "/retweets/with_comments" in interaction_url
                        or "/likes" in interaction_url
                    ):
                        interaction_counts.append(
                            {
                                "label": interaction_name,
                                "url": interaction_url,
                                "count": int(user_interaction_count),
                            }
                        )
                    elif interaction_name == "Replies":
                        interaction_counts.append(
                            {
                                "label": interaction_name,
                                "url": interaction_url,
                                "count": int(user_interaction_count),
                            }
                        )

        results_info.append(
            {
                "username": additional_name,
                "id": identifier,
                "tweets": og_description,
                "url": url,
                "date_published": date_published,
                "interactioncounts": interaction_counts,
            }
        )
    resData = results_info

    # Insert the documents
    insertData = collection.insert_many(resData)
    print("Inserted document ids:", insertData.inserted_ids)
    
    # Convert ObjectId to string in results_info for JSON serialization
    for doc in resData:
        if '_id' in doc:
            doc['_id'] = str(doc['_id'])  # Converting ObjectId to string

    print(resData)
    # Return network data as JSON response
    return jsonify(resData)
script = """
var entries = window.performance.getEntries();
return entries.filter(entry => entry.entryType === 'resource').map(entry => ({
    name: entry.name,
    entryType: entry.entryType,
    initiatorType: entry.initiatorType, // This property can help identify XHRs
    startTime: entry.startTime,
    duration: entry.duration,
    responseStart: entry.responseStart,
    responseEnd: entry.responseEnd,
    requestStart: entry.requestStart,
    transferSize: entry.transferSize,
    nextHopProtocol: entry.nextHopProtocol
}));
"""


@app.route("/responses")
def responses():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

    # Navigate to the page
    driver.get("https://twitter.com/kompascom/status/1785900319139909929")
    
    cookie = {'name': 'auth_token', 'value': 'd2011786b03db9c14b5e9044de8211cf00855ab0', 'domain': '.twitter.com'}
    driver.add_cookie(cookie)
    
    # Refresh the page to ensure the cookie is used
    driver.refresh()
    time.sleep(5)
  
    tweet_divs = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="tweetText"]')

    tweets = []
    for div in tweet_divs:
        span_elements = div.find_elements(By.CSS_SELECTOR, 'span.css-1qaijid.r-bcqeeo.r-qvutc0.r-poiln3')
        for span in span_elements:
            tweets.append(span.text)


    # Optionally, return the outerHTML of each div if needed elsewhere
    return tweets
    found_url = next((item.get("name") for item in network_data if "TweetDetail" in item.get("name")), None)
    
    if not found_url:
        return jsonify({"error": "No matching network data found"}), 404

    print(found_url)
    # Make an HTTP request to the found URL
    response = requests.get(found_url)
    response.raise_for_status()  # Raises an HTTPError for bad responses

    # Parse the response text as JSON
    json_data = json.loads(response.text)
    return jsonify(json_data)
    



if __name__ == "__main__":
    app.run(debug=True)
