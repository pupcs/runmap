const map = L.map('map').setView([0, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OpenStreetMap contributors'
}).addTo(map);

const tcxFiles = ['runs/run1.tcx', 'runs/run2.tcx']; // Add all your .tcx filenames here

tcxFiles.forEach(file => {
  fetch(file)
    .then(res => res.text())
    .then(xmlText => {
      const parser = new DOMParser();
      const xml = parser.parseFromString(xmlText, "text/xml");
      const geojson = toGeoJSON.tcx(xml);

      geojson.features.forEach(f => {
        const coords = f.geometry.coordinates.map(c => [c[1], c[0]]);
        L.polyline(coords, { color: 'blue' }).addTo(map);
      });

      // Zoom to first route
      if (geojson.features.length) {
        const bounds = L.geoJSON(geojson).getBounds();
        map.fitBounds(bounds);
      }
    });
});
