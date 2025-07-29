import requests
import os

CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
REFRESH_TOKEN = "your_initial_refresh_token"  # Get via manual OAuth once
RUNS_DIR = "runs/"

# Get a fresh access token
def get_access_token():
    url = "https://www.strava.com/oauth/token"
    response = requests.post(url, data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    })
    return response.json()["access_token"]

# Download latest activities
def download_runs():
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    activities = requests.get("https://www.strava.com/api/v3/athlete/activities", headers=headers).json()
    
    os.makedirs(RUNS_DIR, exist_ok=True)
    
    for activity in activities:
        if activity["type"] != "Run":
            continue
        activity_id = activity["id"]
        gpx_path = os.path.join(RUNS_DIR, f"{activity_id}.gpx")
        if os.path.exists(gpx_path):
            continue
        # Download GPX
        url = f"https://www.strava.com/api/v3/activities/{activity_id}/export_gpx"
        gpx = requests.get(url, headers=headers)
        with open(gpx_path, "wb") as f:
            f.write(gpx.content)
        print(f"Downloaded {gpx_path}")

if __name__ == "__main__":
    download_runs()
