import os
import requests

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]
RUNS_DIR = "runs/"

def get_access_token():
    response = requests.post("https://www.strava.com/oauth/token", data={
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
    
    response = requests.get("https://www.strava.com/api/v3/athlete/activities", headers=headers)
    
    try:
        data = response.json()
    except ValueError:
        print("❌ Failed to decode JSON response")
        print(response.text)
        return

    # Check if we received an error instead of a list of activities
    if not isinstance(data, list):
        print("❌ Error fetching activities:", data)
        return

    os.makedirs(RUNS_DIR, exist_ok=True)

    for activity in data:
        if activity['type'] != "Run":
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
        print(f"✅ Downloaded {gpx_path}")


if __name__ == "__main__":
    download_runs()
