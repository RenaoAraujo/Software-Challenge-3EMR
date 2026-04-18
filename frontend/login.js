(() => {
  const API_BASE = "/api";
  const THEME_KEY = "emr-theme";

  const form = document.getElementById("form-login");
  const user = document.getElementById("login-user");
  const pass = document.getElementById("login-pass");
  const btn = document.getElementById("btn-login-submit");
  const errEl = document.getElementById("login-error");
  const themeBtn = document.getElementById("login-theme-toggle");

  function applyTheme(theme) {
    if (theme !== "light" && theme !== "dark") return;
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      /* ignore */
    }
  }

  function initTheme() {
    let initial = "dark";
    try {
      const stored = localStorage.getItem(THEME_KEY);
      if (stored === "light" || stored === "dark") initial = stored;
    } catch {
      /* ignore */
    }
    applyTheme(initial);
    themeBtn?.addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
    });
  }

  function showError(msg) {
    if (!errEl) return;
    errEl.textContent = msg;
    errEl.hidden = false;
  }

  function clearError() {
    if (!errEl) return;
    errEl.textContent = "";
    errEl.hidden = true;
  }

  async function redirectIfAlreadyLoggedIn() {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, { credentials: "include" });
      if (res.ok) {
        window.location.replace("/");
      }
    } catch {
      /* permanece na tela de login */
    }
  }

  form?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    clearError();
    const u = user?.value.trim() || "";
    const p = pass?.value || "";
    if (!u || !p) {
      showError("Informe usuário e senha.");
      return;
    }
    if (btn) btn.disabled = true;
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ username: u, password: p }),
      });
      const text = await res.text();
      if (!res.ok) {
        let msg = "Não foi possível entrar.";
        try {
          const j = JSON.parse(text);
          if (typeof j.detail === "string") msg = j.detail;
          else if (Array.isArray(j.detail)) msg = j.detail.map((x) => x.msg || x).join(" ");
        } catch {
          if (text) msg = text;
        }
        showError(msg);
        return;
      }
      window.location.href = "/";
    } catch (e) {
      showError(e instanceof Error ? e.message : "Erro de rede.");
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  initTheme();
  redirectIfAlreadyLoggedIn();
})();
