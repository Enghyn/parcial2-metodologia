/*
 * Nombre de marca — punto único de reemplazo.
 *
 * El proyecto NO tiene una marca definida. Este valor es provisorio y debe
 * permanecer visiblemente marcado como (TBD) hasta que el usuario lo defina.
 * Cambiar únicamente BRAND_NAME y volver a renderizar los previews.
 *
 * Sin red, sin build, sin dependencias.
 */
(function () {
  "use strict";

  var BRAND_NAME = "Consultorio (marca provisoria)";

  function apply(root) {
    var scope = root || document;
    var nodes = scope.querySelectorAll("[data-brand-name]");
    var i;

    for (i = 0; i < nodes.length; i += 1) {
      nodes[i].textContent = BRAND_NAME;
    }

    // Etiquetas accesibles que necesitan el nombre dentro de una frase.
    var labelled = scope.querySelectorAll("[data-brand-label]");
    for (i = 0; i < labelled.length; i += 1) {
      labelled[i].setAttribute(
        "aria-label",
        labelled[i].getAttribute("data-brand-label").replace("{marca}", BRAND_NAME)
      );
    }

    if (document.title.indexOf("{marca}") !== -1) {
      document.title = document.title.replace("{marca}", BRAND_NAME);
    }
  }

  window.DesignSystemBrand = {
    name: BRAND_NAME,
    provisional: true,
    apply: apply
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      apply(document);
    });
  } else {
    apply(document);
  }
})();
