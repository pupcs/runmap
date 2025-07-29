const runFiles = ['runs/123456789.gpx', 'runs/987654321.gpx']; // Add programmatically

runFiles.forEach(file => {
  fetch(file)
    .then(res => res.text())
    .then(xmlText => {
      const parser = new DOMParser();
      const xml = parser.parseFromString(xmlText, "text/xml");
      const geojson = toGeoJSON.gpx(xml); // Use .gpx parser here
      geojson.features.forEach(f => {
        const coords = f.geometry.coordinates.map(c => [c[1], c[0]]);
        L.polyline(coords, { color: 'red' }).addTo(map);
      });
    });
});
