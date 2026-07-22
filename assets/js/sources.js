(function () {
  var updatedEl = document.getElementById('data-updated');
  var sourcesEl = document.getElementById('data-sources');

  function escapeHtml(s) {
    return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  function formatTimestamp(ts) {
    if (!ts) return '';
    try {
      var d = new Date(ts);
      return d.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch (e) {
      return ts;
    }
  }

  function render(data) {
    if (updatedEl) {
      updatedEl.textContent = data.generatedAt
        ? 'Data updated ' + data.generatedAt
        : 'Data update time unknown';
    }
    if (!sourcesEl) return;
    var sources = data.sources || [];
    if (!sources.length) { sourcesEl.hidden = true; return; }

    var chipsHtml = sources.map(function (s) {
      var st = s.status || 'unknown';
      var label = s.label || s.id;
      var title = s.title || s.id;
      var ts = formatTimestamp(s.fetchedAt);
      var tip = escapeHtml(title) + ': ' + escapeHtml(st) + (ts ? ' (' + escapeHtml(ts) + ')' : '');
      return '<li><span class="source-chip source-chip--' + escapeHtml(st) + '" title="' + tip + '">' + escapeHtml(label) + '</span></li>';
    }).join('');

    sourcesEl.innerHTML =
      '<span class="source-chips-label">Sources</span>' +
      '<ul class="source-legend">' +
        '<li class="source-legend__item"><span class="source-legend__swatch source-chip--ok"></span>OK</li>' +
        '<li class="source-legend__item"><span class="source-legend__swatch source-chip--partial"></span>Partial</li>' +
        '<li class="source-legend__item"><span class="source-legend__swatch source-chip--error"></span>Error</li>' +
        '<li class="source-legend__item"><span class="source-legend__swatch source-chip--skipped"></span>Skipped</li>' +
      '</ul>' +
      '<ul class="source-chips">' + chipsHtml + '</ul>';
    sourcesEl.hidden = false;
  }

  fetch('assets/data/meta.json')
    .then(function (r) {
      if (!r.ok) throw new Error(r.statusText || String(r.status));
      return r.json();
    })
    .then(render)
    .catch(function (err) {
      console.error('meta.json load failed', err);
      if (updatedEl) updatedEl.textContent = 'Source status unavailable';
      if (sourcesEl) {
        sourcesEl.hidden = true;
        sourcesEl.textContent = '';
      }
    });
})();
