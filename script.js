const map = L.map('map').setView([0, 0], 2);

// Base tile layers
const tileLayers = [
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }),
  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap, © Carto'
  }),
  L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    attribution: '© OpenStreetMap, © Carto'
  })
];

let currentLayerIndex = 0;
tileLayers[currentLayerIndex].addTo(map);

// Double-click and double-tap map switch
function switchBaseMap() {
  map.removeLayer(tileLayers[currentLayerIndex]);
  currentLayerIndex = (currentLayerIndex + 1) % tileLayers.length;
  tileLayers[currentLayerIndex].addTo(map);
}
map.on('dblclick', switchBaseMap);

let lastTap = 0;
map.getContainer().addEventListener('touchend', e => {
  const now = new Date().getTime();
  if (now - lastTap < 300) switchBaseMap();
  lastTap = now;
});

const allCoords = [];

// Load GPX files from a runner directory and draw them in the specified color
function loadRunnerTracks(basePath, color) {
  return fetch(`${basePath}/index.json`)
    .then(res => {
      if (!res.ok) throw new Error(`Failed to load ${basePath}/index.json`);
      return res.json();
    })
    .then(runFiles => {
      return Promise.all(runFiles.map(file =>
        fetch(`${basePath}/${file}`)
          .then(res => {
            if (!res.ok) throw new Error(`Failed to load ${file}`);
            return res.text();
          })
          .then(xmlText => {
            const xml = new DOMParser().parseFromString(xmlText, "text/xml");
            const geojson = toGeoJSON.gpx(xml);
            geojson.features.forEach(feature => {
              const coords = feature.geometry.coordinates.map(c => [c[1], c[0]]);
              if (coords.length) {
                allCoords.push(...coords); // Global coords across both runners
                L.polyline(coords, { color }).addTo(map);
              }
            });
          })
      ));
    });
}

// Load both runners' tracks and adjust the map view once all are loaded
Promise.all([
  loadRunnerTracks('runs_janos', '#250ff2'),
  loadRunnerTracks('runs_jazmin', '#eb21d3')
]).then(() => {
  if (allCoords.length > 0) {
    const bounds = L.latLngBounds(allCoords);
    map.fitBounds(bounds);
  }
}).catch(err => {
  console.error("Error loading runner tracks:", err);
});
