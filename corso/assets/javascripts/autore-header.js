// "Prof. Giuseppe Bosi" nella barra in alto, sotto il titolo, su tutte le pagine (richiesta del 28/10/2026).
// La barra è fissa (sticky) e con la navigazione istantanea di Material non viene mai ricreata: basta inserirlo una volta.
(function () {
  "use strict";
  function inserisci() {
    var titolo = document.querySelector(".md-header__title .md-header__topic:first-child");
    if (!titolo || document.querySelector(".autore-header")) return;
    var a = document.createElement("a");
    a.className = "autore-header";
    var en = document.documentElement.lang === "en";
    a.href = en ? "https://www.giuseppebosi.com/en/" : "https://www.giuseppebosi.com";
    a.textContent = en ? "by Prof. Giuseppe Bosi" : "Prof. Giuseppe Bosi";
    a.title = en ? "Giuseppe Bosi's personal website" : "Sito personale di Giuseppe Bosi";
    titolo.appendChild(a);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", inserisci);
  else inserisci();
})();
