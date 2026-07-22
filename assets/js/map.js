(function () {
  var mapEl = document.getElementById('map');
  var announcer = document.getElementById('status-announcer');

  var map = L.map('map', {
    zoomControl: true,
    attributionControl: true
  }).setView([20, 10], 2);

  L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>',
    maxZoom: 18,
    subdomains: 'abcd'
  }).addTo(map);

  var isTouch = L.Browser.touch || L.Browser.mobile;
  var baseRadius = isTouch ? 10 : 8;
  var baseWeight = isTouch ? 2.5 : 2;

  var levels = {
    'Extreme': '#dc2626',
    'Very High': '#ef4444',
    'Moderate/High': '#f97316',
    'High': '#f97316',
    'Moderate': '#facc15',
    'Low': '#3b82f6'
  };

  function announce(msg) {
    if (announcer) announcer.textContent = msg;
  }

  announce('Loading map data...');

  fetch('countries/geojson.json?v=' + Date.now())
    .then(function (r) {
      if (!r.ok) throw new Error(r.statusText);
      return r.json();
    })
    .then(function (data) {
      var count = data.features ? data.features.length : 0;

      L.geoJSON(data, {
        pointToLayer: function (f, latlng) {
          var color = levels[f.properties.level] || '#94a3b8';
          var marker = L.circleMarker(latlng, {
            radius: baseRadius,
            fillColor: color,
            color: '#fff',
            weight: baseWeight,
            opacity: 1,
            fillOpacity: 0.85,
            className: 'persecution-marker'
          });

          if (!isTouch) {
            marker.on('mouseover', function () {
              this.setStyle({ weight: 3, fillOpacity: 1 });
              this.openTooltip();
            });
            marker.on('mouseout', function () {
              this.setStyle({ weight: baseWeight, fillOpacity: 0.85 });
              this.closeTooltip();
            });
          }

          return marker;
        },
        onEachFeature: function (f, l) {
          l.on('click', function () {
            window.location.href = 'countries/' + f.properties.slug + '.html';
          });
          var label = f.properties.title;
          if (f.properties.level) {
            label += ' \u2014 ' + f.properties.level;
          }
          l.bindTooltip(label, {
            sticky: true,
            direction: 'top',
            offset: [0, -baseRadius]
          });
        }
      }).addTo(map);

      announce(count + ' countries loaded on map.');
    })
    .catch(function (err) {
      console.error('geojson load failed', err);
      if (mapEl) {
        mapEl.innerHTML = '<div class="loading">Map data failed to load. Please try refreshing the page.</div>';
      }
      announce('Failed to load map data.');
    });
})();
