function interpolateColor(color1, color2, factor) {
  const hexToRgb = hex => [
    parseInt(hex.slice(1, 3), 16),
    parseInt(hex.slice(3, 5), 16),
    parseInt(hex.slice(5, 7), 16)
  ];
  const rgbToHex = rgb => '#' + rgb.map(v => v.toString(16).padStart(2, '0')).join('');

  const c1 = hexToRgb(color1);
  const c2 = hexToRgb(color2);
  const result = c1.map((v, i) => Math.round(v + factor * (c2[i] - v)));
  return rgbToHex(result);
}

// Slider presets
const janosStart = "#0000ff"; // blue
const janosEnd   = "#4dff00ff"; // cyan

const jazminStart = "#ff00ff"; // pink
const jazminEnd   = "#ff0000"; // red

function getRunnerColors() {
  const fJanos = parseInt(document.getElementById("color-janos").value, 10) / 100;
  const fJazmin = parseInt(document.getElementById("color-jazmin").value, 10) / 100;
  return {
    janos: interpolateColor(janosStart, janosEnd, fJanos),
    jazmin: interpolateColor(jazminStart, jazminEnd, fJazmin)
  };
}

const map = L.map('map').setView([0, 0], 2);

const tileSources = {
  osm: L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'),
  light: L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png'),
  dark: L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png')
};

let currentTile = tileSources.osm;
currentTile.addTo(map);

function updateBaseLayer(styleKey) {
  if (tileSources[styleKey] && tileSources[styleKey] !== currentTile) {
    map.removeLayer(currentTile);
    currentTile = tileSources[styleKey];
    currentTile.addTo(map);
  }
}

const allCoords = [];
let janosLayerGroup = L.layerGroup().addTo(map);
let jazminLayerGroup = L.layerGroup().addTo(map);

function loadRunnerTracks(basePath, color, layerGroup) {
  layerGroup.clearLayers();
  return fetch(`${basePath}/index.json`)
    .then(res => res.json())
    .then(runFiles => Promise.all(runFiles.map(file =>
      fetch(`${basePath}/${file}`)
        .then(res => res.text())
        .then(xmlText => {
          const xml = new DOMParser().parseFromString(xmlText, "text/xml");
          const geojson = toGeoJSON.gpx(xml);
          geojson.features.forEach(feature => {
            const coords = feature.geometry.coordinates.map(c => [c[1], c[0]]);
            if (coords.length) {
              allCoords.push(...coords);
              L.polyline(coords, { color }).addTo(layerGroup);
            }
          });
        })
    )));
}

function reloadAllTracks() {
  allCoords.length = 0;
  const colors = getRunnerColors();

  Promise.all([
    loadRunnerTracks('runs_janos', colors.janos, janosLayerGroup),
    loadRunnerTracks('runs_jazmin', colors.jazmin, jazminLayerGroup)
  ]).then(() => {
    if (allCoords.length > 0) {
      map.fitBounds(L.latLngBounds(allCoords));
    }
  });
}


// Initial load
reloadAllTracks();

// Menu toggle
document.getElementById('menu-toggle').addEventListener('click', () => {
  const panel = document.getElementById('settings-panel');
  panel.classList.toggle('hidden');
});

// Handlers for UI controls
document.querySelectorAll('input[name="map-style"]').forEach(el => {
  el.addEventListener('change', (e) => {
    updateBaseLayer(e.target.value);
  });
});

document.getElementById('color-janos').addEventListener('input', reloadAllTracks);
document.getElementById('color-jazmin').addEventListener('input', reloadAllTracks);

