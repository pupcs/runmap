import os
import json
import requests
import datetime
import gpxpy
import gpxpy.gpx

# Environment variables for Strava API credentials
CLIENT_ID = os.environ["CLIENT_ID"]
CLIENT_SECRET = os.environ["CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["REFRESH_TOKEN"]

# Output directory for GPX files
RUNS_DIR = "runs/"

def get_access_token():
    """
    Exchanges the refresh token for a new access token.
    """
    response = requests.post("https://www.strava.com/oauth/token", data={
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN
    })

    response.raise_for_status()
    return response.json()["access_token"]

def download_runs():
    """
    Fetches recent running activities and exports them to GPX files.
    """
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}

    print("Fetching activities...")
    response = requests.get(
        "https://www.strava.com/api/v3/athlete/activities",
        headers=headers,
        params={"per_page": 50, "page": 1}
    )

    try:
        activities = response.json()
    except ValueError:
        print("Failed to decode activities response.")
        print(response.text)
        return

    if not isinstance(activities, list):
        print("Unexpected response format:", activities)
        return

    if not activities:
        print("No activities found.")
        return

    os.makedirs(RUNS_DIR, exist_ok=True)

    for activity in activities:
        if activity.get('type') != "Run":
            continue

        activity_id = activity["id"]
        gpx_path = os.path.join(RUNS_DIR, f"{activity_id}.gpx")

        if os.path.exists(gpx_path):
            print(f"Skipping existing GPX: {activity_id}.gpx")
            continue

        print(f"Fetching GPS data for activity {activity_id}...")

        # Request the GPS data stream
        stream_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
        params = {"keys": "latlng,time", "key_by_type": "true"}
        res = requests.get(stream_url, headers=headers, params=params)

        if res.status_code != 200:
            print(f"Failed to fetch streams for activity {activity_id}: HTTP {res.status_code}")
            continue

        streams = res.json()
        latlngs = streams.get("latlng", {}).get("data")
        times = streams.get("time", {}).get("data")

        if not latlngs or not times or len(latlngs) != len(times):
            print(f"No valid GPS data for activity {activity_id}")
            continue

        # Build the GPX structure
        gpx = gpxpy.gpx.GPX()
        track = gpxpy.gpx.GPXTrack()
        segment = gpxpy.gpx.GPXTrackSegment()
        track.segments.append(segment)
        gpx.tracks.append(track)

        start_time = datetime.datetime.strptime(activity["start_date"], "%Y-%m-%dT%H:%M:%SZ")

        for offset, (lat, lon) in zip(times, latlngs):
            point_time = start_time + datetime.timedelta(seconds=offset)
            segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, time=point_time))

        # Save the GPX file
        with open(gpx_path, "w") as f:
            f.write(gpx.to_xml())

        print(f"Saved GPX: {gpx_path}")

def save_index_file():
    """
    Generates an index.json file listing all downloaded GPX files.
    """
    files = [f for f in os.listdir(RUNS_DIR) if f.endswith(".gpx")]
    index_path = os.path.join(RUNS_DIR, "index.json")

    with open(index_path, "w") as f:
        json.dump(files, f)

    print(f"Index file updated with {len(files)} entries.")

if __name__ == "__main__":
    download_runs()
    save_index_file()
