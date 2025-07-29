const map = L.map('map').setView([0, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

const allCoords = [];

console.log("🗺️ Map initialized. Fetching index.json...");

fetch('runs/index.json')
  .then(res => {
    if (!res.ok) {
      throw new Error(`Failed to load index.json: ${res.status}`);
    }
    return res.json();
  })
  .then(runFiles => {
    console.log(`📄 Found ${runFiles.length} run files:`, runFiles);

    let filesLoaded = 0;

    runFiles.forEach(file => {
      console.log(`📥 Fetching ${file}...`);

      fetch('runs/' + file)
        .then(res => {
          if (!res.ok) {
            throw new Error(`Failed to load ${file}: ${res.status}`);
          }
          return res.text();
        })
        .then(xmlText => {
          const xml = new DOMParser().parseFromString(xmlText, "text/xml");
          const geojson = toGeoJSON.gpx(xml); // or toGeoJSON.tcx(xml)

          if (!geojson.features.length) {
            console.warn(`⚠️ No features found in ${file}`);
            return;
          }

          geojson.features.forEach(f => {
            const coords = f.geometry.coordinates.map(c => [c[1], c[0]]);
            if (coords.length > 0) {
              console.log(`✅ Drawing ${file} with ${coords.length} points`);
              allCoords.push(...coords);
              L.polyline(coords, { color: 'blue' }).addTo(map);
            } else {
              console.warn(`⚠️ ${file} has no valid coordinates`);
            }
          });

          filesLoaded++;
          if (filesLoaded === runFiles.length && allCoords.length > 0) {
            const bounds = L.latLngBounds(allCoords);
            map.fitBounds(bounds);
            console.log("🔍 Zoomed to all tracks");
          }
        })
        .catch(err => {
          console.error(`❌ Error loading or parsing ${file}:`, err);
        });
    });
  })
  .catch(err => {
    console.error("❌ Error loading index.json:", err);
  });
