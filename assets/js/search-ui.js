(function(){
  fetch('assets/data/search.json?v='+Date.now())
    .then(r => {
      if (!r.ok) throw new Error(r.statusText);
      return r.json();
    })
    .then(indexData => {
      const idx = lunr(function(){this.ref('slug');this.field('title');this.field('country');indexData.forEach(d=>this.add(d));});
      const input = document.getElementById('country-search');
      const out = document.getElementById('search-results');
      if(!input||!out)return;
      input.addEventListener('input',()=>{
        const q=input.value.trim();
        if(q.length<2){out.classList.add('hidden');return;}
        const hits=idx.search(q+'*').slice(0,8);
        if(!hits.length){out.classList.add('hidden');return;}
        out.innerHTML=hits.map(h=>{const item=indexData.find(d=>d.slug===h.ref);if(!item)return '';return `<a class="block px-3 py-2 hover:bg-slate-50 text-sm" href="countries/${item.slug}.html">${item.title} <span class="text-slate-500">— ${item.country}</span></a>`;}).join('');
        out.classList.remove('hidden');
      });
    })
    .catch(err => console.error('search.json load failed', err));
})();
