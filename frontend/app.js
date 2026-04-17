(() => {
  const API_BASE = "/api";
  const THEME_KEY = "emr-theme";

  const el = {
    connStatus: document.getElementById("conn-status"),
    robotList: document.getElementById("robot-list"),
    btnRefresh: document.getElementById("btn-refresh"),
    robotSearch: document.getElementById("robot-search"),
    newRobotDisclosure: document.getElementById("new-robot-disclosure"),
    formNewRobot: document.getElementById("form-new-robot"),
    newCode: document.getElementById("new-code"),
    newName: document.getElementById("new-name"),
    newLocation: document.getElementById("new-location"),
    newModel: document.getElementById("new-model"),
    newThroughput: document.getElementById("new-throughput"),
    btnNewRobot: document.getElementById("btn-new-robot"),
    toastRegion: document.getElementById("toast-region"),
    deleteModal: document.getElementById("delete-robot-modal"),
    deleteModalMessage: document.getElementById("delete-modal-message"),
    deleteModalConfirm: document.getElementById("delete-modal-confirm"),
    deleteModalCancel: document.getElementById("delete-modal-cancel"),
    deleteModalBackdrop: document.querySelector("#delete-robot-modal [data-modal-dismiss]"),
    editModal: document.getElementById("edit-robot-modal"),
    editModalBackdrop: document.querySelector("#edit-robot-modal [data-edit-modal-dismiss]"),
    formEditRobot: document.getElementById("form-edit-robot"),
    editRobotId: document.getElementById("edit-robot-id"),
    editCode: document.getElementById("edit-code"),
    editName: document.getElementById("edit-name"),
    editLocation: document.getElementById("edit-location"),
    editModel: document.getElementById("edit-model"),
    editModalCancel: document.getElementById("edit-modal-cancel"),
    editModalSave: document.getElementById("edit-modal-save"),
    themeToggle: document.getElementById("theme-toggle"),
    detailEmpty: document.getElementById("robot-detail-empty"),
    detailArticle: document.getElementById("robot-detail-article"),
    detailHeading: document.getElementById("robot-detail-heading"),
    detailMeta: document.getElementById("robot-detail-meta"),
    detailBadges: document.getElementById("robot-detail-badges"),
    detailOs: document.getElementById("robot-detail-os"),
    detailClient: document.getElementById("robot-detail-client"),
    detailUnits: document.getElementById("robot-detail-units"),
    detailElapsed: document.getElementById("robot-detail-elapsed"),
    detailStart: document.getElementById("robot-detail-start"),
    detailMedicinesBlock: document.getElementById("robot-detail-medicines-block"),
    detailMedicines: document.getElementById("robot-detail-medicines"),
    detailMedicinesEmpty: document.getElementById("robot-detail-medicines-empty"),
    detailCamera: document.getElementById("robot-detail-camera"),
  };

  let csrfToken = "";
  let selectedRobotId = null;
  let robotsCache = [];
  let robotSearchDebounce = null;
  let pendingDeleteRobot = null;
  let deleteModalPreviousFocus = null;
  let editModalPreviousFocus = null;
  let detailElapsedTimer = null;
  let detailJobStartedMs = null;
  let detailLoadSeq = 0;

  function formatApiDetail(detail) {
    if (detail == null) return "Erro na requisição.";
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail))
      return detail.map((x) => (typeof x === "string" ? x : x.msg || JSON.stringify(x))).join(" ");
    return String(detail);
  }

  function applyTheme(theme) {
    if (theme !== "light" && theme !== "dark") return;
    document.documentElement.setAttribute("data-theme", theme);
    try {
      localStorage.setItem(THEME_KEY, theme);
    } catch {
      /* ignore */
    }
    if (el.themeToggle) {
      el.themeToggle.setAttribute(
        "aria-label",
        theme === "dark"
          ? "Tema escuro (Softtek). Clique para tema claro (Apsen)."
          : "Tema claro (Apsen). Clique para tema escuro (Softtek).",
      );
    }
  }

  function initThemeToggle() {
    let initial = "dark";
    try {
      const stored = localStorage.getItem(THEME_KEY);
      if (stored === "light" || stored === "dark") initial = stored;
    } catch {
      /* ignore */
    }
    applyTheme(initial);
    el.themeToggle?.addEventListener("click", () => {
      const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
      applyTheme(next);
    });
  }

  function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = String(str);
    return d.innerHTML;
  }

  function closeDeleteModal() {
    pendingDeleteRobot = null;
    el.deleteModal.hidden = true;
    el.deleteModal.setAttribute("aria-hidden", "true");
    if (el.editModal.hidden) document.body.classList.remove("modal-open");
    if (deleteModalPreviousFocus && typeof deleteModalPreviousFocus.focus === "function") {
      try {
        deleteModalPreviousFocus.focus();
      } catch {
        /* ignore */
      }
    }
    deleteModalPreviousFocus = null;
  }

  function closeEditModal() {
    el.editModal.hidden = true;
    el.editModal.setAttribute("aria-hidden", "true");
    if (el.deleteModal.hidden) document.body.classList.remove("modal-open");
    if (editModalPreviousFocus && typeof editModalPreviousFocus.focus === "function") {
      try {
        editModalPreviousFocus.focus();
      } catch {
        /* ignore */
      }
    }
    editModalPreviousFocus = null;
  }

  async function openEditModal(robotId) {
    editModalPreviousFocus = document.activeElement;
    try {
      await fetchCsrf();
      const res = await fetch(`${API_BASE}/robots/${robotId}`);
      if (!res.ok) {
        toast("Não foi possível carregar o separador para edição.", "error");
        editModalPreviousFocus = null;
        return;
      }
      const d = await res.json();
      el.editRobotId.value = String(d.id);
      el.editCode.value = d.code || "";
      el.editName.value = d.name || "";
      el.editLocation.value = d.location || "";
      el.editModel.value = d.model || "";
      el.editModal.hidden = false;
      el.editModal.setAttribute("aria-hidden", "false");
      document.body.classList.add("modal-open");
      el.editCode.focus();
    } catch (e) {
      editModalPreviousFocus = null;
      toast(e instanceof Error ? e.message : "Erro ao abrir edição.", "error");
    }
  }

  function openDeleteModal(robot) {
    pendingDeleteRobot = robot;
    deleteModalPreviousFocus = document.activeElement;
    const name = escapeHtml(robot.name);
    const code = escapeHtml(robot.code);
    const os = robot.current_os_code ? escapeHtml(robot.current_os_code) : null;
    let html = `Você está prestes a excluir <strong>${name}</strong> (<strong>${code}</strong>).`;
    if (os) {
      html += ` A ordem de serviço <strong>${os}</strong> voltará para o status pendente.`;
    }
    html += " Esta ação não pode ser desfeita.";
    el.deleteModalMessage.innerHTML = html;
    el.deleteModal.hidden = false;
    el.deleteModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
    el.deleteModalCancel.focus();
  }

  function toast(message, type = "error") {
    const node = document.createElement("div");
    node.className = `toast toast--${type}`;
    node.textContent = message;
    el.toastRegion.appendChild(node);
    setTimeout(() => node.remove(), 6500);
  }

  async function fetchCsrf() {
    const res = await fetch(`${API_BASE}/csrf-token`);
    if (!res.ok) throw new Error("Falha ao obter token de segurança.");
    const data = await res.json();
    csrfToken = data.csrf_token;
  }

  async function apiJson(path, options = {}) {
    const headers = {
      Accept: "application/json",
      ...(options.headers || {}),
    };
    if (options.method && options.method !== "GET") {
      headers["Content-Type"] = "application/json";
      headers["X-CSRF-Token"] = csrfToken;
    }
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    return res;
  }

  function robotIsOnline(r) {
    if (typeof r.online === "boolean") return r.online;
    if (r.status === "offline") return false;
    return r.status === "idle" || r.status === "running";
  }

  function connectivityBadgeClass(online) {
    return online ? "badge--online" : "badge--offline";
  }

  function connectivityLabel(online) {
    return online ? "Online" : "Offline";
  }

  function clearDetailElapsedTimer() {
    if (detailElapsedTimer != null) {
      clearInterval(detailElapsedTimer);
      detailElapsedTimer = null;
    }
    detailJobStartedMs = null;
  }

  function formatExecutionStart(iso) {
    if (!iso) return "—";
    const dt = new Date(iso);
    if (Number.isNaN(dt.getTime())) return "—";
    return `Início: ${dt.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}`;
  }

  function formatElapsedSeconds(totalSec) {
    if (totalSec == null || totalSec < 0) return "—";
    const s = Math.floor(totalSec);
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const r = s % 60;
    if (h > 0) return `${h} h ${m} min ${r} s`;
    if (m > 0) return `${m} min ${r} s`;
    return `${r} s`;
  }

  function showDetailPlaceholder() {
    clearDetailElapsedTimer();
    el.detailEmpty.classList.remove("hidden");
    el.detailArticle.classList.add("hidden");
  }

  function startElapsedTicker(jobStartedAtIso) {
    clearDetailElapsedTimer();
    if (!jobStartedAtIso) return;
    const t = Date.parse(jobStartedAtIso);
    if (Number.isNaN(t)) return;
    detailJobStartedMs = t;
    const tick = () => {
      const sec = Math.max(0, Math.floor((Date.now() - detailJobStartedMs) / 1000));
      el.detailElapsed.textContent = formatElapsedSeconds(sec);
    };
    tick();
    detailElapsedTimer = setInterval(tick, 1000);
  }

  function renderRobotDetail(d) {
    el.detailEmpty.classList.add("hidden");
    el.detailArticle.classList.remove("hidden");
    if (el.detailCamera) el.detailCamera.value = "";

    el.detailHeading.textContent = d.name || "";
    const loc = d.location ? ` · ${d.location}` : "";
    el.detailMeta.textContent = `${d.code || ""}${loc}`;

    const running = d.status === "running";
    const online = typeof d.online === "boolean" ? d.online : robotIsOnline(d);

    el.detailBadges.innerHTML = "";
    const execBadge = document.createElement("span");
    execBadge.className = `badge ${running ? "badge--running" : "badge--idle"}`;
    execBadge.textContent = running ? "Em execução" : "Não em execução";
    el.detailBadges.appendChild(execBadge);

    const netBadge = document.createElement("span");
    netBadge.className = `badge ${connectivityBadgeClass(online)}`;
    netBadge.textContent = connectivityLabel(online);
    el.detailBadges.appendChild(netBadge);

    const ord = d.current_order;
    el.detailOs.textContent = ord?.os_code ?? "—";
    const client = ord?.client_name != null ? String(ord.client_name).trim() : "";
    el.detailClient.textContent = client || "—";

    if (ord) {
      el.detailMedicinesBlock.hidden = false;
      const meds = Array.isArray(ord.medicines) ? ord.medicines : [];
      el.detailMedicines.innerHTML = "";
      if (meds.length > 0) {
        el.detailMedicines.hidden = false;
        el.detailMedicinesEmpty.hidden = true;
        meds.forEach((item) => {
          const li = document.createElement("li");
          li.textContent = String(item);
          el.detailMedicines.appendChild(li);
        });
      } else {
        el.detailMedicines.hidden = true;
        el.detailMedicinesEmpty.hidden = false;
      }
    } else {
      el.detailMedicinesBlock.hidden = true;
      el.detailMedicines.innerHTML = "";
      el.detailMedicines.hidden = false;
      el.detailMedicinesEmpty.hidden = true;
    }

    if (ord) {
      const got = d.units_separated ?? 0;
      const total = ord.expected_units ?? 0;
      el.detailUnits.textContent = `${got} / ${total}`;
    } else {
      el.detailUnits.textContent = "—";
    }

    el.detailStart.textContent = formatExecutionStart(d.job_started_at);

    el.detailElapsed.textContent = "—";
    if (running && d.job_started_at) {
      startElapsedTicker(d.job_started_at);
    } else if (d.elapsed_seconds != null && d.elapsed_seconds >= 0) {
      el.detailElapsed.textContent = formatElapsedSeconds(d.elapsed_seconds);
    }
  }

  async function loadRobotDetail(robotId) {
    const seq = ++detailLoadSeq;
    try {
      const res = await fetch(`${API_BASE}/robots/${robotId}`);
      if (seq !== detailLoadSeq) return;
      if (!res.ok) {
        showDetailPlaceholder();
        toast(`Não foi possível carregar o separador (${res.status}).`, "error");
        return;
      }
      const d = await res.json();
      if (seq !== detailLoadSeq) return;
      renderRobotDetail(d);
    } catch (e) {
      if (seq !== detailLoadSeq) return;
      showDetailPlaceholder();
      toast(e instanceof Error ? e.message : "Erro ao carregar detalhes.", "error");
    }
  }

  function robotSearchQuery() {
    return el.robotSearch.value.trim();
  }

  function robotsListUrl() {
    const q = robotSearchQuery();
    const params = new URLSearchParams();
    if (q) params.set("name", q);
    const qs = params.toString();
    return `${API_BASE}/robots${qs ? `?${qs}` : ""}`;
  }

  function renderRobotList(robots) {
    robotsCache = robots;
    el.robotList.innerHTML = "";
    if (!robots.length) {
      const empty = document.createElement("li");
      empty.className = "robot-list__empty";
      empty.setAttribute("role", "presentation");
      empty.textContent = robotSearchQuery()
        ? "Nenhum separador encontrado para essa pesquisa. Tente outro termo ou limpe o campo."
        : "Nenhum separador ainda. Abra “Novo separador” abaixo e clique em Cadastrar.";
      el.robotList.appendChild(empty);
      return;
    }
    robots.forEach((r) => {
      const li = document.createElement("li");
      li.className = "robot-list__item";

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "robot-item";
      btn.setAttribute("role", "option");
      btn.setAttribute("aria-selected", r.id === selectedRobotId ? "true" : "false");
      btn.dataset.id = String(r.id);
      if (r.id === selectedRobotId) btn.classList.add("robot-item--active");

      const row = document.createElement("div");
      row.className = "robot-item__row";
      const name = document.createElement("span");
      name.className = "robot-item__name";
      name.textContent = r.name;
      const online = robotIsOnline(r);
      const st = document.createElement("span");
      st.className = `badge ${connectivityBadgeClass(online)}`;
      st.textContent = connectivityLabel(online);
      st.setAttribute("aria-label", online ? "Separador online" : "Separador offline");
      row.appendChild(name);
      row.appendChild(st);

      const code = document.createElement("div");
      code.className = "robot-item__code";
      const loc = r.location ? `${r.location}` : "";
      code.textContent = loc ? `${r.code} · ${loc}` : r.code;

      btn.appendChild(row);
      btn.appendChild(code);
      if (r.current_os_code) {
        const os = document.createElement("div");
        os.className = "robot-item__os";
        os.textContent = `OS: ${r.current_os_code}`;
        btn.appendChild(os);
      }
      btn.addEventListener("click", () => selectRobot(r.id));

      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "robot-item__delete";
      delBtn.setAttribute("aria-label", `Excluir separador ${r.name}`);
      delBtn.innerHTML =
        '<svg class="robot-item__delete-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" aria-hidden="true"><path stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6M10 11v6M14 11v6"/></svg>';
      delBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        openDeleteModal(r);
      });

      const editBtn = document.createElement("button");
      editBtn.type = "button";
      editBtn.className = "robot-item__edit";
      editBtn.setAttribute("aria-label", `Editar separador ${r.name}`);
      editBtn.innerHTML =
        '<svg class="robot-item__edit-icon" xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" aria-hidden="true"><path stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" d="M12 20h9M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>';
      editBtn.addEventListener("click", (ev) => {
        ev.stopPropagation();
        openEditModal(r.id);
      });

      const actions = document.createElement("div");
      actions.className = "robot-list__actions";
      actions.appendChild(editBtn);
      actions.appendChild(delBtn);

      li.appendChild(btn);
      li.appendChild(actions);
      el.robotList.appendChild(li);
    });
  }

  async function selectRobot(id) {
    selectedRobotId = id;
    renderRobotList(robotsCache);
    if (id != null) await loadRobotDetail(id);
  }

  async function loadRobots() {
    try {
      const res = await fetch(robotsListUrl());
      if (!res.ok) {
        const errBody = await res.text();
        throw new Error(errBody || `Lista falhou (${res.status})`);
      }
      const data = await res.json();
      if (!Array.isArray(data)) {
        throw new Error("Resposta inválida da API.");
      }
      renderRobotList(data);
      el.connStatus.textContent = "Conectado";
      el.connStatus.className = "badge badge--ok";
      if (selectedRobotId != null && !data.some((r) => r.id === selectedRobotId)) {
        selectedRobotId = null;
        renderRobotList(data);
        showDetailPlaceholder();
      } else if (selectedRobotId != null) {
        loadRobotDetail(selectedRobotId);
      } else {
        showDetailPlaceholder();
      }
    } catch (e) {
      el.connStatus.textContent = "Offline";
      el.connStatus.className = "badge badge--error";
      toast(
        e instanceof Error ? e.message : "Não foi possível contatar o servidor.",
        "error",
      );
    }
  }

  el.formNewRobot.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    await fetchCsrf();
    const body = {
      code: el.newCode.value.trim(),
      name: el.newName.value.trim(),
      location: el.newLocation.value.trim(),
      model: el.newModel.value.trim(),
      specifications: "",
      max_units_per_hour: parseInt(el.newThroughput.value, 10),
    };
    if (!body.code || !body.name) {
      toast("Código e nome são obrigatórios.", "error");
      return;
    }
    if (Number.isNaN(body.max_units_per_hour) || body.max_units_per_hour < 1) {
      toast("Capacidade inválida.", "error");
      return;
    }
    el.btnNewRobot.disabled = true;
    try {
      const res = await apiJson("/robots", {
        method: "POST",
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const text = await res.text();
        let msg = `Erro ${res.status}`;
        try {
          const err = JSON.parse(text);
          msg = formatApiDetail(err.detail) || text || msg;
        } catch {
          if (text) msg = text;
        }
        toast(msg, "error");
        return;
      }
      const data = await res.json();
      el.formNewRobot.reset();
      el.newThroughput.value = "500";
      el.newRobotDisclosure.open = false;
      await loadRobots();
      await selectRobot(data.id);
      const active = el.robotList.querySelector(".robot-item--active");
      active?.scrollIntoView({ block: "nearest", behavior: "smooth" });
      toast("Separador cadastrado.", "success");
    } catch (e) {
      toast(String(e.message || e), "error");
    } finally {
      el.btnNewRobot.disabled = false;
    }
  });

  el.btnRefresh.addEventListener("click", () => {
    loadRobots();
  });

  el.robotSearch.addEventListener("input", () => {
    clearTimeout(robotSearchDebounce);
    robotSearchDebounce = setTimeout(() => loadRobots(), 320);
  });

  el.deleteModalBackdrop.addEventListener("click", closeDeleteModal);
  el.deleteModalCancel.addEventListener("click", closeDeleteModal);

  el.editModalBackdrop.addEventListener("click", closeEditModal);
  el.editModalCancel.addEventListener("click", closeEditModal);

  el.formEditRobot.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const id = parseInt(el.editRobotId.value, 10);
    if (Number.isNaN(id)) return;
    const body = {
      code: el.editCode.value.trim(),
      name: el.editName.value.trim(),
      location: el.editLocation.value.trim(),
      model: el.editModel.value.trim(),
    };
    if (!body.code || !body.name) {
      toast("Código e nome são obrigatórios.", "error");
      return;
    }
    await fetchCsrf();
    el.editModalSave.disabled = true;
    try {
      const res = await apiJson(`/robots/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const text = await res.text();
        let msg = `Erro ${res.status}`;
        try {
          const err = JSON.parse(text);
          msg = formatApiDetail(err.detail) || text || msg;
        } catch {
          if (text) msg = text;
        }
        toast(msg, "error");
        return;
      }
      closeEditModal();
      toast("Separador atualizado.", "success");
      await loadRobots();
      if (selectedRobotId === id) await loadRobotDetail(id);
    } catch (e) {
      toast(String(e.message || e), "error");
    } finally {
      el.editModalSave.disabled = false;
    }
  });

  el.deleteModalConfirm.addEventListener("click", async () => {
    const r = pendingDeleteRobot;
    if (!r) return;
    el.deleteModalConfirm.disabled = true;
    try {
      await fetchCsrf();
      const res = await apiJson(`/robots/${r.id}`, { method: "DELETE" });
      if (!res.ok) {
        const text = await res.text();
        let errMsg = `Erro ${res.status}`;
        try {
          const err = JSON.parse(text);
          errMsg = formatApiDetail(err.detail) || text || errMsg;
        } catch {
          if (text) errMsg = text;
        }
        toast(errMsg, "error");
        return;
      }
      closeDeleteModal();
      if (selectedRobotId === r.id) {
        selectedRobotId = null;
        showDetailPlaceholder();
      }
      toast("Separador excluído.", "success");
      await loadRobots();
    } catch (e) {
      toast(String(e.message || e), "error");
    } finally {
      el.deleteModalConfirm.disabled = false;
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (!el.editModal.hidden) {
      e.preventDefault();
      closeEditModal();
      return;
    }
    if (!el.deleteModal.hidden) {
      e.preventDefault();
      closeDeleteModal();
    }
  });

  async function boot() {
    initThemeToggle();
    try {
      await fetchCsrf();
      await loadRobots();
    } catch (e) {
      el.connStatus.textContent = "Erro";
      el.connStatus.className = "badge badge--error";
      toast(String(e.message || e), "error");
    }
  }

  boot();
})();
