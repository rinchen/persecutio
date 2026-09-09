(function () {
  var btn = document.getElementById('back-to-top');
  if (!btn) return;

  var prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ticking = false;

  function onScroll() {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(function () {
      if (window.scrollY > 480) {
        btn.classList.add('is-visible');
        btn.removeAttribute('hidden');
      } else {
        btn.classList.remove('is-visible');
        btn.setAttribute('hidden', '');
      }
      ticking = false;
    });
  }

  btn.setAttribute('hidden', '');
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  btn.addEventListener('click', function () {
    window.scrollTo({
      top: 0,
      behavior: prefersReduced ? 'auto' : 'smooth'
    });
    var main = document.getElementById('main-content');
    if (main) {
      main.focus({ preventScroll: true });
    }
  });
})();
