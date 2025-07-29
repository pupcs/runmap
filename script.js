const map = L.map('map').setView([0, 0], 2);

// Define multiple base tile layers
const tileLayers = [
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }),
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap, © Carto'
  }),
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap, © Carto'
  }),
  L.tileLayer('https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png', {
    attribution: 'Map tiles by Stamen Design — Map data © OpenStreetMap'
  })
];

let currentLayerIndex = 0;

// Add the first tile layer
tileLayers[currentLayerIndex].addTo(map);

// Function to cycle to the next tile layer
function switchBaseMap() {
  map.removeLayer(tileLayers[currentLayerIndex]);
  currentLayerIndex = (currentLayerIndex + 1) % tileLayers.length;
  tileLayers[currentLayerIndex].addTo(map);
}

// Bind double-click and double-tap
map.on('dblclick', switchBaseMap);

// Basic mobile double-tap handling
let lastTap = 0;
map.getContainer().addEventListener('touchend', e => {
  const now = new Date().getTime();
  if (now - lastTap < 300) {
    switchBaseMap();
  }
  lastTap = now;
});
const allCoords = [];

fetch('runs/index.json')
  .then(res => {
    if (!res.ok) throw new Error(`Failed to load index.json: ${res.status}`);
    return res.json();
  })
  .then(runFiles => {
    let filesLoaded = 0;

    runFiles.forEach(file => {
      fetch(`runs/${file}`)
        .then(res => {
          if (!res.ok) throw new Error(`Failed to load ${file}: ${res.status}`);
          return res.text();
        })
        .then(xmlText => {
          const xml = new DOMParser().parseFromString(xmlText, "text/xml");
          const geojson = toGeoJSON.gpx(xml);
          if (!geojson.features.length) return;

          geojson.features.forEach(feature => {
            const coords = feature.geometry.coordinates.map(c => [c[1], c[0]]);
            if (coords.length) {
              allCoords.push(...coords);
              L.polyline(coords, { color: 'blue' }).addTo(map);
            }
          });

          filesLoaded++;
          if (filesLoaded === runFiles.length && allCoords.length > 0) {
            const bounds = L.latLngBounds(allCoords);
            map.fitBounds(bounds);
          }
        })
        .catch(err => console.error(`Error processing ${file}:`, err));
    });
  })
  .catch(err => console.error("Error loading index.json:", err));
