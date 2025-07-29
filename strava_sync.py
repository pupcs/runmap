import os
import requests
import json

import gpxpy
import gpxpy.gpx

CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]
RUNS_DIR = "runs/"

CLIENT_ID = "170279"
CLIENT_SECRET = "8f82c4a778fac76340e921af1cd57082cd47ca0b"
REFRESH_TOKEN = "1351f4799c3356a16542dd7c7e9284cbeacb88c4"

def save_index_file():
    files = [f for f in os.listdir(RUNS_DIR) if f.endswith(".gpx")]
    with open(os.path.join(RUNS_DIR, "index.json"), "w") as f:
        json.dump(files, f)

def get_access_token():
    response = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    })
    return response.json()["access_token"]

# Download latest activities
import os
import requests
import gpxpy
import gpxpy.gpx

def download_runs():
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    print("📡 Fetching activities...")
    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers=headers,
        params={"per_page": 50, "page": 1}  # adjust as needed
    )

    try:
        data = response.json()
    except ValueError:
        print("❌ Failed to decode JSON response")
        print(response.text)
        return

    if not isinstance(data, list):
        print("❌ Error fetching activities:", data)
        return

    if not data:
        print("⚠️ No activities found.")
        return

    os.makedirs(RUNS_DIR, exist_ok=True)

    for activity in data:
        if activity['type'] != "Run":
            continue

        activity_id = activity["id"]
        gpx_path = os.path.join(RUNS_DIR, f"{activity_id}.gpx")

        if os.path.exists(gpx_path):
            print(f"🔁 Skipping existing {activity_id}.gpx")
            continue

        print(f"⬇️  Fetching GPS stream for activity {activity_id}...")

        stream_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
        params = {"keys": "latlng,time", "key_by_type": "true"}
        res = requests.get(stream_url, headers=headers, params=params)

        if res.status_code != 200:
            print(f"❌ Failed to fetch streams for {activity_id}: status {res.status_code}")
            continue

        streams = res.json()

        if "latlng" not in streams or "time" not in streams:
            print(f"⚠️ No GPS data for {activity_id}")
            continue

        latlngs = streams["latlng"]["data"]
        times = streams["time"]["data"]

        if len(latlngs) != len(times):
            print(f"⚠️ Mismatch in latlng/time for {activity_id}")
            continue

        # Create GPX track
        gpx = gpxpy.gpx.GPX()
        segment = gpxpy.gpx.GPXTrackSegment()
        track = gpxpy.gpx.GPXTrack()
        track.segments.append(segment)
        gpx.tracks.append(track)

        import datetime
        start_time = datetime.datetime.strptime(activity["start_date"], "%Y-%m-%dT%H:%M:%SZ")

        for offset, (lat, lon) in zip(times, latlngs):
            point_time = start_time + datetime.timedelta(seconds=offset)
            segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, time=point_time))

        with open(gpx_path, "w") as f:
            f.write(gpx.to_xml())

        print(f"✅ Saved: {gpx_path}")




if __name__ == "__main__":
    download_runs()
    save_index_file()
