const map = L.map('map').setView([0, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

fetch('runs/index.json')
  .then(res => res.json())
  .then(runFiles => {
    runFiles.forEach(file => {
      fetch('runs/' + file)
        .then(res => res.text())
        .then(xmlText => {
          const xml = new DOMParser().parseFromString(xmlText, "text/xml");
          const geojson = toGeoJSON.gpx(xml); // or .tcx if using TCX
          geojson.features.forEach(f => {
            const coords = f.geometry.coordinates.map(c => [c[1], c[0]]);
            L.polyline(coords, { color: 'blue' }).addTo(map);
          });
        });
    });
  });
