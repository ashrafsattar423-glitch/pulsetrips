import os
import re
import json
import random
import requests
import google.generativeai as genai

# Configuration (Supports both variable names)
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MAKE_WEBHOOK_URL = os.getenv("MAKE_WEBHOOK_URL") or os.getenv("WEBHOOK_URL")

genai.configure(api_key=GEMINI_API_KEY)

# Affiliate Links
AFFILIATE_LINKS = {
    "flights": "https://kiwi.tpk.ro/NsxwLSqE",
    "esim": "https://airalo.tpk.ro/WZs9mIjC",
    "tours": "https://klook.tpk.ro/TmmM5wxy",
    "transfers": "https://gettransfer.tpk.ro/sdoNOlXV",
    "airhelp": "https://airhelp.tpk.ro/GJreOSXw"
}

DESTINATIONS = [
    "Tokyo, Japan", "Paris, France", "Rome, Italy", "Bali, Indonesia",
    "New York, USA", "London, UK", "Barcelona, Spain", "Dubai, UAE",
    "Istanbul, Turkey", "Bangkok, Thailand", "Amsterdam, Netherlands"
]

def clean_text(text):
    return re.sub(r'[*#_`]', '', text).strip()

def get_pexels_image(query):
    headers = {"Authorization": PEXELS_API_KEY}
    url = f"https://api.pexels.com/v1/search?query={query}&per_page=1"
    try:
        res = requests.get(url, headers=headers).json()
        if res.get("photos"):
            return res["photos"][0]["src"]["large"]
    except Exception as e:
        print(f"Pexels error: {e}")
    return "https://images.pexels.com/photos/386009/pexels-photo-386009.jpeg"

def generate_content(destination):
    # Updated model string format to ensure compatibility
    model = genai.GenerativeModel("models/gemini-1.5-flash")
    prompt = f"Create a short travel guide for {destination}. Return ONLY JSON with keys: 'title', 'description', 'slug'."
    
    try:
        res = model.generate_content(prompt)
        text = res.text
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
            return data["title"], data["description"], data["slug"]
    except Exception as e:
        print(f"Gemini API Error: {e}")
    
    slug = destination.lower().replace(",", "").replace(" ", "-")
    return f"Explore {destination}", f"Discover the best of {destination}.", slug

def build_html_page(title, description, image_url, destination, slug):
    os.makedirs("destinations", exist_ok=True)
    file_path = f"destinations/{slug}.html"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; margin: 0; padding: 20px; color: #333; }}
        .card {{ max-width: 650px; margin: 20px auto; background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
        .card img {{ width: 100%; height: 350px; object-fit: cover; }}
        .content {{ padding: 25px; text-align: center; }}
        h1 {{ font-size: 26px; margin-bottom: 15px; color: #1a1a1a; }}
        p {{ font-size: 16px; line-height: 1.6; color: #555; margin-bottom: 25px; text-align: left; }}
        
        .btn-container {{ display: flex; flex-direction: column; gap: 12px; margin-top: 20px; }}
        .btn {{ display: block; padding: 14px 20px; border-radius: 10px; font-weight: bold; text-decoration: none; font-size: 16px; transition: transform 0.2s, opacity 0.2s; color: white; }}
        .btn:hover {{ transform: translateY(-2px); opacity: 0.95; }}
        
        .btn-flights {{ background-color: #00a699; }}
        .btn-esim {{ background-color: #ff5a5f; }}
        .btn-tours {{ background-color: #ffb400; color: #1a1a1a; }}
        .btn-transfers {{ background-color: #484848; }}
        .btn-airhelp {{ background-color: #007bc7; }}
    </style>
</head>
<body>
    <div class="card">
        <img src="{image_url}" alt="{title}">
        <div class="content">
            <h1>{title}</h1>
            <p>{description}</p>            
            
            <div class="btn-container">
                <a href="{AFFILIATE_LINKS['flights']}" target="_blank" class="btn btn-flights">✈️ Search Flights on Kiwi</a>
                <a href="{AFFILIATE_LINKS['esim']}" target="_blank" class="btn btn-esim">📶 Get Travel eSIM (Airalo)</a>
                <a href="{AFFILIATE_LINKS['tours']}" target="_blank" class="btn btn-tours">🎟️ Book Tours & Activities (Klook)</a>
                <a href="{AFFILIATE_LINKS['transfers']}" target="_blank" class="btn btn-transfers">🚕 Airport Transfers & Cars (GetTransfer)</a>
                <a href="{AFFILIATE_LINKS['airhelp']}" target="_blank" class="btn btn-airhelp">⚖️ Delayed Flight Compensation (AirHelp)</a>
            </div>
        </div>
    </div>
</body>
</html>
"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    return f"https://pulsetrips.com/destinations/{slug}.html"

def send_to_make(title, description, image_url, page_url):
    if not MAKE_WEBHOOK_URL:
        print("Webhook URL missing, skipping Make.com call")
        return
    payload = {
        "title": title,
        "description": description,
        "image_url": image_url,
        "link": page_url
    }
    requests.post(MAKE_WEBHOOK_URL, json=payload)

def main():
    destination = random.choice(DESTINATIONS)
    title, description, slug = generate_content(destination)
    image_url = get_pexels_image(destination)
    
    page_url = build_html_page(title, description, image_url, destination, slug)
    send_to_make(title, description, image_url, page_url)
    print(f"Successfully processed for {destination}: {page_url}")

if __name__ == "__main__":
    main()
