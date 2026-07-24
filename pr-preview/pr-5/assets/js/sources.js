(function () {
  var updatedEl = document.getElementById('data-updated');
  var sourcesEl = document.getElementById('data-sources');
  var script = document.querySelector('script[src*="sources.js"]');
  var metaUrl = (script && script.getAttribute('data-meta')) || 'assets/data/meta.json';

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

  function legendHtml() {
    var items = [
      ['ok', 'OK'],
      ['partial', 'Partial'],
      ['error', 'Error'],
      ['skipped', 'Skipped']
    ];
    return (
      '<ul class="source-legend" aria-label="Source status color key">' +
      items
        .map(function (pair) {
          return (
            '<li class="source-legend__item">' +
              '<span class="source-legend__swatch source-chip--' + pair[0] + '" aria-hidden="true"></span>' +
              '<span class="source-legend__text">' + pair[1] + '</span>' +
            '</li>'
          );
        })
        .join('') +
      '</ul>'
    );
  }

  function render(data) {
    if (updatedEl) {
      updatedEl.textContent = data.generatedAt
        ? 'Data updated ' + data.generatedAt
        : 'Data update time unknown';
    }
    if (!sourcesEl) return;
    var sources = data.sources || [];
    if (!sources.length) {
      sourcesEl.hidden = true;
      sourcesEl.innerHTML = '';
      return;
    }

    var chipsHtml = sources
      .map(function (s) {
        var st = s.status || 'unknown';
        var label = s.label || s.id;
        var title = s.title || s.id;
        var ts = formatTimestamp(s.fetchedAt);
        var tip =
          escapeHtml(title) +
          ': ' +
          escapeHtml(st) +
          (ts ? ' (' + escapeHtml(ts) + ')' : '');
        var aria = escapeHtml(title) + ': ' + escapeHtml(st);
        return (
          '<li><span class="source-chip source-chip--' +
          escapeHtml(st) +
          '" title="' +
          tip +
          '" aria-label="' +
          aria +
          '">' +
          escapeHtml(label) +
          '</span></li>'
        );
      })
      .join('');

    sourcesEl.innerHTML =
      '<div class="site-footer__sources-head">' +
        '<span class="site-footer__sources-label">Sources</span>' +
        legendHtml() +
      '</div>' +
      '<ul class="source-chips" aria-label="Data source status">' +
        chipsHtml +
      '</ul>';
    sourcesEl.hidden = false;
  }

  fetch(metaUrl)
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
