import os
import json
import requests
import datetime
import gpxpy
import gpxpy.gpx


class Runner:
    def __init__(self, name: str):
        self.name = name.lower()
        self.client_id = os.environ[f"CLIENT_ID_{self.name.upper()}"]
        self.client_secret = os.environ[f"CLIENT_SECRET_{self.name.upper()}"]
        self.refresh_token = os.environ[f"REFRESH_TOKEN_{self.name.upper()}"]
        self.runs_dir = f"runs_{self.name}/"

    def get_access_token(self):
        response = requests.post("https://www.strava.com/oauth/token", data={
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token
        })
        response.raise_for_status()
        return response.json()["access_token"]

    def download_runs(self):
        token = self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        print(f"[{self.name}] Fetching activities...")
        response = requests.get(
            "https://www.strava.com/api/v3/athlete/activities",
            headers=headers,
            params={"per_page": 50, "page": 1}
        )

        try:
            activities = response.json()
        except ValueError:
            print(f"[{self.name}] Failed to decode activities response.")
            print(response.text)
            return

        if not isinstance(activities, list):
            print(f"[{self.name}] Unexpected response format:", activities)
            return

        if not activities:
            print(f"[{self.name}] No activities found.")
            return

        os.makedirs(self.runs_dir, exist_ok=True)

        for activity in activities:
            if activity.get('type') != "Run":
                continue

            activity_id = activity["id"]
            gpx_path = os.path.join(self.runs_dir, f"{activity_id}.gpx")

            if os.path.exists(gpx_path):
                print(f"[{self.name}] Skipping existing GPX: {activity_id}.gpx")
                continue

            print(f"[{self.name}] Fetching GPS data for activity {activity_id}...")

            stream_url = f"https://www.strava.com/api/v3/activities/{activity_id}/streams"
            params = {"keys": "latlng,time", "key_by_type": "true"}
            res = requests.get(stream_url, headers=headers, params=params)

            if res.status_code != 200:
                print(f"[{self.name}] Failed to fetch streams: {activity_id} (HTTP {res.status_code})")
                continue

            streams = res.json()
            latlngs = streams.get("latlng", {}).get("data")
            times = streams.get("time", {}).get("data")

            if not latlngs or not times or len(latlngs) != len(times):
                print(f"[{self.name}] Invalid GPS data for activity {activity_id}")
                continue

            # Build GPX structure
            gpx = gpxpy.gpx.GPX()
            track = gpxpy.gpx.GPXTrack()
            segment = gpxpy.gpx.GPXTrackSegment()
            track.segments.append(segment)
            gpx.tracks.append(track)

            start_time = datetime.datetime.strptime(activity["start_date"], "%Y-%m-%dT%H:%M:%SZ")
            for offset, (lat, lon) in zip(times, latlngs):
                point_time = start_time + datetime.timedelta(seconds=offset)
                segment.points.append(gpxpy.gpx.GPXTrackPoint(lat, lon, time=point_time))

            with open(gpx_path, "w") as f:
                f.write(gpx.to_xml())

            print(f"[{self.name}] Saved GPX: {gpx_path}")

    def save_index_file(self):
        files = [f for f in os.listdir(self.runs_dir) if f.endswith(".gpx")]
        index_path = os.path.join(self.runs_dir, "index.json")

        with open(index_path, "w") as f:
            json.dump(files, f)

        print(f"[{self.name}] Index updated: {len(files)} entries.")


if __name__ == "__main__":
    janos = Runner("janos")
    jazmin = Runner("jazmin")

    janos.download_runs()
    janos.save_index_file()

    jazmin.download_runs()
    jazmin.save_index_file()
