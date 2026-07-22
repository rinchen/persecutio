(function () {
  var announcer = document.getElementById('status-announcer');
  var input = document.getElementById('country-search');
  var out = document.getElementById('search-results');
  var SLUG_RE = /^[a-z0-9-]+$/;

  function announce(msg) {
    if (announcer) announcer.textContent = msg;
  }

  function setSearchUnavailable(message) {
    if (input) {
      input.disabled = true;
      input.placeholder = 'Search unavailable';
      input.setAttribute('aria-disabled', 'true');
    }
    if (out) {
      out.textContent = '';
      var el = document.createElement('div');
      el.className = 'loading';
      el.style.padding = '12px';
      el.textContent = message;
      out.appendChild(el);
      out.classList.remove('hidden');
    }
    announce(message);
  }

  function isSafeSlug(slug) {
    return typeof slug === 'string' && SLUG_RE.test(slug);
  }

  function renderHits(hits, indexData) {
    out.textContent = '';
    hits.forEach(function (h) {
      var item = indexData.find(function (d) { return d.slug === h.ref; });
      if (!item || !isSafeSlug(item.slug)) return;
      var a = document.createElement('a');
      a.className = 'search-result-item';
      a.setAttribute('role', 'option');
      a.href = 'countries/' + item.slug + '.html';
      a.appendChild(document.createTextNode(String(item.title || '')));
      var meta = document.createElement('span');
      meta.className = 'meta';
      meta.textContent = ' \u2014 ' + String(item.country || '');
      a.appendChild(meta);
      out.appendChild(a);
    });
  }

  fetch('assets/data/search.json?v=' + Date.now())
    .then(function (r) {
      if (!r.ok) throw new Error(r.statusText || String(r.status));
      return r.json();
    })
    .then(function (indexData) {
      var idx = lunr(function () {
        this.ref('slug');
        this.field('title');
        this.field('country');
        indexData.forEach(function (d) { this.add(d); }, this);
      });

      if (!input || !out) return;

      input.addEventListener('input', function () {
        var q = input.value.trim();
        if (q.length < 2) {
          out.classList.add('hidden');
          out.textContent = '';
          return;
        }
        var hits = idx.search(q + '*').slice(0, 8);
        if (!hits.length) {
          out.textContent = '';
          var empty = document.createElement('div');
          empty.className = 'loading';
          empty.style.padding = '12px';
          empty.textContent = 'No results found';
          out.appendChild(empty);
          out.classList.remove('hidden');
          return;
        }
        renderHits(hits, indexData);
        out.classList.remove('hidden');
        announce(hits.length + ' results found.');
      });

      input.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          out.classList.add('hidden');
          out.textContent = '';
          input.blur();
        }
      });
    })
    .catch(function (err) {
      console.error('search.json load failed', err);
      setSearchUnavailable('Search unavailable');
    });
})();
