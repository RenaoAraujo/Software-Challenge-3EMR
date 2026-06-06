// Aplicado antes do body carregar (via <script> na <head>) para evitar flash de tema errado.
(function () {
  try {
    var t = localStorage.getItem("emr-theme");
    if (t === "light" || t === "dark") document.documentElement.setAttribute("data-theme", t);
  } catch (e) {}
})();
