/* Форма заявки: отправка без перезагрузки, метки визита, цель в Метрике.
   Без JavaScript форма уходит обычным POST и сервер отвечает страницей. */
(function () {
  var UTM = ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term"];
  var KEY = "padacha-visit";

  // Метки первого захода за сессию: человек пришёл из Директа, походил
  // по сайту и оставил заявку со страницы без меток — источник не теряем.
  var visit = null;
  try { visit = JSON.parse(sessionStorage.getItem(KEY) || "null"); } catch (e) {}
  if (!visit) {
    var q = new URLSearchParams(location.search);
    visit = { referrer: document.referrer || "" };
    UTM.forEach(function (k) { if (q.get(k)) visit[k] = q.get(k); });
    try { sessionStorage.setItem(KEY, JSON.stringify(visit)); } catch (e) {}
  }

  document.querySelectorAll("form[data-lead]").forEach(function (form) {
    var msg = form.querySelector(".lead-msg");
    var btn = form.querySelector("button[type=submit]");
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var data = new FormData(form);
      Object.keys(visit).forEach(function (k) { data.set(k, visit[k]); });
      btn.disabled = true;
      msg.className = "lead-msg";
      msg.textContent = "Отправляем…";
      fetch(form.action, { method: "POST", body: data, headers: { Accept: "application/json" } })
        .then(function (r) { return r.json(); })
        .then(function (res) {
          if (!res.ok) throw new Error(res.error || "");
          form.classList.add("sent");
          msg.textContent = "Заявка у нас. Перезвоним в течение рабочего дня.";
          if (typeof ym === "function") ym(112273830, "reachGoal", "lead_form");
        })
        .catch(function (err) {
          btn.disabled = false;
          msg.className = "lead-msg err";
          msg.textContent = err.message || "Не отправилось. Позвоните нам — так даже быстрее.";
        });
    });
  });
})();
