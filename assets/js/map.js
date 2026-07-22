(function() {
  const map = L.map('map').setView([20, 10], 2);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OSM' }).addTo(map);
  fetch('countries/geojson.json?v=' + Date.now())
    .then(r => {
      if (!r.ok) throw new Error(r.statusText);
      return r.json();
    })
    .then(data => {
      L.geoJSON(data, {
        pointToLayer: (f, latlng) => {
          const levels = {
            'Extreme': '#dc2626',
            'Very High': '#ef4444',
            'Moderate/High': '#f97316',
            'High': '#f97316',
            'Moderate': '#facc15',
            'Low': '#3b82f6'
          };
          return L.circleMarker(latlng, {
            radius: 5,
            fillColor: levels[f.properties.level] || '#94a3b8',
            color: '#fff',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.9
          });
        },
        onEachFeature: (f, l) => {
          l.on('click', () => {
            window.location.href = 'countries/' + f.properties.slug + '.html';
          });
          l.bindTooltip(f.properties.title + ' — ' + (f.properties.level || ''), { sticky: true });
        }
      }).addTo(map);
    })
    .catch(err => {
      console.error('geojson load failed', err);
      const el = document.getElementById('map');
      if (el) el.innerHTML = '<div class="p-4 text-red-600">Map data failed to load.</div>';
    });
})();
