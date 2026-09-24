// Clic (o Invio/Spazio) su un diagramma Mermaid → lo riapre, ridisegnato più grande,
// in una finestra a schermo intero. Il codice sorgente originale viene letto da
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
  var diagramEl = null;
  var lastFocused = null;
  var renderCount = 0;

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
    diagramEl = modal.querySelector(".mermaid-modal__diagram");
    return modal;
  }

  function closeModal() {
    if (!modal || !modal.classList.contains("is-open")) return;
    modal.classList.remove("is-open");
    document.documentElement.classList.remove("mermaid-modal-open");
    window.setTimeout(function () {
      if (diagramEl) diagramEl.innerHTML = "";
    }, 200);
    if (lastFocused && typeof lastFocused.focus === "function") lastFocused.focus();
  }

  function openModal(triggerEl) {
    buildModal();
    lastFocused = triggerEl || document.activeElement;
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
    diagramEl.textContent = "Disegno il diagramma…";
    var id = "mermaid-lightbox-" + renderCount++;
    window.mermaid
      .render(id, code)
      .then(function (result) {
        diagramEl.innerHTML = result.svg;
        var svg = diagramEl.querySelector("svg");
        if (svg) {
          svg.removeAttribute("height");
          svg.style.maxWidth = "none";
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
