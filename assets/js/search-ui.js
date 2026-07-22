(function () {
  var announcer = document.getElementById('status-announcer');

  fetch('assets/data/search.json?v=' + Date.now())
    .then(function (r) {
      if (!r.ok) throw new Error(r.statusText);
      return r.json();
    })
    .then(function (indexData) {
      var idx = lunr(function () {
        this.ref('slug');
        this.field('title');
        this.field('country');
        indexData.forEach(function (d) { this.add(d); }, this);
      });

      var input = document.getElementById('country-search');
      var out = document.getElementById('search-results');
      if (!input || !out) return;

      input.addEventListener('input', function () {
        var q = input.value.trim();
        if (q.length < 2) {
          out.classList.add('hidden');
          out.innerHTML = '';
          return;
        }
        var hits = idx.search(q + '*').slice(0, 8);
        if (!hits.length) {
          out.innerHTML = '<div class="loading" style="padding:12px">No results found</div>';
          out.classList.remove('hidden');
          return;
        }
        out.innerHTML = hits.map(function (h) {
          var item = indexData.find(function (d) { return d.slug === h.ref; });
          if (!item) return '';
          return '<a class="search-result-item" role="option" href="countries/' + item.slug + '.html">' +
            item.title +
            ' <span class="meta">\u2014 ' + item.country + '</span></a>';
        }).join('');
        out.classList.remove('hidden');
        if (announcer) announcer.textContent = hits.length + ' results found.';
      });

      input.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
          out.classList.add('hidden');
          out.innerHTML = '';
          input.blur();
        }
      });
    })
    .catch(function (err) {
      console.error('search.json load failed', err);
    });
})();
