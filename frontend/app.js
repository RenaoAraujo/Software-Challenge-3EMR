(() => {
  const API_BASE = "/api";
  const THEME_KEY = "emr-theme";
  const SELECTED_ROBOT_KEY = "emr-selected-robot-id";
  /** Última aba (operação / histórico / relatório / logs) para restaurar após novo login na mesma sessão do navegador. */
  const LAST_APP_VIEW_KEY = "emr-last-app-view";
  /** Sub-aba em Relatório: os | separador */
  const LAST_RELATORIO_SUBTAB_KEY = "emr-relatorio-subtab";
  const RELATORIO_OS_LIMIT = 100;
  /** Último id de auditoria de OS concluída “visto” neste separador — badge = eventos com id maior. */
  const NOTIF_LAST_SEEN_KEY = "emr-notif-last-seen-id";
  /** Oculta na lista ids ≤ este valor após “Excluir” — novas conclusões (id maior) voltam a aparecer. */
  const NOTIF_DISMISSED_MAX_KEY = "emr-notif-dismissed-max-id";
  const NOTIF_POLL_INTERVAL_MS = 18000;
  const REMEDY_SIM_JOBS_KEY = "emr-remedy-sim-jobs";
  /** @deprecated migração — removidos após ler jobs novos */
  const REMEDY_SIM_ACTIVE_KEY = "emr-remedy-sim-active";
  const REMEDY_SIM_ROBOT_KEY = "emr-remedy-sim-robot-id";
  const REMEDY_SIM_TARGET_KEY = "emr-remedy-sim-target-units";
  const FETCH_CRED = { credentials: "include", cache: "no-store" };

  const el = {
    connStatus: document.getElementById("conn-status"),
    robotList: document.getElementById("robot-list"),
    btnRefresh: document.getElementById("btn-refresh"),
    btnOpenNewRobot: document.getElementById("btn-open-new-robot"),
    robotSearch: document.getElementById("robot-search"),
    newRobotModal: document.getElementById("new-robot-modal"),
    newRobotModalBackdrop: document.querySelector("#new-robot-modal [data-new-robot-modal-dismiss]"),
    newRobotModalCancel: document.getElementById("new-robot-modal-cancel"),
    formNewRobot: document.getElementById("form-new-robot"),
    newCode: document.getElementById("new-code"),
    newName: document.getElementById("new-name"),
    newLocation: document.getElementById("new-location"),
    newModel: document.getElementById("new-model"),
    btnNewRobot: document.getElementById("btn-new-robot"),
    toastRegion: document.getElementById("toast-region"),
    deleteModal: document.getElementById("delete-robot-modal"),
    deleteModalMessage: document.getElementById("delete-modal-message"),
    deleteModalConfirm: document.getElementById("delete-modal-confirm"),
    deleteModalCancel: document.getElementById("delete-modal-cancel"),
    deleteModalBackdrop: document.querySelector("#delete-robot-modal [data-modal-dismiss]"),
    clearLogsModal: document.getElementById("clear-logs-modal"),
    clearLogsModalBackdrop: document.querySelector("#clear-logs-modal [data-clear-logs-modal-dismiss]"),
    clearLogsModalCancel: document.getElementById("clear-logs-modal-cancel"),
    clearLogsModalConfirm: document.getElementById("clear-logs-modal-confirm"),
    editModal: document.getElementById("edit-robot-modal"),
    editModalBackdrop: document.querySelector("#edit-robot-modal [data-edit-modal-dismiss]"),
    formEditRobot: document.getElementById("form-edit-robot"),
    editRobotId: document.getElementById("edit-robot-id"),
    editCode: document.getElementById("edit-code"),
    editName: document.getElementById("edit-name"),
    editLocation: document.getElementById("edit-location"),
    editModel: document.getElementById("edit-model"),
    editStatus: document.getElementById("edit-status"),
    editStatusHint: document.getElementById("edit-status-hint"),
    editStatusLocked: document.getElementById("edit-status-locked"),
    editModalCancel: document.getElementById("edit-modal-cancel"),
    editModalSave: document.getElementById("edit-modal-save"),
    themeToggle: document.getElementById("theme-toggle"),
    headerNotif: document.getElementById("header-notif"),
    btnNotifications: document.getElementById("btn-notifications"),
    notifPanel: document.getElementById("notif-panel"),
    notifList: document.getElementById("notif-list"),
    notifEmpty: document.getElementById("notif-empty"),
    notifBadge: document.getElementById("notif-badge"),
    btnNotifClear: document.getElementById("btn-notif-clear"),
    btnProfile: document.getElementById("btn-profile"),
    profileDrawer: document.getElementById("profile-drawer"),
    profileDrawerBackdrop: document.getElementById("profile-drawer-backdrop"),
    profileDrawerClose: document.getElementById("profile-drawer-close"),
    profileUsernameDisplay: document.getElementById("profile-username-display"),
    profileDrawerTabs: document.getElementById("profile-drawer-tabs"),
    profileTabOwn: document.getElementById("profile-tab-own"),
    profileTabUser: document.getElementById("profile-tab-user"),
    profileTabNew: document.getElementById("profile-tab-new"),
    profilePanelOwn: document.getElementById("profile-panel-own"),
    profilePanelUser: document.getElementById("profile-panel-user"),
    profilePanelNew: document.getElementById("profile-panel-new"),
    profileUserSelect: document.getElementById("profile-user-select"),
    profileTargetPwd: document.getElementById("profile-target-pwd"),
    profileTargetAdmin: document.getElementById("profile-target-admin"),
    formProfileOwnPwd: document.getElementById("form-profile-own-pwd"),
    profileOwnCurrent: document.getElementById("profile-own-current"),
    profileOwnNew: document.getElementById("profile-own-new"),
    profileOwnNew2: document.getElementById("profile-own-new2"),
    formProfileTarget: document.getElementById("form-profile-target"),
    formProfileNewUser: document.getElementById("form-profile-new-user"),
    profileNewUsername: document.getElementById("profile-new-username"),
    profileNewPwd: document.getElementById("profile-new-pwd"),
    profileNewAdmin: document.getElementById("profile-new-admin"),
    btnLogout: document.getElementById("btn-logout"),
    detailEmpty: document.getElementById("robot-detail-empty"),
    detailArticle: document.getElementById("robot-detail-article"),
    detailHeading: document.getElementById("robot-detail-heading"),
    detailMeta: document.getElementById("robot-detail-meta"),
    detailBadges: document.getElementById("robot-detail-badges"),
    detailOs: document.getElementById("robot-detail-os"),
    detailClient: document.getElementById("robot-detail-client"),
    detailUnits: document.getElementById("robot-detail-units"),
    detailElapsed: document.getElementById("robot-detail-elapsed"),
    detailAvgPerMed: document.getElementById("robot-detail-avg-per-med"),
    detailOsProjection: document.getElementById("robot-detail-os-projection"),
    detailStart: document.getElementById("robot-detail-start"),
    detailActions: document.getElementById("robot-detail-actions"),
    btnPausarOs: document.getElementById("btn-pausar-os"),
    btnRetomarOs: document.getElementById("btn-retomar-os"),
    btnCancelarOs: document.getElementById("btn-cancelar-os"),
    tabOperacao: document.getElementById("tab-operacao"),
    tabHistorico: document.getElementById("tab-historico"),
    tabRelatorio: document.getElementById("tab-relatorio"),
    tabLogs: document.getElementById("tab-logs"),
    viewOperacao: document.getElementById("view-operacao"),
    operacaoColetivaGrid: document.getElementById("operacao-coletiva-grid"),
    viewHistorico: document.getElementById("view-historico"),
    viewRelatorio: document.getElementById("view-relatorio"),
    viewLogs: document.getElementById("view-logs"),
    logsResult: document.getElementById("logs-result"),
    btnLogsRefresh: document.getElementById("btn-logs-refresh"),
    btnLogsClear: document.getElementById("btn-logs-clear"),
    formLogsFilter: document.getElementById("form-logs-filter"),
    logsFilterUsername: document.getElementById("logs-filter-username"),
    logsFilterCategory: document.getElementById("logs-filter-category"),
    logsFilterDe: document.getElementById("logs-filter-de"),
    logsFilterAte: document.getElementById("logs-filter-ate"),
    logsPerPage: document.getElementById("logs-per-page"),
    btnLogsFilterClear: document.getElementById("btn-logs-filter-clear"),
    formHistorico: document.getElementById("form-historico"),
    historicoRobot: document.getElementById("historico-robot"),
    historicoDe: document.getElementById("historico-de"),
    historicoAte: document.getElementById("historico-ate"),
    historicoResult: document.getElementById("historico-result"),
    btnHistoricoConsultar: document.getElementById("btn-historico-consultar"),
    relatorioTabOs: document.getElementById("relatorio-tab-os"),
    relatorioTabSeparador: document.getElementById("relatorio-tab-separador"),
    relatorioPanelOs: document.getElementById("relatorio-panel-os"),
    relatorioPanelSeparador: document.getElementById("relatorio-panel-separador"),
    formRelatorioOs: document.getElementById("form-relatorio-os"),
    relatorioOsDe: document.getElementById("relatorio-os-de"),
    relatorioOsAte: document.getElementById("relatorio-os-ate"),
    relatorioOsFiltroOs: document.getElementById("relatorio-os-filtro-os"),
    relatorioOsCliente: document.getElementById("relatorio-os-cliente"),
    relatorioOsSituacao: document.getElementById("relatorio-os-situacao"),
    relatorioOsNomeSeparador: document.getElementById("relatorio-os-nome-separador"),
    relatorioOsCodigoSeparador: document.getElementById("relatorio-os-codigo-separador"),
    relatorioOsResult: document.getElementById("relatorio-os-result"),
    btnRelatorioOsConsultar: document.getElementById("btn-relatorio-os-consultar"),
    btnRelatorioOsLimpar: document.getElementById("btn-relatorio-os-limpar"),
    relatorioSeparadorBusca: document.getElementById("relatorio-separador-busca"),
    relatorioSeparadorResult: document.getElementById("relatorio-separador-result"),
    formManualOs: document.getElementById("form-manual-os"),
    manualOsCode: document.getElementById("manual-os-code"),
    manualOsClient: document.getElementById("manual-os-client"),
    manualOsRobot: document.getElementById("manual-os-robot"),
    manualOsQty: document.getElementById("manual-os-qty"),
    manualOsSimulate: document.getElementById("manual-os-simulate"),
    btnManualOsSubmit: document.getElementById("btn-manual-os-submit"),
    manualOsModal: document.getElementById("manual-os-modal"),
    manualOsModalBackdrop: document.querySelector("#manual-os-modal [data-manual-os-modal-dismiss]"),
    manualOsModalCancel: document.getElementById("manual-os-modal-cancel"),
    btnOpenManualOs: document.getElementById("btn-open-manual-os"),
  };

  let csrfToken = "";
  let currentUserIsAdmin = false;
  let currentUserId = null;
  let currentUsername = "";
  let profileUsersCache = [];
  let profileDrawerPreviousFocus = null;
  /** Painel ativo no perfil: own | user | new */
  let profileDrawerView = "own";
  let selectedRobotId = null;
  let robotsCache = [];
  let historicoRemediosChart = null;
  let historicoOsChart = null;
  let historicoTempoOsChart = null;
  let relatorioOsPageOffset = 0;
  const AUDIT_LOGS_LIMIT_KEY = "emr-audit-logs-limit";
  let auditLogsOffset = 0;
  let lastAuditLogsTotal = 0;
  let robotSearchDebounce = null;
  let pendingDeleteRobot = null;
  let deleteModalPreviousFocus = null;
  let editModalPreviousFocus = null;
  let newRobotModalPreviousFocus = null;
  let manualOsModalPreviousFocus = null;
  let notifItems = [];
  let notifBaselineDone = false;
  let notifPollTimer = null;
  let clearLogsModalPreviousFocus = null;
  let detailPollTimer = null;
  let detailPollRobotId = null;
  let listPollTimer = null;
  const LIST_POLL_INTERVAL_MS = 2500;
  let detailElapsedDisplayTimer = null;
  /** Só âncora servidor + Date.now() — evita depender do parse de job_started_at no cliente. */
  const detailElapsedSync = {
    anchorSec: 0,
    anchorAtMs: 0,
  };
  /** Unidades da OS exibida — o timer usa isso para média e projeção. */
  let detailLiveUnitGot = 0;
  let detailLiveUnitTotal = 0;
  /** Média por medicamento e projeção da OS só mudam quando `units_separated` aumenta (ou troca separador). */
  let detailPaceRobotId = null;
  let detailPaceFrozenAtUnits = null;
  let detailLoadSeq = 0;
  /** Timeout por separador — simulação de unidades (não usa setInterval fixo para respeitar pausa). */
  const remedySimTimers = new Map();
  /** Momento alvo (Date.now()) do próximo incremento; não é adiantado enquanto a OS está pausada. */
  const remedyNextDue = new Map();

  function migrateLegacyRemedySimStorage() {
    try {
      if (sessionStorage.getItem(REMEDY_SIM_JOBS_KEY) != null) return;
      if (sessionStorage.getItem(REMEDY_SIM_ACTIVE_KEY) !== "1") return;
      const rawId = sessionStorage.getItem(REMEDY_SIM_ROBOT_KEY);
      if (rawId == null) return;
      const id = parseInt(rawId, 10);
      if (Number.isNaN(id)) return;
      const rawT = sessionStorage.getItem(REMEDY_SIM_TARGET_KEY);
      let tgt = rawT != null ? parseInt(rawT, 10) : NaN;
      if (Number.isNaN(tgt) || tgt < 1) tgt = 50;
      sessionStorage.setItem(REMEDY_SIM_JOBS_KEY, JSON.stringify({ [String(id)]: { target: tgt } }));
      sessionStorage.removeItem(REMEDY_SIM_ACTIVE_KEY);
      sessionStorage.removeItem(REMEDY_SIM_ROBOT_KEY);
      sessionStorage.removeItem(REMEDY_SIM_TARGET_KEY);
    } catch {
      /* ignore */
    }
  }

  function readRemedySimJobs() {
    migrateLegacyRemedySimStorage();
    try {
      const raw = sessionStorage.getItem(REMEDY_SIM_JOBS_KEY);
      if (raw == null) return {};
      const o = JSON.parse(raw);
      return o && typeof o === "object" && !Array.isArray(o) ? o : {};
    } catch {
      return {};
    }
  }

  function writeRemedySimJobs(jobs) {
    try {
      const keys = Object.keys(jobs);
      if (keys.length === 0) sessionStorage.removeItem(REMEDY_SIM_JOBS_KEY);
      else sessionStorage.setItem(REMEDY_SIM_JOBS_KEY, JSON.stringify(jobs));
    } catch {
      /* ignore */
    }
  }

  function persistRemedySim(robotId, targetUnits) {
    const jobs = readRemedySimJobs();
    jobs[String(robotId)] = { target: Math.max(1, Number(targetUnits) || 1) };
    writeRemedySimJobs(jobs);
  }

  function removeRemedySimJob(robotId) {
    const jobs = readRemedySimJobs();
    delete jobs[String(robotId)];
    writeRemedySimJobs(jobs);
  }

  function clearAllRemedySimJobs() {
    try {
      sessionStorage.removeItem(REMEDY_SIM_JOBS_KEY);
      sessionStorage.removeItem(REMEDY_SIM_ACTIVE_KEY);
      sessionStorage.removeItem(REMEDY_SIM_ROBOT_KEY);
      sessionStorage.removeItem(REMEDY_SIM_TARGET_KEY);
    } catch {
      /* ignore */
    }
  }

  function clearRemedySimulationTimerFor(robotId) {
    const rid = Number(robotId);
    const h = remedySimTimers.get(rid);
    if (h != null) {
      clearTimeout(h);
      remedySimTimers.delete(rid);
    }
  }

  function clearAllRemedySimulationTimers() {
    for (const h of remedySimTimers.values()) {
      clearTimeout(h);
    }
    remedySimTimers.clear();
  }

  /** Sem argumento: para todas as simulações. Com id: só aquele separador. */
  function stopRemedySimulation(robotId) {
    if (robotId != null && robotId !== undefined && !Number.isNaN(Number(robotId))) {
      const rid = Number(robotId);
      removeRemedySimJob(rid);
      clearRemedySimulationTimerFor(rid);
      remedyNextDue.delete(rid);
      return;
    }
    clearAllRemedySimJobs();
    clearAllRemedySimulationTimers();
    remedyNextDue.clear();
  }

  function scheduleRemedySimulationStep(robotId, targetUnits) {
    const rid = Number(robotId);
    const tgt = Math.max(1, Number(targetUnits) || 1);
    clearRemedySimulationTimerFor(rid);
    let nd = remedyNextDue.get(rid);
    if (nd == null) {
      nd = Date.now() + 3000;
      remedyNextDue.set(rid, nd);
    }
    const delay = Math.max(0, nd - Date.now());
    const tid = setTimeout(() => {
      void remedySimulationStep(rid, tgt);
    }, delay);
    remedySimTimers.set(rid, tid);
  }

  async function remedySimulationStep(robotId, targetUnits) {
    const rid = Number(robotId);
    const tgt = Math.max(1, Number(targetUnits) || 1);
    const outcome = await runRemedySimulationTick(rid, tgt);
    if (outcome === "stopped") {
      return;
    }
    if (outcome === "paused") {
      const tid = setTimeout(() => {
        void remedySimulationStep(rid, tgt);
      }, 600);
      remedySimTimers.set(rid, tid);
      return;
    }
    if (outcome === "incremented") {
      remedyNextDue.set(rid, Date.now() + 3000);
    }
    scheduleRemedySimulationStep(rid, tgt);
  }

  function ensureRemedySimulationsRunning() {
    migrateLegacyRemedySimStorage();
    const jobs = readRemedySimJobs();
    for (const sid of Object.keys(jobs)) {
      const robotId = parseInt(sid, 10);
      if (Number.isNaN(robotId)) continue;
      if (remedySimTimers.has(robotId)) continue;
      const tgt = Math.max(1, Number(jobs[sid]?.target) || 1);
      if (!remedyNextDue.has(robotId)) {
        remedyNextDue.set(robotId, Date.now() + 3000);
      }
      scheduleRemedySimulationStep(robotId, tgt);
    }
  }

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
    /* Dois frames: garante que getComputedStyle já veja --accent / fills após data-theme */
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        applyHistoricoChartsThemeColors();
      });
    });
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

  /** Instante gravado em UTC na API: sem sufixo Z o JS interpreta como horário local. */
  function parseApiDateTimeAsUtc(iso) {
    if (iso == null || iso === "") return new Date(NaN);
    const s = String(iso).trim();
    if (/[zZ]$|[+-]\d{2}:\d{2}$/.test(s)) {
      return new Date(s);
    }
    const normalized = s.includes("T") ? s : s.replace(" ", "T");
    return new Date(`${normalized}Z`);
  }

  function resetEditStatusField() {
    el.editStatus?.querySelectorAll("option[data-temp-running]").forEach((o) => o.remove());
    if (el.editStatus) el.editStatus.disabled = false;
    if (el.editStatusLocked) el.editStatusLocked.hidden = true;
    if (el.editStatusHint) el.editStatusHint.hidden = false;
  }

  function setEditStatusFromRobot(d) {
    const sel = el.editStatus;
    if (!sel) return;
    sel.querySelectorAll("option[data-temp-running]").forEach((o) => o.remove());
    const busyWithOrder = d.status === "running" || d.status === "paused";
    if (el.editStatusLocked) el.editStatusLocked.hidden = !busyWithOrder;
    if (el.editStatusHint) el.editStatusHint.hidden = busyWithOrder;
    if (busyWithOrder) {
      const o = document.createElement("option");
      o.value = "__running__";
      o.textContent = d.status === "paused" ? "Pausado" : "Em execução";
      o.disabled = true;
      o.dataset.tempRunning = "1";
      sel.insertBefore(o, sel.firstChild);
      sel.value = "__running__";
      sel.disabled = true;
    } else {
      sel.disabled = false;
      const allowed = ["offline", "idle", "maintenance", "error"];
      sel.value = allowed.includes(d.status) ? d.status : "offline";
    }
  }

  function closeDeleteModal() {
    pendingDeleteRobot = null;
    el.deleteModal.hidden = true;
    el.deleteModal.setAttribute("aria-hidden", "true");
    if (
      el.editModal.hidden &&
      (!el.newRobotModal || el.newRobotModal.hidden) &&
      (!el.manualOsModal || el.manualOsModal.hidden) &&
      (!el.clearLogsModal || el.clearLogsModal.hidden)
    ) {
      document.body.classList.remove("modal-open");
    }
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
    resetEditStatusField();
    if (
      el.deleteModal.hidden &&
      (!el.newRobotModal || el.newRobotModal.hidden) &&
      (!el.manualOsModal || el.manualOsModal.hidden) &&
      (!el.clearLogsModal || el.clearLogsModal.hidden)
    ) {
      document.body.classList.remove("modal-open");
    }
    if (editModalPreviousFocus && typeof editModalPreviousFocus.focus === "function") {
      try {
        editModalPreviousFocus.focus();
      } catch {
        /* ignore */
      }
    }
    editModalPreviousFocus = null;
  }

  function closeNewRobotModal() {
    if (!el.newRobotModal) return;
    el.newRobotModal.hidden = true;
    el.newRobotModal.setAttribute("aria-hidden", "true");
    if (
      el.deleteModal.hidden &&
      el.editModal.hidden &&
      (!el.manualOsModal || el.manualOsModal.hidden) &&
      (!el.clearLogsModal || el.clearLogsModal.hidden)
    ) {
      document.body.classList.remove("modal-open");
    }
    if (newRobotModalPreviousFocus && typeof newRobotModalPreviousFocus.focus === "function") {
      try {
        newRobotModalPreviousFocus.focus();
      } catch {
        /* ignore */
      }
    }
    newRobotModalPreviousFocus = null;
  }

  async function openNewRobotModal() {
    if (!el.newRobotModal) return;
    if (el.manualOsModal && !el.manualOsModal.hidden) closeManualOsModal();
    newRobotModalPreviousFocus = document.activeElement;
    try {
      await fetchCsrf();
      el.formNewRobot?.reset();
      el.newRobotModal.hidden = false;
      el.newRobotModal.setAttribute("aria-hidden", "false");
      document.body.classList.add("modal-open");
      el.newCode?.focus();
    } catch (e) {
      newRobotModalPreviousFocus = null;
      toast(e instanceof Error ? e.message : "Erro ao abrir formulário.", "error");
    }
  }

  function closeManualOsModal() {
    if (!el.manualOsModal) return;
    el.manualOsModal.hidden = true;
    el.manualOsModal.setAttribute("aria-hidden", "true");
    if (
      el.deleteModal.hidden &&
      el.editModal.hidden &&
      (!el.newRobotModal || el.newRobotModal.hidden) &&
      (!el.clearLogsModal || el.clearLogsModal.hidden)
    ) {
      document.body.classList.remove("modal-open");
    }
    if (manualOsModalPreviousFocus && typeof manualOsModalPreviousFocus.focus === "function") {
      try {
        manualOsModalPreviousFocus.focus();
      } catch {
        /* ignore */
      }
    }
    manualOsModalPreviousFocus = null;
  }

  async function openManualOsModal() {
    if (!el.manualOsModal) return;
    if (el.newRobotModal && !el.newRobotModal.hidden) closeNewRobotModal();
    manualOsModalPreviousFocus = document.activeElement;
    try {
      await fetchCsrf();
      populateManualOsRobotSelect();
      el.formManualOs?.reset();
      if (el.manualOsQty) el.manualOsQty.value = "5";
      if (el.manualOsSimulate) el.manualOsSimulate.checked = true;
      el.manualOsModal.hidden = false;
      el.manualOsModal.setAttribute("aria-hidden", "false");
      document.body.classList.add("modal-open");
      el.manualOsCode?.focus();
    } catch (e) {
      manualOsModalPreviousFocus = null;
      toast(e instanceof Error ? e.message : "Erro ao abrir formulário.", "error");
    }
  }

  async function openEditModal(robotId) {
    editModalPreviousFocus = document.activeElement;
    try {
      await fetchCsrf();
      const res = await fetch(`${API_BASE}/robots/${robotId}`, FETCH_CRED);
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
      setEditStatusFromRobot(d);
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

  function closeClearLogsModal() {
    if (!el.clearLogsModal) return;
    el.clearLogsModal.hidden = true;
    el.clearLogsModal.setAttribute("aria-hidden", "true");
    if (
      el.deleteModal.hidden &&
      el.editModal.hidden &&
      (!el.newRobotModal || el.newRobotModal.hidden) &&
      (!el.manualOsModal || el.manualOsModal.hidden)
    ) {
      document.body.classList.remove("modal-open");
    }
    if (clearLogsModalPreviousFocus && typeof clearLogsModalPreviousFocus.focus === "function") {
      try {
        clearLogsModalPreviousFocus.focus();
      } catch {
        /* ignore */
      }
    }
    clearLogsModalPreviousFocus = null;
  }

  function openClearLogsModal() {
    if (!el.clearLogsModal) return;
    clearLogsModalPreviousFocus = document.activeElement;
    el.clearLogsModal.hidden = false;
    el.clearLogsModal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
    el.clearLogsModalCancel?.focus();
  }

  function toast(message, type = "error") {
    const node = document.createElement("div");
    node.className = `toast toast--${type}`;
    node.textContent = message;
    el.toastRegion.appendChild(node);
    setTimeout(() => node.remove(), 6500);
  }

  async function fetchCsrf() {
    const res = await fetch(`${API_BASE}/csrf-token`, FETCH_CRED);
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
    const res = await fetch(`${API_BASE}${path}`, {
      ...FETCH_CRED,
      ...options,
      headers,
    });
    return res;
  }

  function robotIsOnline(r) {
    if (typeof r.online === "boolean") return r.online;
    if (r.status === "offline") return false;
    return r.status === "idle" || r.status === "running" || r.status === "paused";
  }

  function connectivityBadgeClass(online) {
    return online ? "badge--online" : "badge--offline";
  }

  function connectivityLabel(online) {
    return online ? "Online" : "Offline";
  }

  function clearDetailPollTimer() {
    if (detailPollTimer != null) {
      clearInterval(detailPollTimer);
      detailPollTimer = null;
    }
    detailPollRobotId = null;
  }

  function clearDetailElapsedDisplayTimer() {
    if (detailElapsedDisplayTimer != null) {
      clearInterval(detailElapsedDisplayTimer);
      detailElapsedDisplayTimer = null;
    }
    detailElapsedSync.anchorSec = 0;
    detailElapsedSync.anchorAtMs = 0;
  }

  function detailViewMatchesRobot(d) {
    return selectedRobotId != null && Number(selectedRobotId) === Number(d.id);
  }

  function formatAvgSecondsPerMedicamento(sec) {
    if (sec == null || !Number.isFinite(sec) || sec < 0) return "—";
    const rounded = sec >= 100 ? Math.round(sec) : Math.round(sec * 10) / 10;
    const br = new Intl.NumberFormat("pt-BR", {
      minimumFractionDigits: sec >= 100 ? 0 : 1,
      maximumFractionDigits: sec >= 100 ? 0 : 1,
    }).format(rounded);
    return `${br} s`;
  }

  function resetDetailPaceMetricsState() {
    detailPaceRobotId = null;
    detailPaceFrozenAtUnits = null;
  }

  /**
   * Tempo médio por medicamento e projeção total da OS: só quando a contagem de unidades separadas muda.
   */
  function maybeUpdatePaceMetrics(d, elapsedSec) {
    const rid = d.id;
    if (detailPaceRobotId == null || Number(detailPaceRobotId) !== Number(rid)) {
      detailPaceRobotId = rid;
      detailPaceFrozenAtUnits = null;
    }
    const got = detailLiveUnitGot;
    const total = detailLiveUnitTotal;
    if (got < 1 || total <= 0 || elapsedSec == null || elapsedSec < 0) {
      detailPaceFrozenAtUnits = null;
      if (el.detailAvgPerMed) el.detailAvgPerMed.textContent = "—";
      if (el.detailOsProjection) el.detailOsProjection.textContent = "—";
      return;
    }
    if (detailPaceFrozenAtUnits === null || detailPaceFrozenAtUnits !== got) {
      const avgSec = elapsedSec / got;
      if (el.detailAvgPerMed) el.detailAvgPerMed.textContent = formatAvgSecondsPerMedicamento(avgSec);
      if (el.detailOsProjection) {
        const projected = Math.round(avgSec * total);
        el.detailOsProjection.textContent = formatElapsedSeconds(Math.max(0, projected));
      }
      detailPaceFrozenAtUnits = got;
    }
  }

  function resetDetailDerivedMetrics() {
    if (el.detailAvgPerMed) el.detailAvgPerMed.textContent = "—";
    if (el.detailOsProjection) el.detailOsProjection.textContent = "—";
    resetDetailPaceMetricsState();
  }

  function paintDetailElapsedDom() {
    if (!el.detailElapsed) return;
    const s = detailElapsedSync;
    const sec = Math.max(0, Math.floor(s.anchorSec + (Date.now() - s.anchorAtMs) / 1000));
    el.detailElapsed.textContent = formatElapsedSeconds(sec);
  }

  /**
   * Cronômetro: a cada render sincroniza com elapsed_seconds da API; entre polls soma o delta local.
   */
  function ensureDetailElapsedDisplay(d) {
    const ord = d.current_order;
    const active =
      ord != null &&
      d.job_started_at != null &&
      d.status === "running" &&
      detailViewMatchesRobot(d);

    if (!active) {
      clearDetailElapsedDisplayTimer();
      return;
    }

    const es = d.elapsed_seconds;
    detailElapsedSync.anchorSec = es != null && es >= 0 ? es : 0;
    detailElapsedSync.anchorAtMs = Date.now();

    paintDetailElapsedDom();

    if (detailElapsedDisplayTimer == null) {
      detailElapsedDisplayTimer = setInterval(paintDetailElapsedDom, 500);
    }
  }

  function persistSelectedRobotId(id) {
    try {
      if (id == null) sessionStorage.removeItem(SELECTED_ROBOT_KEY);
      else sessionStorage.setItem(SELECTED_ROBOT_KEY, String(id));
    } catch {
      /* ignore */
    }
  }

  /**
   * Enquanto houver OS em execução, consulta o backend periodicamente para atualizar
   * tempo decorrido (elapsed_seconds) e unidades — valores calculados no servidor.
   */
  function updateDetailPolling(d) {
    const robotId = d.id;
    const ord = d.current_order;
    const activeJob =
      d.status === "running" || d.status === "paused";
    const shouldPoll =
      ord != null &&
      d.job_started_at != null &&
      activeJob &&
      selectedRobotId != null &&
      Number(selectedRobotId) === Number(robotId);

    if (!shouldPoll) {
      clearDetailPollTimer();
      return;
    }

    if (detailPollTimer != null && detailPollRobotId === robotId) {
      return;
    }

    clearDetailPollTimer();
    detailPollRobotId = robotId;
    detailPollTimer = setInterval(() => {
      if (selectedRobotId == null || Number(selectedRobotId) !== Number(robotId)) {
        clearDetailPollTimer();
        return;
      }
      void loadRobotDetail(robotId);
    }, 1000);
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

  function formatOsActivityStatus(status) {
    if (status === "running") return "Em execução";
    if (status === "paused") return "Pausado";
    return "Em operação";
  }

  function renderOperacaoColetiva(robots) {
    const container = el.operacaoColetivaGrid;
    if (!container) return;
    const active = robots.filter((r) => r.current_os_code);
    if (!active.length) {
      container.innerHTML =
        '<p class="operacao-coletiva__empty" role="status">Nenhuma OS em andamento no momento — todos os separadores estão ociosos ou sem ordem vinculada.</p>';
      return;
    }
    active.sort((a, b) => String(a.name).localeCompare(String(b.name), "pt-BR"));
    container.innerHTML = active
      .map((r) => {
        const st = formatOsActivityStatus(r.status);
        const exp = r.expected_units != null ? r.expected_units : "—";
        const got = r.units_separated ?? 0;
        const client = (r.client_name && String(r.client_name).trim()) || "—";
        const elapsed =
          r.elapsed_seconds != null && r.elapsed_seconds >= 0
            ? formatElapsedSeconds(r.elapsed_seconds)
            : "—";
        const badgeClass = r.status === "paused" ? "badge--paused" : "badge--running";
        return `<article class="operacao-coletiva-card" role="listitem">
            <header class="operacao-coletiva-card__head">
              <span class="operacao-coletiva-card__name">${escapeHtml(r.name)}</span>
              <span class="badge ${badgeClass}">${escapeHtml(st)}</span>
            </header>
            <p class="operacao-coletiva-card__os"><strong>OS</strong> ${escapeHtml(String(r.current_os_code))}</p>
            <p class="operacao-coletiva-card__meta">${escapeHtml(client)}</p>
            <p class="operacao-coletiva-card__progress"><strong>${got}</strong> / ${escapeHtml(String(exp))} unidades</p>
            <p class="operacao-coletiva-card__time">Tempo: ${escapeHtml(elapsed)}</p>
          </article>`;
      })
      .join("");
  }

  function showDetailPlaceholder() {
    clearDetailPollTimer();
    clearDetailElapsedDisplayTimer();
    detailLiveUnitGot = 0;
    detailLiveUnitTotal = 0;
    resetDetailDerivedMetrics();
    el.detailEmpty.classList.remove("hidden");
    el.detailArticle.classList.add("hidden");
    if (el.detailActions) el.detailActions.hidden = true;
  }

  function initHistoricoDefaultDates() {
    if (!el.historicoDe || !el.historicoAte) return;
    const today = new Date();
    const first = new Date(today.getFullYear(), today.getMonth(), 1);
    const iso = (d) => {
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, "0");
      const day = String(d.getDate()).padStart(2, "0");
      return `${y}-${m}-${day}`;
    };
    el.historicoDe.value = iso(first);
    el.historicoAte.value = iso(today);
  }

  function getAuditLogsLimit() {
    const n = parseInt(el.logsPerPage?.value ?? "50", 10);
    if (n === 20 || n === 50 || n === 100) return n;
    return 50;
  }

  function initLogsPerPageFromStorage() {
    try {
      const v = localStorage.getItem(AUDIT_LOGS_LIMIT_KEY);
      if ((v === "20" || v === "50" || v === "100") && el.logsPerPage) el.logsPerPage.value = v;
    } catch (_) {
      /* ignore */
    }
  }

  function populateHistoricoRobotSelect() {
    if (!el.historicoRobot) return;
    const prev = el.historicoRobot.value;
    el.historicoRobot.innerHTML = "";
    const opt0 = document.createElement("option");
    opt0.value = "";
    opt0.textContent = "Selecione…";
    el.historicoRobot.appendChild(opt0);
    robotsCache.forEach((r) => {
      const opt = document.createElement("option");
      opt.value = String(r.id);
      opt.textContent = `${r.name} (${r.code})`;
      el.historicoRobot.appendChild(opt);
    });
    if (selectedRobotId != null) {
      el.historicoRobot.value = String(selectedRobotId);
    } else if (prev && robotsCache.some((x) => String(x.id) === prev)) {
      el.historicoRobot.value = prev;
    }
  }

  function populateManualOsRobotSelect() {
    if (!el.manualOsRobot) return;
    const prev = el.manualOsRobot.value;
    el.manualOsRobot.innerHTML = "";
    const opt0 = document.createElement("option");
    opt0.value = "";
    opt0.textContent = "Selecione…";
    el.manualOsRobot.appendChild(opt0);
    robotsCache.forEach((r) => {
      const opt = document.createElement("option");
      opt.value = String(r.id);
      const st = r.status || "";
      opt.textContent = `${r.name} (${r.code}) — ${st}`;
      el.manualOsRobot.appendChild(opt);
    });
    if (prev && robotsCache.some((x) => String(x.id) === prev)) {
      el.manualOsRobot.value = prev;
    }
  }

  /**
   * Simula +1 unidade. Devolve estado para o agendador manter o ciclo de 3 s mesmo após pausar/retomar.
   * @returns {"incremented"|"paused"|"stopped"}
   */
  async function runRemedySimulationTick(robotId, targetUnits) {
    try {
      await fetchCsrf();
      const res = await fetch(`${API_BASE}/robots/${robotId}`, FETCH_CRED);
      if (res.status === 401) {
        stopRemedySimulation();
        window.location.replace("/login.html");
        return "stopped";
      }
      if (!res.ok) {
        stopRemedySimulation(robotId);
        return "stopped";
      }
      const d = await res.json();
      if (!d.current_order) {
        stopRemedySimulation(robotId);
        return "stopped";
      }
      if (d.status === "paused") {
        return "paused";
      }
      if (d.status !== "running") {
        stopRemedySimulation(robotId);
        return "stopped";
      }
      const u = d.units_separated ?? 0;
      const total = d.current_order.expected_units ?? targetUnits;
      if (u >= total) {
        stopRemedySimulation(robotId);
        await loadRobots();
        if (selectedRobotId === robotId) await loadRobotDetail(robotId);
        return "stopped";
      }
      const next = u + 1;
      const patch = await apiJson(`/robots/${robotId}/units`, {
        method: "PATCH",
        body: JSON.stringify({ units_separated: next }),
      });
      if (!patch.ok) {
        stopRemedySimulation(robotId);
        const text = await patch.text();
        let msg = "Erro ao atualizar unidades.";
        try {
          const err = JSON.parse(text);
          msg = formatApiDetail(err.detail) || msg;
        } catch {
          /* ignore */
        }
        toast(msg, "error");
        return "stopped";
      }
      const data = await patch.json();
      if (data.status !== "running" || !data.current_order) {
        stopRemedySimulation(robotId);
        toast("Ordem concluída automaticamente ao atingir a meta de unidades.", "success");
        await loadRobots();
        if (selectedRobotId === robotId) await loadRobotDetail(robotId);
        return "stopped";
      }
      await loadRobots();
      if (selectedRobotId === robotId) await loadRobotDetail(robotId);
      return "incremented";
    } catch {
      stopRemedySimulation(robotId);
      return "stopped";
    }
  }

  function startRemedySimulation(robotId, targetUnits) {
    const rid = Number(robotId);
    const tgt = Math.max(1, Number(targetUnits) || 1);
    clearRemedySimulationTimerFor(rid);
    persistRemedySim(rid, tgt);
    /* Primeiro incremento após 3 s — mesmo critério de antes. */
    remedyNextDue.set(rid, Date.now() + 3000);
    scheduleRemedySimulationStep(rid, tgt);
  }

  /**
   * Mantém a lista de separadores (e o detalhe do selecionado) atualizada em qualquer aba —
   * Operação, Histórico ou Logs — para o cronômetro e unidades não “congelarem” ao consultar histórico.
   */
  function ensureOperacaoListPoll() {
    if (listPollTimer != null) return;
    listPollTimer = setInterval(() => {
      void loadRobots({ silent: true });
    }, LIST_POLL_INTERVAL_MS);
  }

  function readLastAppView() {
    try {
      const v = sessionStorage.getItem(LAST_APP_VIEW_KEY);
      if (v === "operacao" || v === "historico" || v === "relatorio" || v === "logs") return v;
    } catch {
      /* ignore */
    }
    return null;
  }

  function getRelatorioSubtab() {
    try {
      const s = sessionStorage.getItem(LAST_RELATORIO_SUBTAB_KEY);
      if (s === "os" || s === "separador") return s;
    } catch {
      /* ignore */
    }
    return "os";
  }

  function setRelatorioSubtab(which) {
    const wasOs = el.relatorioTabOs?.classList.contains("relatorio-subtab--active");
    const wasSep = el.relatorioTabSeparador?.classList.contains("relatorio-subtab--active");
    const isOs = which === "os";
    if (el.relatorioTabOs) {
      el.relatorioTabOs.classList.toggle("relatorio-subtab--active", isOs);
      el.relatorioTabOs.setAttribute("aria-selected", isOs ? "true" : "false");
      el.relatorioTabOs.tabIndex = isOs ? 0 : -1;
    }
    if (el.relatorioTabSeparador) {
      el.relatorioTabSeparador.classList.toggle("relatorio-subtab--active", !isOs);
      el.relatorioTabSeparador.setAttribute("aria-selected", !isOs ? "true" : "false");
      el.relatorioTabSeparador.tabIndex = !isOs ? 0 : -1;
    }
    if (el.relatorioPanelOs) {
      const show = isOs;
      el.relatorioPanelOs.classList.toggle("hidden", !show);
      if (show) el.relatorioPanelOs.removeAttribute("hidden");
      else el.relatorioPanelOs.setAttribute("hidden", "true");
    }
    if (el.relatorioPanelSeparador) {
      const show = !isOs;
      el.relatorioPanelSeparador.classList.toggle("hidden", !show);
      if (show) el.relatorioPanelSeparador.removeAttribute("hidden");
      else el.relatorioPanelSeparador.setAttribute("hidden", "true");
    }
    try {
      sessionStorage.setItem(LAST_RELATORIO_SUBTAB_KEY, which);
    } catch {
      /* ignore */
    }
    if (isOs && !wasOs) {
      void loadRelatorioOsList(true);
    }
    if (which === "separador" && !wasSep) {
      void loadRelatorioSeparadorList();
    }
  }

  function initRelatorioSubtabs() {
    setRelatorioSubtab(getRelatorioSubtab());
  }

  async function loadRelatorioOsList(resetOffset) {
    if (!el.relatorioOsResult) return;
    if (resetOffset) relatorioOsPageOffset = 0;
    const de = el.relatorioOsDe?.value?.trim() || "";
    const ate = el.relatorioOsAte?.value?.trim() || "";
    if ((de && !ate) || (!de && ate)) {
      toast("Preencha data inicial e final, ou deixe as duas em branco.", "error");
      return;
    }
    el.relatorioOsResult.innerHTML = '<p class="historico-empty" role="status">Carregando…</p>';
    if (el.btnRelatorioOsConsultar) el.btnRelatorioOsConsultar.disabled = true;
    try {
      const params = new URLSearchParams({
        limit: String(RELATORIO_OS_LIMIT),
        offset: String(relatorioOsPageOffset),
      });
      if (de && ate) {
        params.set("de", de);
        params.set("ate", ate);
      }
      const fo = el.relatorioOsFiltroOs?.value?.trim();
      if (fo) params.set("os", fo);
      const cl = el.relatorioOsCliente?.value?.trim();
      if (cl) params.set("cliente", cl);
      const sit = el.relatorioOsSituacao?.value?.trim();
      if (sit) params.set("situacao", sit);
      const nsep = el.relatorioOsNomeSeparador?.value?.trim();
      if (nsep) params.set("nome_separador", nsep);
      const csep = el.relatorioOsCodigoSeparador?.value?.trim();
      if (csep) params.set("codigo_separador", csep);
      const res = await fetch(`${API_BASE}/service-orders/completed?${params}`, FETCH_CRED);
      const text = await res.text();
      if (res.status === 401) {
        window.location.replace("/login.html");
        return;
      }
      if (!res.ok) {
        let msg = `Erro ${res.status}`;
        try {
          const err = JSON.parse(text);
          msg = formatApiDetail(err.detail) || text || msg;
        } catch {
          if (text) msg = text;
        }
        el.relatorioOsResult.innerHTML = "";
        toast(msg, "error");
        return;
      }
      const data = JSON.parse(text);
      renderRelatorioOsTable(data);
    } catch (e) {
      el.relatorioOsResult.innerHTML = "";
      toast(e instanceof Error ? e.message : "Falha ao carregar relatório.", "error");
    } finally {
      if (el.btnRelatorioOsConsultar) el.btnRelatorioOsConsultar.disabled = false;
    }
  }

  function clearRelatorioOsFilters() {
    if (el.relatorioOsDe) el.relatorioOsDe.value = "";
    if (el.relatorioOsAte) el.relatorioOsAte.value = "";
    if (el.relatorioOsFiltroOs) el.relatorioOsFiltroOs.value = "";
    if (el.relatorioOsCliente) el.relatorioOsCliente.value = "";
    if (el.relatorioOsSituacao) el.relatorioOsSituacao.value = "";
    if (el.relatorioOsNomeSeparador) el.relatorioOsNomeSeparador.value = "";
    if (el.relatorioOsCodigoSeparador) el.relatorioOsCodigoSeparador.value = "";
    relatorioOsPageOffset = 0;
    void loadRelatorioOsList(true);
  }

  function renderRelatorioOsTable(data) {
    if (!el.relatorioOsResult) return;
    const total = Number(data.total) || 0;
    const items = Array.isArray(data.items) ? data.items : [];
    const nf = new Intl.NumberFormat("pt-BR");
    const from = total === 0 ? 0 : relatorioOsPageOffset + 1;
    const to = relatorioOsPageOffset + items.length;
    const canPrev = relatorioOsPageOffset > 0;
    const canNext = to < total;
    if (items.length === 0) {
      el.relatorioOsResult.innerHTML =
        '<p class="historico-empty" role="status">Nenhuma OS encontrada para o filtro.</p>';
      return;
    }
    const rows = items
      .map((row) => {
        const rawData = row.data;
        const dataOnly =
          rawData != null && String(rawData).trim() !== ""
            ? new Date(`${String(rawData).slice(0, 10)}T12:00:00`).toLocaleDateString("pt-BR", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
              })
            : "—";
        const sep = row.separador_nome
          ? escapeHtml(String(row.separador_nome))
          : "Separador removido ou não identificado";
        const situacao =
          row.situacao === "cancelada"
            ? "Cancelada"
            : row.situacao === "concluida"
              ? "Concluída"
              : escapeHtml(String(row.situacao || "—"));
        return `<tr>
          <td class="logs-table__time">${dataOnly}</td>
          <td>${escapeHtml(String(row.os_code))}</td>
          <td>${escapeHtml(row.client_name ? String(row.client_name) : "—")}</td>
          <td>${sep}</td>
          <td>${nf.format(Number(row.unidades_totais) || 0)}</td>
          <td>${situacao}</td>
        </tr>`;
      })
      .join("");
    const showPager = canPrev || canNext;
    const pager = showPager
      ? `<div class="logs-pagination" role="navigation" aria-label="Páginas do relatório">
            <button type="button" class="btn btn--ghost btn--small" data-relatorio-os-page="prev" ${
              canPrev ? "" : "disabled"
            }>Anterior</button>
            <span class="logs-pagination__status">${formatHistoricoNum(from)}–${formatHistoricoNum(to)} de ${formatHistoricoNum(total)}</span>
            <button type="button" class="btn btn--ghost btn--small" data-relatorio-os-page="next" ${
              canNext ? "" : "disabled"
            }>Próxima</button>
          </div>`
      : `<p class="logs-table__meta">Mostrando ${formatHistoricoNum(from)}–${formatHistoricoNum(to)} de ${formatHistoricoNum(total)} no filtro.</p>`;
    el.relatorioOsResult.innerHTML = `
      <div class="logs-table-wrap" role="region" aria-label="Relatório de ordens encerradas" tabindex="0">
        <table class="logs-table">
          <thead>
            <tr>
              <th scope="col">Data</th>
              <th scope="col">OS</th>
              <th scope="col">Cliente</th>
              <th scope="col">Separador</th>
              <th scope="col">Unidades totais</th>
              <th scope="col">Situação</th>
            </tr>
          </thead>
          <tbody>${rows}</tbody>
        </table>
      </div>
      ${pager}`;
  }

  async function loadRelatorioSeparadorList() {
    if (!el.relatorioSeparadorResult) return;
    el.relatorioSeparadorResult.innerHTML =
      '<p class="historico-empty" role="status">Carregando…</p>';
    await loadRobots({ silent: true });
    renderRelatorioSeparadorList();
  }

  function renderRelatorioSeparadorList() {
    if (!el.relatorioSeparadorResult) return;
    let robots = Array.isArray(robotsCache) ? [...robotsCache] : [];
    const q = (el.relatorioSeparadorBusca?.value || "").trim().toLowerCase();
    if (q) {
      robots = robots.filter((r) => String(r.name || "").toLowerCase().includes(q));
    }
    robots.sort((a, b) => String(a.name).localeCompare(String(b.name), "pt-BR"));
    if (!robots.length) {
      el.relatorioSeparadorResult.innerHTML =
        '<p class="historico-empty" role="status">' +
          (q
            ? "Nenhum separador com esse nome."
            : "Nenhum separador cadastrado.") +
        "</p>";
      return;
    }
    const items = robots
      .map((r) => {
        const online = robotIsOnline(r);
        const badgeClass = connectivityBadgeClass(online);
        const badgeText = connectivityLabel(online);
        const loc = r.location ? escapeHtml(String(r.location)) : "";
        const codeLine = loc
          ? `${escapeHtml(String(r.code))} · ${loc}`
          : escapeHtml(String(r.code));
        return `<li class="relatorio-separador-list__item">
          <div class="relatorio-separador-card">
            <div class="relatorio-separador-card__head">
              <span class="relatorio-separador-card__name">${escapeHtml(String(r.name))}</span>
              <span class="badge ${badgeClass}" aria-label="${online ? "Separador online" : "Separador offline"}">${badgeText}</span>
            </div>
            <p class="relatorio-separador-card__meta">${codeLine}</p>
            <p class="relatorio-separador-card__model">${escapeHtml(String(r.model || "—"))}</p>
            <p class="relatorio-separador-card__status">${escapeHtml(formatOsActivityStatus(r.status))}</p>
          </div>
        </li>`;
      })
      .join("");
    el.relatorioSeparadorResult.innerHTML = `<ul class="relatorio-separador-list" role="list">${items}</ul>`;
  }

  function setAppView(view) {
    if (view === "logs" && !currentUserIsAdmin) {
      view = "operacao";
    }
    const isOp = view === "operacao";
    const isHist = view === "historico";
    const isRel = view === "relatorio";
    const isLogs = view === "logs";
    if (el.viewOperacao) el.viewOperacao.classList.toggle("hidden", !isOp);
    if (el.viewHistorico) el.viewHistorico.classList.toggle("hidden", !isHist);
    if (el.viewRelatorio) el.viewRelatorio.classList.toggle("hidden", !isRel);
    if (el.viewLogs) el.viewLogs.classList.toggle("hidden", !isLogs);
    if (el.tabOperacao) {
      el.tabOperacao.classList.toggle("app-nav__tab--active", isOp);
      el.tabOperacao.setAttribute("aria-selected", isOp ? "true" : "false");
    }
    if (el.tabHistorico) {
      el.tabHistorico.classList.toggle("app-nav__tab--active", isHist);
      el.tabHistorico.setAttribute("aria-selected", isHist ? "true" : "false");
    }
    if (el.tabRelatorio) {
      el.tabRelatorio.classList.toggle("app-nav__tab--active", isRel);
      el.tabRelatorio.setAttribute("aria-selected", isRel ? "true" : "false");
    }
    if (el.tabLogs) {
      el.tabLogs.classList.toggle("app-nav__tab--active", isLogs);
      el.tabLogs.setAttribute("aria-selected", isLogs ? "true" : "false");
    }
    try {
      sessionStorage.setItem(LAST_APP_VIEW_KEY, view);
    } catch {
      /* ignore */
    }
    ensureOperacaoListPoll();
    if (isOp) {
      void loadRobots({ silent: true });
    }
    if (isHist) populateHistoricoRobotSelect();
    if (isLogs) void loadAuditLogs();
    if (isRel && getRelatorioSubtab() === "os") {
      void loadRelatorioOsList(true);
    }
    if (isRel && getRelatorioSubtab() === "separador") {
      void loadRelatorioSeparadorList();
    }
  }

  function readNotifLastSeenId() {
    try {
      const v = sessionStorage.getItem(NOTIF_LAST_SEEN_KEY);
      if (v == null) return null;
      const n = parseInt(v, 10);
      return Number.isFinite(n) ? n : null;
    } catch {
      return null;
    }
  }

  function writeNotifLastSeenId(id) {
    try {
      sessionStorage.setItem(NOTIF_LAST_SEEN_KEY, String(id));
    } catch {
      /* ignore */
    }
  }

  function readNotifDismissedMaxId() {
    try {
      const v = sessionStorage.getItem(NOTIF_DISMISSED_MAX_KEY);
      if (v == null) return 0;
      const n = parseInt(v, 10);
      return Number.isFinite(n) && n > 0 ? n : 0;
    } catch {
      return 0;
    }
  }

  function writeNotifDismissedMaxId(id) {
    try {
      sessionStorage.setItem(NOTIF_DISMISSED_MAX_KEY, String(id));
    } catch {
      /* ignore */
    }
  }

  function notifVisibleItems() {
    const d = readNotifDismissedMaxId();
    return notifItems.filter((i) => i.id > d);
  }

  function maxNotifId(items) {
    if (!items.length) return 0;
    return Math.max(...items.map((x) => x.id));
  }

  function isNotifPanelOpen() {
    return el.notifPanel != null && !el.notifPanel.hidden;
  }

  function setNotifPanelOpen(open) {
    if (!el.notifPanel || !el.btnNotifications) return;
    el.notifPanel.hidden = !open;
    el.btnNotifications.setAttribute("aria-expanded", open ? "true" : "false");
    el.headerNotif?.classList.toggle("header-notif--open", open);
    if (open) {
      const mx = maxNotifId(notifItems);
      writeNotifLastSeenId(mx);
      updateNotifBadge();
    }
  }

  function toggleNotifPanel() {
    setNotifPanelOpen(!isNotifPanelOpen());
  }

  function updateNotifBadge() {
    if (!el.notifBadge) return;
    const lastSeen = readNotifLastSeenId() ?? 0;
    const unread = notifItems.filter((i) => i.id > lastSeen).length;
    if (unread > 0) {
      el.notifBadge.textContent = unread > 99 ? "99+" : String(unread);
      el.notifBadge.hidden = false;
    } else {
      el.notifBadge.hidden = true;
    }
  }

  function formatNotifWhen(iso) {
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return "—";
      return d.toLocaleString("pt-BR", {
        timeZone: "America/Sao_Paulo",
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "—";
    }
  }

  function renderNotifList() {
    if (!el.notifList || !el.notifEmpty) return;
    const visible = notifVisibleItems();
    if (el.btnNotifClear) {
      el.btnNotifClear.disabled = visible.length === 0;
    }
    if (!notifItems.length) {
      el.notifEmpty.textContent = "Nenhuma conclusão recente.";
      el.notifEmpty.hidden = false;
      el.notifList.hidden = true;
      el.notifList.innerHTML = "";
      return;
    }
    if (!visible.length) {
      el.notifEmpty.textContent = "Lista limpa. Novas conclusões aparecerão aqui.";
      el.notifEmpty.hidden = false;
      el.notifList.hidden = true;
      el.notifList.innerHTML = "";
      return;
    }
    el.notifEmpty.hidden = true;
    el.notifList.hidden = false;
    el.notifList.innerHTML = visible
      .map((it) => {
        const desc = escapeHtml(String(it.description || "").trim() || "(sem descrição)");
        const user = escapeHtml(String(it.username || "—"));
        const when = formatNotifWhen(it.created_at);
        return `<li class="header-notif__item"><div>${desc}</div><div class="header-notif__item-meta"><span>${when}</span><span>${user}</span></div></li>`;
      })
      .join("");
  }

  function clearNotificationsFromPanel() {
    if (!notifItems.length) return;
    const mx = maxNotifId(notifItems);
    writeNotifLastSeenId(mx);
    writeNotifDismissedMaxId(mx);
    updateNotifBadge();
    renderNotifList();
  }

  async function fetchNotifications() {
    if (!el.notifPanel) return;
    try {
      const res = await fetch(`${API_BASE}/notifications/os-completions?limit=40`, FETCH_CRED);
      if (res.status === 401) return;
      if (!res.ok) return;
      const data = await res.json();
      const items = Array.isArray(data.items) ? data.items : [];
      notifItems = items;

      if (readNotifLastSeenId() === null && !notifBaselineDone) {
        notifBaselineDone = true;
        writeNotifLastSeenId(maxNotifId(items));
      } else {
        notifBaselineDone = true;
      }

      if (isNotifPanelOpen()) {
        writeNotifLastSeenId(maxNotifId(notifItems));
      }

      renderNotifList();
      updateNotifBadge();
    } catch {
      if (el.notifEmpty && el.notifEmpty.textContent === "Carregando…") {
        el.notifEmpty.textContent = "Não foi possível carregar.";
      }
    }
  }

  function ensureNotificationsPoll() {
    if (notifPollTimer != null) return;
    notifPollTimer = setInterval(() => {
      void fetchNotifications();
    }, NOTIF_POLL_INTERVAL_MS);
  }

  function isProfileDrawerOpen() {
    return el.profileDrawer != null && !el.profileDrawer.hidden;
  }

  function syncProfileSheetTop() {
    const hdr = document.querySelector(".header");
    const top = hdr ? Math.ceil(hdr.getBoundingClientRect().bottom) : 0;
    document.documentElement.style.setProperty("--profile-sheet-top", `${top}px`);
  }

  function onProfileDrawerLayoutTick() {
    if (!isProfileDrawerOpen()) return;
    syncProfileSheetTop();
  }

  function updateProfileDrawerTabsForRole() {
    const admin = currentUserIsAdmin;
    el.profileTabUser?.classList.toggle("hidden", !admin);
    el.profileTabNew?.classList.toggle("hidden", !admin);
    if (!admin && profileDrawerView !== "own") {
      profileDrawerView = "own";
    }
  }

  function setProfileDrawerView(view) {
    let v = view;
    if ((v === "user" || v === "new") && !currentUserIsAdmin) {
      v = "own";
    }
    profileDrawerView = v;
    const rows = [
      ["own", el.profileTabOwn, el.profilePanelOwn],
      ["user", el.profileTabUser, el.profilePanelUser],
      ["new", el.profileTabNew, el.profilePanelNew],
    ];
    for (const [id, tab, panel] of rows) {
      const on = id === profileDrawerView;
      if (tab) {
        tab.classList.toggle("profile-drawer__tab--active", on);
        tab.setAttribute("aria-selected", on ? "true" : "false");
        tab.tabIndex = on ? 0 : -1;
      }
      if (panel) {
        if (on) {
          panel.removeAttribute("hidden");
          panel.classList.remove("hidden");
        } else {
          panel.setAttribute("hidden", "true");
          panel.classList.add("hidden");
        }
      }
    }
  }

  function openProfileDrawer() {
    if (!el.profileDrawer || !el.profileDrawerBackdrop) return;
    syncProfileSheetTop();
    window.addEventListener("resize", onProfileDrawerLayoutTick);
    window.addEventListener("scroll", onProfileDrawerLayoutTick, true);
    profileDrawerPreviousFocus = document.activeElement;
    el.profileDrawer.hidden = false;
    el.profileDrawerBackdrop.hidden = false;
    el.profileDrawer.setAttribute("aria-hidden", "false");
    el.profileDrawerBackdrop.setAttribute("aria-hidden", "false");
    el.btnProfile?.setAttribute("aria-expanded", "true");
    requestAnimationFrame(() => {
      document.body.classList.add("profile-drawer-open");
    });
    if (el.profileUsernameDisplay) el.profileUsernameDisplay.textContent = currentUsername || "—";
    profileDrawerView = "own";
    updateProfileDrawerTabsForRole();
    setProfileDrawerView("own");
    if (currentUserIsAdmin) {
      void loadProfileUserListForDrawer();
    }
    el.profileDrawerClose?.focus();
  }

  function closeProfileDrawer() {
    if (!el.profileDrawer || !el.profileDrawerBackdrop) return;
    window.removeEventListener("resize", onProfileDrawerLayoutTick);
    window.removeEventListener("scroll", onProfileDrawerLayoutTick, true);
    document.documentElement.style.removeProperty("--profile-sheet-top");
    document.body.classList.remove("profile-drawer-open");
    el.profileDrawer.hidden = true;
    el.profileDrawerBackdrop.hidden = true;
    el.profileDrawer.setAttribute("aria-hidden", "true");
    el.profileDrawerBackdrop.setAttribute("aria-hidden", "true");
    el.btnProfile?.setAttribute("aria-expanded", "false");
    if (profileDrawerPreviousFocus && typeof profileDrawerPreviousFocus.focus === "function") {
      try {
        profileDrawerPreviousFocus.focus();
      } catch {
        /* ignore */
      }
    }
    profileDrawerPreviousFocus = null;
  }

  function syncProfileTargetFromSelect() {
    if (!el.profileUserSelect || !el.profileTargetAdmin) return;
    const id = parseInt(el.profileUserSelect.value, 10);
    const u = profileUsersCache.find((x) => Number(x.id) === id);
    if (u) el.profileTargetAdmin.checked = Boolean(u.is_admin);
    if (el.profileTargetPwd) el.profileTargetPwd.value = "";
  }

  async function loadProfileUserListForDrawer() {
    if (!el.profileUserSelect || !currentUserIsAdmin) return;
    try {
      const res = await fetch(`${API_BASE}/admin/users`, FETCH_CRED);
      if (res.status === 401) return;
      if (!res.ok) {
        el.profileUserSelect.innerHTML = '<option value="">Erro ao carregar</option>';
        return;
      }
      const data = await res.json();
      profileUsersCache = Array.isArray(data.users) ? data.users : [];
      el.profileUserSelect.innerHTML = profileUsersCache
        .map((u) => {
          const label = `${u.username}${u.is_admin ? " (admin)" : ""}`;
          return `<option value="${u.id}">${escapeHtml(label)}</option>`;
        })
        .join("");
      if (currentUserId != null) {
        const sid = String(currentUserId);
        const has = profileUsersCache.some((u) => String(u.id) === sid);
        if (has) el.profileUserSelect.value = sid;
      }
      syncProfileTargetFromSelect();
    } catch {
      if (el.profileUserSelect) el.profileUserSelect.innerHTML = '<option value="">—</option>';
    }
  }

  async function refreshSessionUserFromMe() {
    try {
      const me = await fetch(`${API_BASE}/auth/me`, FETCH_CRED);
      if (!me.ok) return;
      const meData = await me.json();
      applyAdminUiFromSession(meData.user?.is_admin);
      currentUserId = meData.user?.id != null ? Number(meData.user.id) : null;
      currentUsername = meData.user?.username != null ? String(meData.user.username) : "";
      if (el.profileUsernameDisplay && isProfileDrawerOpen()) {
        el.profileUsernameDisplay.textContent = currentUsername || "—";
      }
    } catch {
      /* ignore */
    }
  }

  function applyAdminUiFromSession(isAdmin) {
    currentUserIsAdmin = Boolean(isAdmin);
    if (el.tabLogs) {
      if (currentUserIsAdmin) {
        el.tabLogs.classList.remove("hidden");
        el.tabLogs.removeAttribute("hidden");
      } else {
        el.tabLogs.classList.add("hidden");
        el.tabLogs.setAttribute("hidden", "true");
      }
    }
    updateProfileDrawerTabsForRole();
    setProfileDrawerView(profileDrawerView);
    if (!currentUserIsAdmin && el.viewLogs && !el.viewLogs.classList.contains("hidden")) {
      setAppView("operacao");
    }
  }

  function auditActionLabel(action) {
    const m = {
      login: "Login",
      logout: "Logout",
      view_historico: "Histórico (separador)",
      view_logs: "Logs de auditoria",
      os_started: "OS iniciada",
      os_completed: "OS terminada (concluída manual)",
      os_cancelled: "OS terminada (cancelada)",
      os_paused: "OS pausada",
      os_resumed: "OS retomada",
      os_completed_auto: "OS terminada (concluída automática)",
      password_changed_self: "Alterou a própria senha",
      password_changed_by_admin: "Alterou senha de outro usuário",
      user_created: "Cadastrou usuário",
      user_promoted_admin: "Promoveu a administrador",
      user_demoted_admin: "Removeu perfil de administrador",
      user_updated_by_admin: "Alterou outro usuário (admin)",
    };
    return m[action] || action;
  }

  function buildAuditLogsQuery() {
    const params = new URLSearchParams();
    params.set("limit", String(getAuditLogsLimit()));
    params.set("offset", String(auditLogsOffset));
    const u = el.logsFilterUsername?.value?.trim();
    const cat = el.logsFilterCategory?.value?.trim();
    const de = el.logsFilterDe?.value?.trim();
    const ate = el.logsFilterAte?.value?.trim();
    if (u) params.set("username", u);
    if (cat) params.set("category", cat);
    if (de) params.set("de", de);
    if (ate) params.set("ate", ate);
    return params.toString();
  }

  async function loadAuditLogs() {
    if (!el.logsResult || !currentUserIsAdmin) return;
    const de = el.logsFilterDe?.value?.trim();
    const ate = el.logsFilterAte?.value?.trim();
    if (de && ate && de > ate) {
      toast("A data inicial não pode ser depois da final.", "error");
      return;
    }
    el.logsResult.innerHTML = '<p class="historico-empty" role="status">Carregando…</p>';
    try {
      const q = buildAuditLogsQuery();
      const res = await fetch(`${API_BASE}/admin/audit-logs?${q}`, FETCH_CRED);
      if (res.status === 401) {
        window.location.replace("/login.html");
        return;
      }
      if (res.status === 403) {
        el.logsResult.innerHTML =
          '<p class="historico-empty">Sem permissão para ver os logs. Use uma conta de administrador.</p>';
        return;
      }
      if (!res.ok) {
        el.logsResult.innerHTML = "";
        toast(`Erro ${res.status} ao carregar logs.`, "error");
        return;
      }
      const data = await res.json();
      const total = Number(data.total) || 0;
      lastAuditLogsTotal = total;
      const rows = data.items || [];
      const lim = getAuditLogsLimit();

      if (total === 0 && rows.length === 0) {
        el.logsResult.innerHTML =
          '<p class="historico-empty">Nenhum registro corresponde a estes filtros (ou ainda não há logs).</p>';
        return;
      }

      if (rows.length === 0 && total > 0 && auditLogsOffset >= total) {
        auditLogsOffset = Math.max(0, Math.floor((total - 1) / lim) * lim);
        void loadAuditLogs();
        return;
      }

      const from = rows.length ? auditLogsOffset + 1 : 0;
      const to = auditLogsOffset + rows.length;
      const canPrev = auditLogsOffset > 0;
      const canNext = auditLogsOffset + lim < total;
      const pageCount = Math.max(1, Math.ceil(total / lim));
      const pageNum = Math.min(pageCount, Math.floor(auditLogsOffset / lim) + 1);
      const showPager = pageCount > 1;
      const rangeText = rows.length
        ? `Mostrando ${formatHistoricoNum(from)}–${formatHistoricoNum(to)} de ${formatHistoricoNum(total)} correspondentes ao filtro (${formatHistoricoNum(lim)} por página).`
        : "";

      el.logsResult.innerHTML = `
        <div class="logs-table-wrap" role="region" aria-label="Registros de auditoria" tabindex="0">
          <table class="logs-table">
            <thead>
              <tr>
                <th scope="col">Data e hora</th>
                <th scope="col">Usuário</th>
                <th scope="col">Tipo</th>
                <th scope="col">Descrição</th>
              </tr>
            </thead>
            <tbody>
              ${rows
                .map(
                  (r) => `
                <tr>
                  <td class="logs-table__time">${escapeHtml(
                    parseApiDateTimeAsUtc(r.created_at).toLocaleString("pt-BR", {
                      dateStyle: "short",
                      timeStyle: "medium",
                    }),
                  )}</td>
                  <td>${escapeHtml(r.username)}</td>
                  <td><span class="logs-table__action">${escapeHtml(auditActionLabel(r.action))}</span></td>
                  <td>${escapeHtml(r.description)}</td>
                </tr>`,
                )
                .join("")}
            </tbody>
          </table>
          ${
            showPager
              ? `<div class="logs-pagination" role="navigation" aria-label="Paginação dos logs">
            <button type="button" class="btn btn--ghost btn--small" data-audit-logs-page="prev" ${
              canPrev ? "" : "disabled"
            }>Anterior</button>
            <span class="logs-pagination__status">Página ${formatHistoricoNum(pageNum)} de ${formatHistoricoNum(pageCount)}</span>
            <button type="button" class="btn btn--ghost btn--small" data-audit-logs-page="next" ${
              canNext ? "" : "disabled"
            }>Próxima</button>
          </div>`
              : ""
          }
          <p class="logs-table__meta">${rangeText}</p>
        </div>`;
    } catch (e) {
      el.logsResult.innerHTML = "";
      toast(e instanceof Error ? e.message : "Falha ao carregar logs.", "error");
    }
  }

  function formatHistoricoNum(n) {
    if (n == null || Number.isNaN(n)) return "—";
    return new Intl.NumberFormat("pt-BR").format(n);
  }

  function destroyHistoricoCharts() {
    if (historicoRemediosChart) {
      historicoRemediosChart.destroy();
      historicoRemediosChart = null;
    }
    if (historicoOsChart) {
      historicoOsChart.destroy();
      historicoOsChart = null;
    }
    if (historicoTempoOsChart) {
      historicoTempoOsChart.destroy();
      historicoTempoOsChart = null;
    }
  }

  function historicoCssVar(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }

  function applyHistoricoChartsThemeColors() {
    const grid = historicoCssVar("--historico-chart-grid", "rgba(128, 128, 128, 0.15)");
    const tick = historicoCssVar("--text-muted", "#888");
    function patch(chart) {
      if (!chart || !chart._historicoTheme) return;
      const { lineVar, fillVar } = chart._historicoTheme;
      const line = historicoCssVar(lineVar, "#0082df");
      const fill = historicoCssVar(fillVar, line);
      const ds = chart.data.datasets[0];
      ds.borderColor = line;
      ds.backgroundColor = fill;
      ds.pointBackgroundColor = line;
      ds.pointBorderColor = line;
      ds.pointHoverBackgroundColor = line;
      ds.pointHoverBorderColor = line;
      if (!chart.options.elements) chart.options.elements = {};
      if (!chart.options.elements.point) chart.options.elements.point = {};
      const pt = chart.options.elements.point;
      pt.backgroundColor = line;
      pt.borderColor = line;
      pt.hoverBackgroundColor = line;
      pt.hoverBorderColor = line;
      if (chart.options?.scales?.x) {
        chart.options.scales.x.grid.color = grid;
        chart.options.scales.x.ticks.color = tick;
      }
      if (chart.options?.scales?.y) {
        chart.options.scales.y.grid.color = grid;
        chart.options.scales.y.ticks.color = tick;
      }
      /* update() sem modo redesenha cores; 'none' pode não refletir troca de tema */
      chart.update();
    }
    patch(historicoRemediosChart);
    patch(historicoOsChart);
    patch(historicoTempoOsChart);
  }

  /**
   * @param {string} canvasId
   * @param {unknown[]} serie
   * @param {{ valueKey: string; datasetLabel: string; lineColorVar: string; fillColorVar: string; formatTooltip: (v: number) => string; nullableValues?: boolean; yTickPrecision?: number }} opts
   */
  function createHistoricoAreaChart(canvasId, serie, opts) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || typeof window.Chart === "undefined") return null;
    const points = Array.isArray(serie) ? serie : [];
    const nullableY = Boolean(opts.nullableValues);
    const yPrec = opts.yTickPrecision != null ? opts.yTickPrecision : 0;
    const labels = points.map((p) => {
      const raw = p.data;
      const d = new Date(typeof raw === "string" ? `${raw}T12:00:00` : raw);
      return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" });
    });
    const values = points.map((p) => {
      let v = p[opts.valueKey];
      if ((v == null || v === "") && opts.valueKey === "remedios") v = p.unidades;
      if (nullableY && (v == null || v === "")) return null;
      const n = Number(v);
      if (nullableY && !Number.isFinite(n)) return null;
      return nullableY ? n : Number(v) || 0;
    });
    const lineColor = historicoCssVar(opts.lineColorVar, "#0082df");
    const fillColor = historicoCssVar(opts.fillColorVar, lineColor);
    const gridMinor = historicoCssVar("--historico-chart-grid", "rgba(128, 128, 128, 0.15)");
    const tickColor = historicoCssVar("--text-muted", "#888");

    const chart = new window.Chart(canvas.getContext("2d"), {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: opts.datasetLabel,
            data: values,
            borderColor: lineColor,
            backgroundColor: fillColor,
            fill: true,
            tension: 0,
            spanGaps: false,
            pointRadius: points.length > 45 ? 0 : 3,
            pointHoverRadius: 5,
            pointBackgroundColor: lineColor,
            pointBorderColor: lineColor,
            pointHoverBackgroundColor: lineColor,
            pointHoverBorderColor: lineColor,
            borderWidth: 2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        elements: {
          point: {
            backgroundColor: lineColor,
            borderColor: lineColor,
            hoverBackgroundColor: lineColor,
            hoverBorderColor: lineColor,
          },
        },
        plugins: {
          colors: { enabled: false },
          legend: { display: false },
          tooltip: {
            callbacks: {
              title(items) {
                const i = items[0]?.dataIndex;
                const raw = points[i]?.data;
                if (raw == null) return "";
                const d = new Date(typeof raw === "string" ? `${raw}T12:00:00` : raw);
                return d.toLocaleDateString("pt-BR", {
                  weekday: "short",
                  day: "2-digit",
                  month: "long",
                  year: "numeric",
                });
              },
              label(item) {
                const v = item.parsed.y;
                if (v == null || Number.isNaN(Number(v))) return "";
                return opts.formatTooltip(Number(v));
              },
            },
          },
        },
        scales: {
          x: {
            grid: { color: gridMinor },
            ticks: {
              color: tickColor,
              maxRotation: 45,
              minRotation: 0,
              autoSkip: true,
              maxTicksLimit: 14,
            },
          },
          y: {
            beginAtZero: true,
            grid: { color: gridMinor },
            ticks:
              yPrec > 0
                ? {
                    color: tickColor,
                    callback(value) {
                      return Number(value).toLocaleString("pt-BR", {
                        minimumFractionDigits: yPrec,
                        maximumFractionDigits: yPrec,
                      });
                    },
                  }
                : {
                    color: tickColor,
                    precision: 0,
                  },
          },
        },
      },
    });
    chart._historicoTheme = {
      lineVar: opts.lineColorVar,
      fillVar: opts.fillColorVar,
    };
    return chart;
  }

  function renderHistoricoStats(data) {
    if (!el.historicoResult) return;
    destroyHistoricoCharts();
    const nConc = Number(data.ordens_concluidas) || 0;
    const nCanc = Number(data.ordens_canceladas) || 0;
    const nPausa = Number(data.ordens_com_pausa) || 0;
    if (nConc === 0 && nCanc === 0 && nPausa === 0) {
      el.historicoResult.innerHTML = `
        <p class="historico-empty">Nenhum resultado nesse intervalo para este separador (sem OS concluídas, canceladas ou com pausa registrada). Conclua, cancele ou use pausa na aba Operação para ver indicadores aqui.</p>
      `;
      return;
    }
    const tmed =
      data.tempo_medio_minutos != null
        ? `${formatHistoricoNum(data.tempo_medio_minutos)} min`
        : "—";
    const tmedMed =
      data.tempo_medio_por_medicamento_segundos != null
        ? `${formatHistoricoNum(data.tempo_medio_por_medicamento_segundos)} s`
        : "—";
    const showChart = nConc > 0;
    const chartBlock = showChart
      ? `
      <div class="historico-charts-row">
        <div class="historico-chart-card" role="region" aria-label="Gráfico de remédios empacotados por dia">
          <h3 class="historico-chart__title">Remédios empacotados por dia</h3>
          <p class="historico-chart__lede">Total por dia civil (Brasília); cada ponto é só aquele dia.</p>
          <div class="historico-chart__canvas-wrap">
            <canvas id="historico-remedios-chart" width="400" height="200"></canvas>
          </div>
        </div>
        <div class="historico-chart-card" role="region" aria-label="Gráfico de OS concluídas por dia">
          <h3 class="historico-chart__title">OS concluídas por dia</h3>
          <p class="historico-chart__lede">Quantidade de OS finalizadas por dia civil (Brasília).</p>
          <div class="historico-chart__canvas-wrap">
            <canvas id="historico-os-chart" width="400" height="200"></canvas>
          </div>
        </div>
        <div class="historico-chart-card" role="region" aria-label="Gráfico de tempo médio por OS por dia">
          <h3 class="historico-chart__title">Tempo médio por OS (min)</h3>
          <p class="historico-chart__lede">Média do envio à conclusão por dia civil (Brasília); sem ponto nos dias sem OS com tempo válido.</p>
          <div class="historico-chart__canvas-wrap">
            <canvas id="historico-tempo-os-chart" width="400" height="200"></canvas>
          </div>
        </div>
      </div>`
      : "";
    el.historicoResult.innerHTML = `
      <div class="historico-stats-wrap">
      <div class="historico-grid" role="list">
        <div class="metric-box metric-box--progress" role="listitem">
          <span class="metric-box__label">OS concluídas</span>
          <p class="metric-box__value metric-box__value--elapsed">${formatHistoricoNum(data.ordens_concluidas)}</p>
          <span class="metric-box__hint">no período</span>
        </div>
        <div class="metric-box metric-box--time" role="listitem">
          <span class="metric-box__label">OS canceladas</span>
          <p class="metric-box__value metric-box__value--elapsed">${formatHistoricoNum(data.ordens_canceladas)}</p>
          <span class="metric-box__hint">cancelamento registrado no período</span>
        </div>
        <div class="metric-box metric-box--time" role="listitem">
          <span class="metric-box__label">OS pausadas</span>
          <p class="metric-box__value metric-box__value--elapsed">${formatHistoricoNum(data.ordens_com_pausa)}</p>
          <span class="metric-box__hint">concluídas ou canceladas com ≥1 pausa</span>
        </div>
        <div class="metric-box metric-box--progress" role="listitem">
          <span class="metric-box__label">Unidades empacotadas</span>
          <p class="metric-box__value metric-box__value--elapsed">${formatHistoricoNum(data.unidades_empacotadas)}</p>
          <span class="metric-box__hint">registradas ao concluir</span>
        </div>
        <div class="metric-box metric-box--time" role="listitem">
          <span class="metric-box__label">Unidades previstas (total)</span>
          <p class="metric-box__value metric-box__value--elapsed">${formatHistoricoNum(data.unidades_previstas_total)}</p>
          <span class="metric-box__hint">soma das OS</span>
        </div>
        <div class="metric-box metric-box--time" role="listitem">
          <span class="metric-box__label">Tempo médio por OS</span>
          <p class="metric-box__value metric-box__value--elapsed">${tmed}</p>
          <span class="metric-box__hint">do envio à conclusão</span>
        </div>
        <div class="metric-box metric-box--progress" role="listitem">
          <span class="metric-box__label">Tempo médio por medicamento</span>
          <p class="metric-box__value metric-box__value--elapsed">${tmedMed}</p>
          <span class="metric-box__hint">s por unidade no período</span>
        </div>
      </div>
      ${chartBlock}
      </div>
    `;
    if (showChart) {
      const serieRem = Array.isArray(data.remedios_por_dia)
        ? data.remedios_por_dia
        : Array.isArray(data.unidades_por_dia)
          ? data.unidades_por_dia
          : [];
      const serieOs = Array.isArray(data.os_concluidas_por_dia) ? data.os_concluidas_por_dia : [];
      const serieTmo = Array.isArray(data.tempo_medio_os_por_dia) ? data.tempo_medio_os_por_dia : [];
      const nf = new Intl.NumberFormat("pt-BR");
      requestAnimationFrame(() => {
        historicoRemediosChart = createHistoricoAreaChart("historico-remedios-chart", serieRem, {
          valueKey: "remedios",
          datasetLabel: "Remédios (linhas)",
          lineColorVar: "--accent-hover",
          fillColorVar: "--historico-chart-fill-remedios",
          formatTooltip: (v) => `${nf.format(v)} remédio(s)`,
        });
        historicoOsChart = createHistoricoAreaChart("historico-os-chart", serieOs, {
          valueKey: "ordens",
          datasetLabel: "OS concluídas",
          lineColorVar: "--accent",
          fillColorVar: "--historico-chart-fill-os",
          formatTooltip: (v) => `${nf.format(v)} OS`,
        });
        historicoTempoOsChart = createHistoricoAreaChart("historico-tempo-os-chart", serieTmo, {
          valueKey: "minutos_medio",
          datasetLabel: "Tempo médio (min)",
          lineColorVar: "--accent",
          fillColorVar: "--historico-chart-fill-os",
          nullableValues: true,
          yTickPrecision: 1,
          formatTooltip: (v) => `${nf.format(v)} min`,
        });
      });
    }
  }

  function renderRobotDetail(d) {
    el.detailEmpty.classList.add("hidden");
    el.detailArticle.classList.remove("hidden");

    el.detailHeading.textContent = d.name || "";
    const loc = d.location ? ` · ${d.location}` : "";
    el.detailMeta.textContent = `${d.code || ""}${loc}`;

    const running = d.status === "running";
    const paused = d.status === "paused";
    const online = typeof d.online === "boolean" ? d.online : robotIsOnline(d);

    el.detailBadges.innerHTML = "";
    const execBadge = document.createElement("span");
    if (paused) {
      execBadge.className = "badge badge--paused";
      execBadge.textContent = "Pausado";
    } else {
      execBadge.className = `badge ${running ? "badge--running" : "badge--idle"}`;
      execBadge.textContent = running ? "Em execução" : "Não em execução";
    }
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
      const got = d.units_separated ?? 0;
      const total = ord.expected_units ?? 0;
      detailLiveUnitGot = got;
      detailLiveUnitTotal = total;
      el.detailUnits.textContent = `${got} / ${total}`;
    } else {
      detailLiveUnitGot = 0;
      detailLiveUnitTotal = 0;
      el.detailUnits.textContent = "—";
      resetDetailDerivedMetrics();
    }

    el.detailStart.textContent = formatExecutionStart(d.job_started_at);

    /* Tempo: durante OS ativa o DOM do tempo é só do timer local (paintDetailElapsedDom).
 Unidades vêm do poll/render acima — assim os dois não se atrapalham. */
    const elapsedUiActive =
      running &&
      !paused &&
      ord != null &&
      d.job_started_at != null &&
      detailViewMatchesRobot(d);
    if (!elapsedUiActive) {
      el.detailElapsed.textContent = "—";
      if (d.elapsed_seconds != null && d.elapsed_seconds >= 0) {
        el.detailElapsed.textContent = formatElapsedSeconds(d.elapsed_seconds);
      }
    }

    ensureDetailElapsedDisplay(d);

    const secForPace =
      elapsedUiActive && ord != null
        ? Math.max(0, Math.floor(detailElapsedSync.anchorSec + (Date.now() - detailElapsedSync.anchorAtMs) / 1000))
        : d.elapsed_seconds != null && d.elapsed_seconds >= 0
          ? d.elapsed_seconds
          : null;
    maybeUpdatePaceMetrics(d, secForPace);

    const canActOnOs = ord != null && (running || paused);
    if (el.detailActions) {
      el.detailActions.hidden = ord == null;
    }
    if (el.btnPausarOs) {
      el.btnPausarOs.hidden = !(ord != null && running);
    }
    if (el.btnRetomarOs) {
      el.btnRetomarOs.hidden = !(ord != null && paused);
    }
    if (el.btnCancelarOs) {
      el.btnCancelarOs.hidden = !canActOnOs;
    }

    updateDetailPolling(d);
    ensureRemedySimulationsRunning();
  }

  async function loadRobotDetail(robotId) {
    const seq = ++detailLoadSeq;
    try {
      const res = await fetch(`${API_BASE}/robots/${robotId}`, FETCH_CRED);
      if (seq !== detailLoadSeq) return;
      if (res.status === 401) {
        window.location.replace("/login.html");
        return;
      }
      if (!res.ok) {
        if (res.status === 404) {
          showDetailPlaceholder();
          toast("Separador não encontrado.", "error");
        }
        /* Outros erros: mantém painel e contador local; o próximo poll tenta de novo. */
        return;
      }
      const d = await res.json();
      if (seq !== detailLoadSeq) return;
      renderRobotDetail(d);
    } catch (e) {
      if (seq !== detailLoadSeq) return;
      /* Falha de rede: não remove o detalhe nem zera o contador local. */
      toast(e instanceof Error ? e.message : "Erro de rede ao atualizar detalhes.", "error");
    }
  }

  function robotSearchQuery() {
    return el.robotSearch.value.trim();
  }

  function robotsListUrl() {
    return `${API_BASE}/robots`;
  }

  function renderRobotList(robots) {
    robotsCache = robots;
    renderOperacaoColetiva(robots);
    const q = robotSearchQuery().toLowerCase();
    const filtered = q
      ? robots.filter(
          (r) =>
            String(r.name).toLowerCase().includes(q) ||
            String(r.code).toLowerCase().includes(q) ||
            (r.location && String(r.location).toLowerCase().includes(q)),
        )
      : robots;
    el.robotList.innerHTML = "";
    if (!robots.length) {
      const empty = document.createElement("li");
      empty.className = "robot-list__empty";
      empty.setAttribute("role", "presentation");
      empty.textContent =
        "Nenhum separador ainda. Abra “Novo separador” abaixo e clique em Cadastrar.";
      el.robotList.appendChild(empty);
      return;
    }
    if (!filtered.length) {
      const empty = document.createElement("li");
      empty.className = "robot-list__empty";
      empty.setAttribute("role", "presentation");
      empty.textContent =
        "Nenhum separador encontrado para essa pesquisa. Tente outro termo ou limpe o campo.";
      el.robotList.appendChild(empty);
      return;
    }
    filtered.forEach((r) => {
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
        const exp = r.expected_units != null ? r.expected_units : "—";
        const got = r.units_separated ?? 0;
        const sub = document.createElement("div");
        sub.className = "robot-item__os-detail";
        sub.textContent = `${got} / ${exp} · ${formatOsActivityStatus(r.status)}`;
        btn.appendChild(sub);
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
    persistSelectedRobotId(id);
    renderRobotList(robotsCache);
    if (id != null) await loadRobotDetail(id);
  }

  async function loadRobots(options = {}) {
    const silent = Boolean(options.silent);
    try {
      const res = await fetch(robotsListUrl(), FETCH_CRED);
      if (res.status === 401) {
        window.location.replace("/login.html");
        return;
      }
      if (!res.ok) {
        const errBody = await res.text();
        throw new Error(errBody || `Lista falhou (${res.status})`);
      }
      const data = await res.json();
      if (!Array.isArray(data)) {
        throw new Error("Resposta inválida da API.");
      }
      renderRobotList(data);
      populateManualOsRobotSelect();
      if (el.historicoRobot && !el.viewHistorico?.classList.contains("hidden")) {
        populateHistoricoRobotSelect();
      }
      if (!el.viewRelatorio?.classList.contains("hidden") && getRelatorioSubtab() === "separador") {
        renderRelatorioSeparadorList();
      }
      el.connStatus.textContent = "Conectado";
      el.connStatus.className = "badge badge--ok";
      ensureRemedySimulationsRunning();
      ensureOperacaoListPoll();
      if (selectedRobotId != null && !data.some((r) => r.id === selectedRobotId)) {
        selectedRobotId = null;
        persistSelectedRobotId(null);
        renderRobotList(data);
        showDetailPlaceholder();
      } else if (selectedRobotId != null) {
        await loadRobotDetail(selectedRobotId);
      } else {
        showDetailPlaceholder();
      }
    } catch (e) {
      el.connStatus.textContent = "Offline";
      el.connStatus.className = "badge badge--error";
      if (!silent) {
        toast(
          e instanceof Error ? e.message : "Não foi possível contatar o servidor.",
          "error",
        );
      }
    }
  }

  el.formManualOs?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const rid = parseInt(el.manualOsRobot?.value || "", 10);
    const qty = parseInt(el.manualOsQty?.value || "0", 10);
    const code = el.manualOsCode?.value.trim() || "";
    if (!code) {
      toast("Informe o número da OS.", "error");
      return;
    }
    if (Number.isNaN(rid) || rid < 1) {
      toast("Selecione um separador.", "error");
      return;
    }
    if (Number.isNaN(qty) || qty < 1 || qty > 500) {
      toast("Quantidade de remédios deve ser entre 1 e 500.", "error");
      return;
    }
    await fetchCsrf();
    el.btnManualOsSubmit.disabled = true;
    const wantSimulate = Boolean(el.manualOsSimulate?.checked);
    try {
      const res = await apiJson("/service-orders/manual", {
        method: "POST",
        body: JSON.stringify({
          os_code: code,
          client_name: el.manualOsClient?.value.trim() || "",
          robot_id: rid,
          quantidade_remedios: qty,
        }),
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
      const order = await res.json();
      el.formManualOs.reset();
      if (el.manualOsQty) el.manualOsQty.value = "5";
      if (el.manualOsSimulate) el.manualOsSimulate.checked = true;
      closeManualOsModal();
      toast("OS criada e enviada ao separador.", "success");
      stopRemedySimulation(rid);
      await loadRobots();
      await selectRobot(rid);
      const listBtn = el.robotList?.querySelector(`[data-id="${rid}"]`);
      listBtn?.scrollIntoView({ block: "nearest", behavior: "smooth" });
      if (wantSimulate) {
        startRemedySimulation(rid, order.expected_units ?? qty);
      }
    } catch (e) {
      toast(e instanceof Error ? e.message : "Erro ao criar OS.", "error");
    } finally {
      el.btnManualOsSubmit.disabled = false;
    }
  });

  el.formNewRobot.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    await fetchCsrf();
    const body = {
      code: el.newCode.value.trim(),
      name: el.newName.value.trim(),
      location: el.newLocation.value.trim(),
      model: el.newModel.value.trim(),
      specifications: "",
    };
    if (!body.code || !body.name) {
      toast("Código e nome são obrigatórios.", "error");
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
      closeNewRobotModal();
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

  el.btnNotifications?.addEventListener("click", (ev) => {
    ev.stopPropagation();
    toggleNotifPanel();
  });

  el.btnProfile?.addEventListener("click", (ev) => {
    ev.preventDefault();
    ev.stopPropagation();
    if (isProfileDrawerOpen()) closeProfileDrawer();
    else openProfileDrawer();
  });

  [el.profileTabOwn, el.profileTabUser, el.profileTabNew].forEach((tab) => {
    tab?.addEventListener("click", () => {
      const v = tab.getAttribute("data-profile-view");
      if (!v) return;
      setProfileDrawerView(v);
      if (v === "user" && currentUserIsAdmin) {
        void loadProfileUserListForDrawer();
      }
    });
  });
  el.profileDrawerBackdrop?.addEventListener("click", () => closeProfileDrawer());
  el.profileDrawerClose?.addEventListener("click", () => closeProfileDrawer());
  el.profileUserSelect?.addEventListener("change", () => syncProfileTargetFromSelect());

  el.formProfileOwnPwd?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const cur = el.profileOwnCurrent?.value ?? "";
    const n1 = el.profileOwnNew?.value ?? "";
    const n2 = el.profileOwnNew2?.value ?? "";
    if (n1 !== n2) {
      toast("As novas senhas não coincidem.", "error");
      return;
    }
    if (n1.length < 6) {
      toast("A nova senha deve ter pelo menos 6 caracteres.", "error");
      return;
    }
    await fetchCsrf();
    const btn = el.formProfileOwnPwd?.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    try {
      const res = await apiJson("/auth/me/password", {
        method: "PATCH",
        body: JSON.stringify({ current_password: cur, new_password: n1 }),
      });
      if (res.status === 401) {
        window.location.replace("/login.html");
        return;
      }
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
      toast("Senha alterada.", "success");
      el.formProfileOwnPwd.reset();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Falha ao alterar senha.", "error");
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  el.formProfileTarget?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (!currentUserIsAdmin) return;
    const id = parseInt(el.profileUserSelect?.value, 10);
    if (Number.isNaN(id)) {
      toast("Selecione um usuário.", "error");
      return;
    }
    const pwd = (el.profileTargetPwd?.value || "").trim();
    const isAdm = Boolean(el.profileTargetAdmin?.checked);
    const body = { is_admin: isAdm };
    if (pwd.length) body.new_password = pwd;
    await fetchCsrf();
    const btn = el.formProfileTarget?.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    try {
      const res = await apiJson(`/admin/users/${id}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      });
      if (res.status === 401) {
        window.location.replace("/login.html");
        return;
      }
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
      toast("Usuário atualizado.", "success");
      if (el.profileTargetPwd) el.profileTargetPwd.value = "";
      await loadProfileUserListForDrawer();
      if (id === currentUserId) await refreshSessionUserFromMe();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Falha ao atualizar usuário.", "error");
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  el.formProfileNewUser?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (!currentUserIsAdmin) return;
    const uname = (el.profileNewUsername?.value || "").trim();
    const pwd = el.profileNewPwd?.value || "";
    const isAdm = Boolean(el.profileNewAdmin?.checked);
    if (uname.length < 1) {
      toast("Informe o nome de usuário.", "error");
      return;
    }
    if (pwd.length < 6) {
      toast("A senha inicial deve ter pelo menos 6 caracteres.", "error");
      return;
    }
    await fetchCsrf();
    const btn = el.formProfileNewUser?.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;
    try {
      const res = await apiJson("/admin/users", {
        method: "POST",
        body: JSON.stringify({ username: uname, password: pwd, is_admin: isAdm }),
      });
      if (res.status === 401) {
        window.location.replace("/login.html");
        return;
      }
      if (res.status === 409) {
        toast("Este nome de usuário já existe.", "error");
        return;
      }
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
      toast("Usuário criado.", "success");
      el.formProfileNewUser.reset();
      if (el.profileNewAdmin) el.profileNewAdmin.checked = false;
      await loadProfileUserListForDrawer();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Falha ao criar usuário.", "error");
    } finally {
      if (btn) btn.disabled = false;
    }
  });

  el.btnNotifClear?.addEventListener("click", (ev) => {
    ev.stopPropagation();
    clearNotificationsFromPanel();
  });

  el.btnLogout?.addEventListener("click", async () => {
    /* Persistir separador; aba já vai em sessionStorage via setAppView (garante chave se nunca trocou de aba). */
    if (selectedRobotId != null) persistSelectedRobotId(selectedRobotId);
    try {
      if (sessionStorage.getItem(LAST_APP_VIEW_KEY) == null) {
        sessionStorage.setItem(LAST_APP_VIEW_KEY, "operacao");
      }
    } catch {
      /* ignore */
    }
    /* Não limpar emr-remedy-sim-jobs: após novo login, ensureRemedySimulationsRunning religa os ticks. */
    try {
      await fetch(`${API_BASE}/auth/logout`, { method: "POST", ...FETCH_CRED });
    } catch {
      /* ignore */
    }
    window.location.href = "/login.html";
  });

  el.btnOpenNewRobot?.addEventListener("click", () => {
    openNewRobotModal();
  });
  el.btnOpenManualOs?.addEventListener("click", () => {
    openManualOsModal();
  });

  el.newRobotModalBackdrop?.addEventListener("click", closeNewRobotModal);
  el.newRobotModalCancel?.addEventListener("click", closeNewRobotModal);
  el.manualOsModalBackdrop?.addEventListener("click", closeManualOsModal);
  el.manualOsModalCancel?.addEventListener("click", closeManualOsModal);

  el.robotSearch.addEventListener("input", () => {
    clearTimeout(robotSearchDebounce);
    robotSearchDebounce = setTimeout(() => {
      if (robotsCache.length) {
        renderRobotList(robotsCache);
      } else {
        loadRobots();
      }
    }, 320);
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
    if (
      el.editStatus &&
      !el.editStatus.disabled &&
      el.editStatus.value &&
      el.editStatus.value !== "__running__"
    ) {
      body.status = el.editStatus.value;
    }
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
        persistSelectedRobotId(null);
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

  el.tabOperacao?.addEventListener("click", () => setAppView("operacao"));
  el.tabHistorico?.addEventListener("click", () => setAppView("historico"));
  el.tabRelatorio?.addEventListener("click", () => setAppView("relatorio"));
  el.tabLogs?.addEventListener("click", () => setAppView("logs"));
  el.relatorioTabOs?.addEventListener("click", () => setRelatorioSubtab("os"));
  el.relatorioTabSeparador?.addEventListener("click", () => setRelatorioSubtab("separador"));
  el.formRelatorioOs?.addEventListener("submit", (ev) => {
    ev.preventDefault();
    void loadRelatorioOsList(true);
  });
  el.btnRelatorioOsLimpar?.addEventListener("click", () => {
    clearRelatorioOsFilters();
  });
  el.relatorioSeparadorBusca?.addEventListener("input", () => {
    renderRelatorioSeparadorList();
  });
  el.relatorioOsResult?.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-relatorio-os-page]");
    if (!btn || btn.disabled) return;
    const dir = btn.getAttribute("data-relatorio-os-page");
    if (dir === "prev") {
      relatorioOsPageOffset = Math.max(0, relatorioOsPageOffset - RELATORIO_OS_LIMIT);
      void loadRelatorioOsList(false);
    } else if (dir === "next") {
      relatorioOsPageOffset += RELATORIO_OS_LIMIT;
      void loadRelatorioOsList(false);
    }
  });
  el.btnLogsRefresh?.addEventListener("click", () => void loadAuditLogs());

  el.formLogsFilter?.addEventListener("submit", (ev) => {
    ev.preventDefault();
    auditLogsOffset = 0;
    void loadAuditLogs();
  });

  el.btnLogsFilterClear?.addEventListener("click", () => {
    if (el.logsFilterUsername) el.logsFilterUsername.value = "";
    if (el.logsFilterCategory) el.logsFilterCategory.value = "";
    if (el.logsFilterDe) el.logsFilterDe.value = "";
    if (el.logsFilterAte) el.logsFilterAte.value = "";
    auditLogsOffset = 0;
    void loadAuditLogs();
  });

  el.logsPerPage?.addEventListener("change", () => {
    try {
      localStorage.setItem(AUDIT_LOGS_LIMIT_KEY, el.logsPerPage.value);
    } catch (_) {
      /* ignore */
    }
    auditLogsOffset = 0;
    void loadAuditLogs();
  });

  el.logsResult?.addEventListener("click", (ev) => {
    const btn = ev.target.closest("[data-audit-logs-page]");
    if (!btn || btn.disabled) return;
    const dir = btn.getAttribute("data-audit-logs-page");
    const lim = getAuditLogsLimit();
    if (dir === "prev") {
      auditLogsOffset = Math.max(0, auditLogsOffset - lim);
      void loadAuditLogs();
    } else if (dir === "next" && auditLogsOffset + lim < lastAuditLogsTotal) {
      auditLogsOffset += lim;
      void loadAuditLogs();
    }
  });
  el.btnLogsClear?.addEventListener("click", () => {
    if (!currentUserIsAdmin || !el.btnLogsClear) return;
    openClearLogsModal();
  });

  el.clearLogsModalBackdrop?.addEventListener("click", closeClearLogsModal);
  el.clearLogsModalCancel?.addEventListener("click", closeClearLogsModal);
  el.clearLogsModalConfirm?.addEventListener("click", async () => {
    if (!el.clearLogsModalConfirm) return;
    await fetchCsrf();
    el.clearLogsModalConfirm.disabled = true;
    try {
      const res = await apiJson("/admin/audit-logs", { method: "DELETE" });
      if (res.status === 401) {
        closeClearLogsModal();
        window.location.replace("/login.html");
        return;
      }
      if (res.status === 403) {
        toast("Sem permissão ou token CSRF inválido. Atualize a página.", "error");
        return;
      }
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
      const n = data.deleted != null ? data.deleted : "—";
      closeClearLogsModal();
      toast(`Logs apagados (${n} registro(s)).`, "success");
      auditLogsOffset = 0;
      await loadAuditLogs();
    } catch (e) {
      toast(e instanceof Error ? e.message : "Falha ao limpar logs.", "error");
    } finally {
      el.clearLogsModalConfirm.disabled = false;
    }
  });

  el.formHistorico?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const rid = el.historicoRobot?.value;
    const de = el.historicoDe?.value;
    const ate = el.historicoAte?.value;
    if (!rid || !de || !ate) {
      toast("Preencha separador e datas.", "error");
      return;
    }
    if (de > ate) {
      toast("A data inicial não pode ser depois da final.", "error");
      return;
    }
    el.btnHistoricoConsultar.disabled = true;
    destroyHistoricoCharts();
    el.historicoResult.innerHTML =
      '<p class="historico-empty" role="status">Consultando…</p>';
    try {
      const params = new URLSearchParams({ de, ate });
      const res = await fetch(`${API_BASE}/robots/${encodeURIComponent(rid)}/historico?${params}`, FETCH_CRED);
      const text = await res.text();
      if (res.status === 401) {
        window.location.replace("/login.html");
        return;
      }
      if (!res.ok) {
        let msg = `Erro ${res.status}`;
        try {
          const err = JSON.parse(text);
          msg = formatApiDetail(err.detail) || text || msg;
        } catch {
          if (text) msg = text;
        }
        toast(msg, "error");
        el.historicoResult.innerHTML = "";
        return;
      }
      const data = JSON.parse(text);
      renderHistoricoStats(data);
    } catch (e) {
      el.historicoResult.innerHTML = "";
      toast(e instanceof Error ? e.message : "Falha ao consultar histórico.", "error");
    } finally {
      el.btnHistoricoConsultar.disabled = false;
    }
  });

  async function postRobotAction(path, successMsg) {
    if (selectedRobotId == null) return;
    await fetchCsrf();
    const res = await apiJson(path, { method: "POST" });
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
      return false;
    }
    toast(successMsg, "success");
    await loadRobots();
    await loadRobotDetail(selectedRobotId);
    return true;
  }

  el.btnPausarOs?.addEventListener("click", async () => {
    if (selectedRobotId == null) return;
    el.btnPausarOs.disabled = true;
    try {
      await postRobotAction(`/robots/${selectedRobotId}/pausar`, "Separação pausada.");
    } catch (e) {
      toast(e instanceof Error ? e.message : "Erro ao pausar.", "error");
    } finally {
      el.btnPausarOs.disabled = false;
    }
  });

  el.btnRetomarOs?.addEventListener("click", async () => {
    if (selectedRobotId == null) return;
    el.btnRetomarOs.disabled = true;
    try {
      await postRobotAction(`/robots/${selectedRobotId}/retomar`, "Separação retomada.");
    } catch (e) {
      toast(e instanceof Error ? e.message : "Erro ao retomar.", "error");
    } finally {
      el.btnRetomarOs.disabled = false;
    }
  });

  el.btnCancelarOs?.addEventListener("click", async () => {
    if (selectedRobotId == null) return;
    await fetchCsrf();
    el.btnCancelarOs.disabled = true;
    try {
      const res = await apiJson(`/robots/${selectedRobotId}/cancelar-os`, { method: "POST" });
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
      stopRemedySimulation(selectedRobotId);
      toast("OS cancelada: separador liberado e ordem voltou para a fila.", "success");
      await loadRobots();
      await loadRobotDetail(selectedRobotId);
    } catch (e) {
      toast(e instanceof Error ? e.message : "Erro ao cancelar OS.", "error");
    } finally {
      el.btnCancelarOs.disabled = false;
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    if (isProfileDrawerOpen()) {
      e.preventDefault();
      closeProfileDrawer();
      return;
    }
    if (isNotifPanelOpen()) {
      e.preventDefault();
      setNotifPanelOpen(false);
      return;
    }
    if (!el.editModal.hidden) {
      e.preventDefault();
      closeEditModal();
      return;
    }
    if (el.newRobotModal && !el.newRobotModal.hidden) {
      e.preventDefault();
      closeNewRobotModal();
      return;
    }
    if (el.manualOsModal && !el.manualOsModal.hidden) {
      e.preventDefault();
      closeManualOsModal();
      return;
    }
    if (el.clearLogsModal && !el.clearLogsModal.hidden) {
      e.preventDefault();
      closeClearLogsModal();
      return;
    }
    if (!el.deleteModal.hidden) {
      e.preventDefault();
      closeDeleteModal();
    }
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) return;
    void loadRobots({ silent: true });
  });

  window.addEventListener("pageshow", () => {
    void loadRobots({ silent: true });
  });

  async function boot() {
    initThemeToggle();
    initHistoricoDefaultDates();
    initRelatorioSubtabs();
    initLogsPerPageFromStorage();
    try {
      const me = await fetch(`${API_BASE}/auth/me`, FETCH_CRED);
      if (me.status === 401) {
        window.location.replace("/login.html");
        return;
      }
      if (!me.ok) throw new Error("Falha ao verificar sessão.");
      const meData = await me.json();
      applyAdminUiFromSession(meData.user?.is_admin);
      currentUserId = meData.user?.id != null ? Number(meData.user.id) : null;
      currentUsername = meData.user?.username != null ? String(meData.user.username) : "";
      await fetchCsrf();
      void fetchNotifications();
      ensureNotificationsPoll();
      try {
        const raw = sessionStorage.getItem(SELECTED_ROBOT_KEY);
        if (raw != null) {
          const n = parseInt(raw, 10);
          if (!Number.isNaN(n)) selectedRobotId = n;
        }
      } catch {
        /* ignore */
      }
      await loadRobots();
      const restore = readLastAppView();
      if (restore === "historico" || restore === "relatorio" || restore === "logs") {
        setAppView(restore);
      } else if (restore == null) {
        try {
          sessionStorage.setItem(LAST_APP_VIEW_KEY, "operacao");
        } catch {
          /* ignore */
        }
      }
    } catch (e) {
      el.connStatus.textContent = "Erro";
      el.connStatus.className = "badge badge--error";
      toast(String(e.message || e), "error");
    }
  }

  boot();
})();
