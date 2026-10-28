// "Prof. Giuseppe Bosi" nella barra in alto, accanto al titolo, su tutte le pagine (richiesta del 28/10/2026).
// La barra è fissa (sticky) e con la navigazione istantanea di Material non viene mai ricreata: basta inserirlo una volta.
(function () {
  "use strict";
  function inserisci() {
    var titolo = document.querySelector(".md-header__title");
    if (!titolo || document.querySelector(".autore-header")) return;
    var a = document.createElement("a");
    a.className = "autore-header";
    a.href = "https://home.giuseppebosi.com";
    a.textContent = "Prof. Giuseppe Bosi";
    a.title = "Sito personale di Giuseppe Bosi";
    titolo.insertAdjacentElement("afterend", a);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", inserisci);
  else inserisci();
})();
