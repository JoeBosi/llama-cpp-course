// Clic (o Invio/Spazio) su un diagramma Mermaid → lo riapre, ridisegnato per intero nella
// finestra, in una vista a schermo intero. Il codice sorgente originale viene letto da
// data-mermaid-src (scritto a tempo di build da scripts/mermaid_fence.py): non si può
// leggerlo dall'elemento che Material ha già disegnato, perché lo mette in uno shadow DOM
// "closed" (non ispezionabile da JS). Si registra una sola volta: la navigazione istantanea
// di Material non ricarica mai questa pagina, quindi non serve rifare l'aggancio a ogni click.
(function () {
  "use strict";

  function decodeSource(base64) {
    try {
      var binary = atob(base64);
      var bytes = new Uint8Array(binary.length);
      for (var i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      return new TextDecoder("utf-8").decode(bytes);
    } catch (err) {
      return "";
    }
  }

  var modal = null;
  var scrollEl = null;
  var diagramEl = null;
  var lastFocused = null;
  var renderCount = 0;
  var currentSvg = null;
  var naturalSize = null; // {w, h}: dimensione "vera" del disegno, letta dal viewBox
  var isFitted = true; // vista di partenza: sempre adattata alla finestra

  function updateHint() {
    if (!diagramEl) return;
    diagramEl.setAttribute(
      "data-hint",
      isFitted ? "Clic per vedere a grandezza naturale" : "Clic per adattare alla finestra"
    );
  }

  // Vista "adatta alla finestra": non deforma mai il diagramma, lo scala (in su o in giù)
  // perché stia tutto visibile, senza dover scorrere. È la vista con cui si apre sempre.
  function applyFit() {
    if (!currentSvg || !scrollEl || !naturalSize) return;
    var cs = getComputedStyle(scrollEl);
    var availW = scrollEl.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    var availH = scrollEl.clientHeight - parseFloat(cs.paddingTop) - parseFloat(cs.paddingBottom);
    var scale = Math.min(availW / naturalSize.w, availH / naturalSize.h, 4);
    currentSvg.style.width = naturalSize.w * scale + "px";
    currentSvg.style.height = naturalSize.h * scale + "px";
  }

  // Vista "grandezza naturale": 1:1 con quanto disegnato da Mermaid, per leggere un
  // dettaglio in un diagramma molto denso; scorre se non ci sta nella finestra.
  function applyNaturalSize() {
    if (!currentSvg || !naturalSize) return;
    currentSvg.style.width = naturalSize.w + "px";
    currentSvg.style.height = naturalSize.h + "px";
  }

  function applyCurrentMode() {
    if (isFitted) applyFit();
    else applyNaturalSize();
    if (diagramEl) diagramEl.classList.toggle("is-natural-size", !isFitted);
    updateHint();
  }

  function toggleMode() {
    isFitted = !isFitted;
    applyCurrentMode();
  }

  function buildModal() {
    if (modal) return modal;
    modal = document.createElement("div");
    modal.className = "mermaid-modal";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-label", "Diagramma a schermo intero");
    modal.innerHTML =
      '<div class="mermaid-modal__backdrop" data-mermaid-close></div>' +
      '<div class="mermaid-modal__panel">' +
      '<button type="button" class="mermaid-modal__close" data-mermaid-close aria-label="Chiudi (Esc)">' +
      "&#10005;</button>" +
      '<div class="mermaid-modal__scroll"><div class="mermaid-modal__diagram"></div></div>' +
      "</div>";
    document.body.appendChild(modal);
    scrollEl = modal.querySelector(".mermaid-modal__scroll");
    diagramEl = modal.querySelector(".mermaid-modal__diagram");
    diagramEl.addEventListener("click", function (event) {
      if (event.target.closest("svg")) toggleMode();
    });
    window.addEventListener("resize", function () {
      if (modal.classList.contains("is-open") && isFitted) applyFit();
    });
    return modal;
  }

  function closeModal() {
    if (!modal || !modal.classList.contains("is-open")) return;
    modal.classList.remove("is-open");
    document.documentElement.classList.remove("mermaid-modal-open");
    window.setTimeout(function () {
      if (diagramEl) diagramEl.innerHTML = "";
      currentSvg = null;
      naturalSize = null;
    }, 200);
    if (lastFocused && typeof lastFocused.focus === "function") lastFocused.focus();
  }

  function openModal(triggerEl) {
    buildModal();
    lastFocused = triggerEl || document.activeElement;
    isFitted = true;
    modal.classList.add("is-open");
    document.documentElement.classList.add("mermaid-modal-open");
    modal.querySelector(".mermaid-modal__close").focus();
  }

  function openDiagram(figure) {
    var src = figure.getAttribute("data-mermaid-src");
    if (!src || typeof window.mermaid === "undefined") return;
    var code = decodeSource(src);
    if (!code) return;
    buildModal();
    openModal(figure);
    diagramEl.setAttribute("aria-busy", "true");
    diagramEl.removeAttribute("data-hint");
    diagramEl.textContent = "Disegno il diagramma…";
    var id = "mermaid-lightbox-" + renderCount++;
    window.mermaid
      .render(id, code)
      .then(function (result) {
        diagramEl.innerHTML = result.svg;
        currentSvg = diagramEl.querySelector("svg");
        if (currentSvg) {
          currentSvg.removeAttribute("height");
          currentSvg.style.maxWidth = "none";
          var viewBox = currentSvg.viewBox && currentSvg.viewBox.baseVal;
          var bbox = currentSvg.getBBox();
          naturalSize = {
            w: (viewBox && viewBox.width) || bbox.width,
            h: (viewBox && viewBox.height) || bbox.height,
          };
          applyCurrentMode();
        }
      })
      .catch(function () {
        diagramEl.textContent = "Non è stato possibile disegnare il diagramma.";
      })
      .finally(function () {
        diagramEl.removeAttribute("aria-busy");
      });
  }

  document.addEventListener("click", function (event) {
    var figure = event.target.closest(".mermaid-figure");
    if (figure) {
      openDiagram(figure);
      return;
    }
    if (event.target.closest("[data-mermaid-close]")) {
      closeModal();
    }
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeModal();
      return;
    }
    if (event.key !== "Enter" && event.key !== " ") return;
    var figure = event.target.closest(".mermaid-figure");
    if (figure) {
      event.preventDefault();
      openDiagram(figure);
    }
  });
})();
