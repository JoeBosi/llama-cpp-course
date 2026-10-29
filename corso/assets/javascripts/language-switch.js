// Selettore lingua: porta alla stessa pagina nell'altra lingua (italiano alla radice, inglese sotto /en/).
// Funziona anche con la navigazione istantanea di Material: l'indirizzo si calcola al momento del clic.
(function () {
  "use strict";
  window.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[hreflang]");
    if (!a || !a.closest(".md-select")) return;
    var path = location.pathname.replace(/^\/en(\/|$)/, "/");
    var dest = a.getAttribute("hreflang") === "en" ? "/en" + path : path;
    e.preventDefault();
    e.stopImmediatePropagation();
    location.href = dest + location.hash;
  }, true);
})();
