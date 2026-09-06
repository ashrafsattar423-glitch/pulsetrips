import os
import random
import requests
from google import genai

# ---------------------------------------------------------
# 1. READ SECRETS SAFELY FROM ENVIRONMENT VARIABLES
# ---------------------------------------------------------
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
BUFFER_API_KEY = os.getenv("BUFFER_API_KEY")
BUFFER_PROFILE_ID = os.getenv("BUFFER_PROFILE_ID")
GITHUB_TOKEN = os.getenv("GH_TOKEN")
GITHUB_REPO = "ashrafsattar423-glitch/pulsetrips"

# Target locations list for content generation
TARGET_LOCATIONS = [
    "Kyoto, Japan", "Santorini, Greece", "Maui, Hawaii", 
    "Reykjavik, Iceland", "Banff, Canada", "Amalfi Coast, Italy", 
    "Queenstown, New Zealand", "Swiss Alps, Switzerland", 
    "Cape Town, South Africa", "Bora Bora, French Polynesia"
]

# ---------------------------------------------------------
# 2. HELPER FUNCTIONS
# ---------------------------------------------------------
def get_pexels_image(query):
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
    res = requests.get(url, headers=headers)
    if res.status_code == 200 and res.json().get('photos'):
        return res.json()['photos'][0]['src']['large']
    return "https://images.pexels.com/photos/346885/pexels-photo-346885.jpeg"

def generate_gemini_content(location):
    client = genai.Client(api_key=GEMINI_API_KEY)
    prompt = f"""
    Write an engaging travel blog snippet for '{location}'. 
    Include:
    - 3 Must-visit places
    - Best time to visit
    - A quick travel tip
    Keep the tone exciting and concise for travel enthusiasts.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def generate_landing_page_html(location, content):
    # Convert newlines to HTML break tags safely outside f-string
    formatted_content = content.replace('\n', '<br>')
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Explore {location} - PulseTrips</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
        h1 {{ color: #0066cc; }}
        .content {{ background: #f9f9f9; padding: 20px; border-radius: 8px; border-left: 5px solid #0066cc; }}
    </style>
</head>
<body>
    <h1>Travel Guide: {location}</h1>
    <div class="content">
        {formatted_content}
    </div>
</body>
</html>"""
    return html_template

def push_to_github(location, html_content):
    filename = f"destinations/{location.lower().replace(' ', '-').replace(',', '')}.html"
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{filename}"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # Check if file exists to get SHA
    get_res = requests.get(url, headers=headers)
    sha = get_res.json().get('sha') if get_res.status_code == 200 else None

    import base64
    encoded_content = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
    
    payload = {
        "message": f"Add/Update landing page for {location}",
        "content": encoded_content
    }
    if sha:
        payload["sha"] = sha

    put_res = requests.put(url, headers=headers, json=payload)
    if put_res.status_code in [200, 201]:
        clean_filename = filename.replace("destinations/", "")
        page_url = f"https://pulsetrips.com/destinations/{clean_filename}"
        print(f"[+] Page successfully created/updated: {page_url}")
        return page_url
    else:
        print(f"[-] GitHub API Error: {put_res.status_code} - {put_res.text}")
        return None

def schedule_buffer_post(landing_url, image_url, text):
    url = "https://api.bufferapp.com/1/updates/create.json"
    payload = {
        "access_token": BUFFER_API_KEY,
        "profile_ids[]": BUFFER_PROFILE_ID,
        "text": f"{text}\n\nRead full travel guide here: {landing_url}",
        "media[photo]": image_url,
        "media[link]": landing_url
    }
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        print("[+] Pinterest Pin scheduled on Buffer successfully!")
    else:
        print(f"[-] Buffer API Error: {res.status_code} - {res.text}")

# ---------------------------------------------------------
# 3. MAIN WORKFLOW EXECUTION
# ---------------------------------------------------------
def run_autopilot_task():
    location = random.choice(TARGET_LOCATIONS)
    print(f"\n--- Running Autopilot for Location: {location} ---")
    
    print("[*] Fetching HD image from Pexels...")
    image_url = get_pexels_image(location)
    
    print("[*] Generating AI travel guide content using Gemini...")
    content = generate_gemini_content(location)
    
    print("[*] Creating landing page and pushing to GitHub Pages...")
    html_data = generate_landing_page_html(location, content)
    landing_url = push_to_github(location, html_data)
    
    if landing_url:
        print("[*] Scheduling Pin on Pinterest via Buffer...")
        schedule_buffer_post(landing_url, image_url, f"Top Things to Do in {location}")
        print("[+] Autopilot Workflow Completed Successfully!")

if __name__ == "__main__":
    run_autopilot_task()
