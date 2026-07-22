(function(){
  const map = L.map('map').setView([20,10],2);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'&copy; OSM'}).addTo(map);
  fetch('assets/data/geojson.json?v='+Date.now()).then(r=>r.json()).then(data=>{
    L.geoJSON(data,{
      style:f=>({color:({severe:'#dc2626',warning:'#f97316',restricted:'#facc15',open:'#3b82f6',persecution:'#ef4444'}[f.properties.status]||'#94a3b8'),weight:1}),
      onEachFeature:(f,l)=>{l.on('click',()=>{window.location.href='countries/'+f.properties.slug+'.html';});l.bindTooltip(f.properties.title,{sticky:true});}
    }).addTo(map);
  }).catch(()=>{document.getElementById('map').innerHTML='<div class="p-4 text-red-600">Map data failed to load.</div>';});
})();
