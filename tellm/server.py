"""tellm v4 server"""
import asyncio
import base64
import html as html_lib
import inspect
import json
import logging
import time
from http import HTTPStatus
from urllib.parse import parse_qs

import websockets
from websockets.datastructures import Headers
from websockets.http11 import Response

from .bot import TellmBot, Task, TaskType
from .config import load_config
from .registry import (
    RegistryValidationError,
    registry_manifest_schema,
    service_result_schema,
    validate_schema,
)
from litellm import completion


def _websocket_logger():
    logger = logging.getLogger("tellm.websockets")
    logger.addHandler(logging.NullHandler())
    logger.setLevel(logging.CRITICAL)
    return logger


def _browser_client_html(host: str) -> str:
    ws_url = "ws://" + host
    return f"""<!doctype html>
<html lang="pl" data-theme="light">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>tellm v4</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #20242a;
      --muted: #5d6673;
      --line: #d9dee7;
      --accent: #0f766e;
      --accent-strong: #115e59;
      --danger: #b42318;
      --code: #eef2f7;
      --code-text: #243041;
      --input-bg: #ffffff;
      --button-bg: #ffffff;
      --entry-bg: #fbfcfe;
      --focus: rgba(15, 118, 110, 0.22);
    }}
    :root[data-theme="warm"] {{
      color-scheme: light;
      --bg: #faf6f1;
      --panel: #fffdf8;
      --text: #261f1a;
      --muted: #6f6258;
      --line: #e7d8c7;
      --accent: #b45309;
      --accent-strong: #92400e;
      --danger: #b42318;
      --code: #f4eadf;
      --code-text: #322216;
      --input-bg: #fffaf4;
      --button-bg: #fffaf4;
      --entry-bg: #fff7ed;
      --focus: rgba(180, 83, 9, 0.22);
    }}
    :root[data-theme="dark"] {{
      color-scheme: dark;
      --bg: #151716;
      --panel: #202321;
      --text: #eef4f0;
      --muted: #a9b3ad;
      --line: #383d39;
      --accent: #2dd4bf;
      --accent-strong: #14b8a6;
      --danger: #fb7185;
      --code: #2b302d;
      --code-text: #dbe7e2;
      --input-bg: #181b19;
      --button-bg: #242824;
      --entry-bg: #1b1f1c;
      --focus: rgba(45, 212, 191, 0.24);
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      width: min(1120px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 24px 0;
    }}
    header {{
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{
      margin: 0;
      font-size: 28px;
      line-height: 1.1;
      font-weight: 700;
    }}
    .endpoint {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 14px;
    }}
    code {{
      padding: 2px 5px;
      border-radius: 4px;
      background: var(--code);
      color: var(--code-text);
    }}
    .header-tools {{
      display: grid;
      justify-items: end;
      gap: 10px;
    }}
    .status {{
      min-width: 150px;
      text-align: right;
      color: var(--muted);
      font-size: 14px;
    }}
    .theme-control {{
      margin: 0;
      padding: 0;
      border: 0;
      color: var(--muted);
    }}
    .theme-control legend {{
      margin: 0 0 6px;
      padding: 0;
      text-align: right;
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .theme-options {{
      display: inline-grid;
      grid-template-columns: repeat(3, minmax(62px, 1fr));
      gap: 2px;
      padding: 3px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--button-bg);
    }}
    .theme-options label {{
      position: relative;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 30px;
      margin: 0;
      border-radius: 6px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      user-select: none;
    }}
    .theme-options input {{
      position: absolute;
      opacity: 0;
      inset: 0;
      cursor: pointer;
    }}
    .theme-options span {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 100%;
      min-height: 30px;
      padding: 0 8px;
      border-radius: 5px;
    }}
    .theme-options input:focus-visible + span {{
      outline: 2px solid var(--focus);
      outline-offset: 1px;
    }}
    .theme-options input:checked + span {{
      background: var(--accent);
      color: #fff;
    }}
    .links {{
      display: flex;
      justify-content: flex-end;
      gap: 10px;
      font-size: 13px;
    }}
    .links a {{
      color: var(--accent);
      font-weight: 650;
      text-decoration: none;
    }}
    .layout {{
      display: grid;
      grid-template-columns: minmax(0, 420px) minmax(0, 1fr);
      gap: 20px;
      margin-top: 20px;
    }}
    section {{
      min-width: 0;
    }}
    .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }}
    .panel h2 {{
      margin: 0 0 12px;
      font-size: 16px;
      line-height: 1.25;
    }}
    label {{
      display: block;
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 13px;
      font-weight: 600;
    }}
    textarea {{
      width: 100%;
      min-height: 150px;
      resize: vertical;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 12px;
      color: var(--text);
      font: inherit;
      line-height: 1.45;
      background: var(--input-bg);
    }}
    textarea:focus {{
      outline: 2px solid var(--focus);
      border-color: var(--accent);
    }}
    .actions {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
      margin-top: 12px;
    }}
    .share-actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 8px;
    }}
    button {{
      min-height: 38px;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 0 12px;
      background: var(--button-bg);
      color: var(--text);
      font: inherit;
      font-weight: 650;
      cursor: pointer;
    }}
    button.primary {{
      border-color: var(--accent);
      background: var(--accent);
      color: #fff;
    }}
    button.primary:hover {{ background: var(--accent-strong); }}
    button:disabled {{
      cursor: not-allowed;
      opacity: 0.55;
    }}
    .toggle {{
      display: inline-flex;
      align-items: center;
      gap: 7px;
      margin-left: auto;
      color: var(--muted);
      font-size: 13px;
      font-weight: 600;
    }}
    .toggle input {{ width: 16px; height: 16px; }}
    .log {{
      display: grid;
      gap: 10px;
      max-height: 340px;
      overflow: auto;
    }}
    .entry {{
      border-left: 3px solid var(--line);
      padding: 8px 10px;
      background: var(--entry-bg);
    }}
    .entry.user {{ border-color: var(--accent); }}
    .entry.error {{ border-color: var(--danger); color: var(--danger); }}
    .entry.workflow {{ border-color: var(--accent); }}
    .entry.warn {{ border-color: #b45309; }}
    .entry .meta {{
      margin-bottom: 4px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .entry pre {{
      margin: 6px 0 0;
      white-space: pre-wrap;
      word-break: break-word;
      color: var(--text);
      font-size: 12px;
    }}
    iframe {{
      width: 100%;
      min-height: 430px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--input-bg);
    }}
    .empty {{
      color: var(--muted);
      font-size: 14px;
    }}
    @media (max-width: 820px) {{
      main {{ width: min(100vw - 20px, 720px); padding-top: 16px; }}
      header {{ align-items: flex-start; flex-direction: column; }}
      .header-tools {{ justify-items: start; width: 100%; }}
      .status {{ text-align: left; min-width: 0; }}
      .links {{ justify-content: flex-start; }}
      .theme-control legend {{ text-align: left; }}
      .theme-options {{ width: 100%; }}
      .layout {{ grid-template-columns: 1fr; }}
      .toggle {{ margin-left: 0; width: 100%; }}
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>tellm v4</h1>
        <div class="endpoint">WebSocket endpoint: <code id="endpoint">{ws_url}</code></div>
      </div>
      <div class="header-tools">
        <div class="status" id="status">Łączenie...</div>
        <fieldset class="theme-control">
          <legend>Motyw</legend>
          <div class="theme-options">
            <label><input type="radio" name="theme" value="warm"><span>Warm</span></label>
            <label><input type="radio" name="theme" value="light"><span>Light</span></label>
            <label><input type="radio" name="theme" value="dark"><span>Dark</span></label>
          </div>
        </fieldset>
        <div class="links"><a href="/docs">API docs</a><a href="/registry-ui">registry</a><a href="/autoimprovement">autoimprove</a><a href="/healthz">healthz</a></div>
      </div>
    </header>

    <div class="layout">
      <section class="panel">
        <h2>Wejście</h2>
        <label for="prompt">Tekst lub dyktowanie</label>
        <textarea id="prompt" placeholder="Wpisz polecenie albo użyj dyktowania"></textarea>
        <div class="actions">
          <button id="dictate" type="button">Dyktuj</button>
          <button id="send" class="primary" type="button">Wyślij</button>
          <button id="cancel" type="button" disabled>Przerwij</button>
          <button id="clear" type="button">Wyczyść</button>
          <label class="toggle"><input id="speak" type="checkbox"> TTS</label>
        </div>
        <div class="share-actions">
          <button id="copyQuery" type="button">Kopiuj query</button>
          <button id="copyResult" type="button" disabled>Kopiuj wynik</button>
        </div>
      </section>

      <section class="panel">
        <h2>Historia</h2>
        <div id="log" class="log"><div class="empty">Brak wiadomości.</div></div>
      </section>

      <section class="panel" style="grid-column: 1 / -1;">
        <h2>Logi workflow</h2>
        <div class="share-actions">
          <button id="copyWorkflowLogs" type="button" disabled>Kopiuj logi</button>
        </div>
        <div id="workflowLog" class="log"><div class="empty">Brak logów.</div></div>
      </section>

      <section class="panel" style="grid-column: 1 / -1;">
        <h2>Widok HTML</h2>
        <iframe id="view" title="tellm generated view"></iframe>
      </section>
    </div>
  </main>

  <script>
    const endpoint = document.getElementById("endpoint").textContent;
    const statusEl = document.getElementById("status");
    const promptEl = document.getElementById("prompt");
    const logEl = document.getElementById("log");
    const viewEl = document.getElementById("view");
    const sendBtn = document.getElementById("send");
    const cancelBtn = document.getElementById("cancel");
    const clearBtn = document.getElementById("clear");
    const copyQueryBtn = document.getElementById("copyQuery");
    const copyResultBtn = document.getElementById("copyResult");
    const copyWorkflowLogsBtn = document.getElementById("copyWorkflowLogs");
    const dictateBtn = document.getElementById("dictate");
    const speakEl = document.getElementById("speak");
    const workflowLogEl = document.getElementById("workflowLog");
    const themeInputs = Array.from(document.querySelectorAll('input[name="theme"]'));
    const allowedThemes = new Set(["warm", "light", "dark"]);
    let socket;
    let recognition;
    let recognizing = false;
    let busy = false;
    let urlTimer;
    let lastResultQuery = "";
    let lastViewId = "";
    let workflowLogs = [];

    function applyTheme(theme) {{
      const selected = allowedThemes.has(theme) ? theme : "light";
      document.documentElement.dataset.theme = selected;
      themeInputs.forEach((input) => {{
        input.checked = input.value === selected;
      }});
      localStorage.setItem("tellm-theme", selected);
    }}

    function setStatus(text, isError = false) {{
      statusEl.textContent = text;
      statusEl.style.color = isError ? "var(--danger)" : "var(--muted)";
    }}

    function shareUrl(includeResult = false) {{
      const params = new URLSearchParams();
      const text = promptEl.value.trim();
      if (text) params.set("q", text);
      if (includeResult && lastViewId) params.set("view_id", lastViewId);
      const query = params.toString();
      return window.location.origin + window.location.pathname + (query ? "?" + query : "");
    }}

    function replaceUrl(includeResult = false) {{
      const url = new URL(shareUrl(includeResult));
      window.history.replaceState({{}}, "", url.pathname + url.search);
      updateShareButtons();
    }}

    function updateShareButtons() {{
      copyQueryBtn.disabled = !promptEl.value.trim();
      copyResultBtn.disabled = !lastViewId;
      copyWorkflowLogsBtn.disabled = workflowLogs.length === 0;
    }}

    function setBusy(value) {{
      busy = value;
      sendBtn.disabled = value;
      dictateBtn.disabled = value;
      clearBtn.disabled = value;
      promptEl.readOnly = value;
      cancelBtn.disabled = !value;
    }}

    async function copyText(value) {{
      if (navigator.clipboard && window.isSecureContext) {{
        await navigator.clipboard.writeText(value);
        return;
      }}
      const helper = document.createElement("textarea");
      helper.value = value;
      helper.setAttribute("readonly", "");
      helper.style.position = "fixed";
      helper.style.left = "-9999px";
      document.body.appendChild(helper);
      helper.select();
      document.execCommand("copy");
      helper.remove();
    }}

    async function copyShareUrl(includeResult) {{
      await copyText(shareUrl(includeResult));
      setStatus(includeResult ? "Skopiowano wynik" : "Skopiowano query");
    }}

    function workflowLogsText() {{
      return workflowLogs.map((item) => {{
        const details = item.details ? "\\n" + JSON.stringify(item.details, null, 2) : "";
        return [
          item.ts || "",
          (item.stage || "workflow") + " / " + (item.status || "info"),
          item.message || "",
        ].filter(Boolean).join("\\n") + details;
      }}).join("\\n\\n");
    }}

    async function copyWorkflowLogs() {{
      if (!workflowLogs.length) return;
      await copyText(workflowLogsText());
      setStatus("Skopiowano logi workflow");
    }}

    function syncQueryUrl() {{
      const current = promptEl.value.trim();
      if (lastResultQuery && current !== lastResultQuery) {{
        lastViewId = "";
      }}
      window.clearTimeout(urlTimer);
      urlTimer = window.setTimeout(() => replaceUrl(false), 180);
      updateShareButtons();
    }}

    async function restoreWorkflowLogs(viewId) {{
      const uri = "tellm://artifact/json/workflow-result/" + viewId;
      const response = await fetch("/resolve?uri=" + encodeURIComponent(uri) + "&include_value=true");
      if (!response.ok) throw new Error("Nie znaleziono logów workflow");
      const payload = await response.json();
      const result = payload.value || {{}};
      const resultOk = result.ok === true;
      const errors = Array.isArray(result.errors) ? result.errors : [];
      addWorkflowLog(
        "service_result",
        resultOk ? "ok" : "failed",
        resultOk ? "Wynik usługi OK." : "Usługa zwróciła błąd biznesowy.",
        {{
          business_status: resultOk ? "ok" : "failed",
          result_ok: result.ok,
          errors,
          uri: result.uri || "",
          type: result.type || "",
        }}
      );
      addWorkflowLog(
        "workflow",
        resultOk ? "ok" : "completed_with_service_error",
        resultOk ? "Workflow potwierdzony i zakończony." : "Workflow zakończony, ale wynik usługi jest błędem.",
        {{
          restored_from_view_id: viewId,
          service_result_status: resultOk ? "ok" : "failed",
        }}
      );
    }}

    async function restoreUrlState() {{
      const params = new URLSearchParams(window.location.search);
      const query = params.get("q") || "";
      const viewId = params.get("view_id") || "";
      if (query) {{
        promptEl.value = query;
        lastResultQuery = query;
      }}
      if (viewId) {{
        try {{
          const response = await fetch("/views/" + encodeURIComponent(viewId));
          if (!response.ok) throw new Error("Nie znaleziono widoku");
          viewEl.srcdoc = await response.text();
          lastViewId = viewId;
          addLog("system", "Wczytano wynik z linku.");
          await restoreWorkflowLogs(viewId);
          setStatus("Wczytano link");
        }} catch (error) {{
          addLog("error", error.message || "Nie udało się wczytać wyniku z linku.");
          setStatus("Błąd linku", true);
        }}
      }}
      updateShareButtons();
    }}

    function addLog(kind, text) {{
      const empty = logEl.querySelector(".empty");
      if (empty) empty.remove();
      const entry = document.createElement("div");
      entry.className = "entry " + kind;
      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = kind === "user" ? "Ty" : kind === "error" ? "Błąd" : "tellm";
      const body = document.createElement("div");
      body.textContent = text;
      entry.append(meta, body);
      logEl.prepend(entry);
    }}

    function addWorkflowLog(stage, status, message, details = null) {{
      const empty = workflowLogEl.querySelector(".empty");
      if (empty) empty.remove();
      const entry = document.createElement("div");
      const warnStatuses = ["repair", "warning", "failed", "completed_with_warnings", "completed_with_service_error"];
      entry.className = "entry workflow " + (status === "error" ? "error" : warnStatuses.includes(status) ? "warn" : "");
      const meta = document.createElement("div");
      meta.className = "meta";
      meta.textContent = stage + " / " + status;
      const body = document.createElement("div");
      body.textContent = message || "";
      entry.append(meta, body);
      if (details) {{
        const pre = document.createElement("pre");
        pre.textContent = JSON.stringify(details, null, 2);
        entry.append(pre);
      }}
      workflowLogEl.prepend(entry);
      workflowLogs.push({{
        ts: new Date().toISOString(),
        stage,
        status,
        message,
        details
      }});
      workflowLogs = workflowLogs.slice(-80);
      updateShareButtons();
    }}

    function connect() {{
      socket = new WebSocket(endpoint);
      socket.addEventListener("open", () => setStatus("Połączono"));
      socket.addEventListener("close", () => {{
        setStatus("Rozłączono. Ponawiam...", true);
        setTimeout(connect, 1200);
      }});
      socket.addEventListener("error", () => setStatus("Błąd połączenia", true));
      socket.addEventListener("message", (event) => {{
        const message = JSON.parse(event.data);
        if (message.type === "error") {{
          addLog("error", message.message || "Nieznany błąd");
          addWorkflowLog("server", "error", message.message || "Nieznany błąd");
          setStatus("Błąd", true);
          setBusy(false);
          return;
        }}
        if (message.type === "state") {{
          setBusy(message.state === "busy");
          if (message.label) setStatus(message.label, message.state === "error");
          return;
        }}
        if (message.type === "log") {{
          addWorkflowLog(
            message.stage || "workflow",
            message.status || "info",
            message.message || "",
            message.details || null
          );
          return;
        }}
        if (message.type === "view") {{
          if (message.data && message.data.status === "analyzing") {{
            setStatus("Analizuję...");
            setBusy(true);
          }}
          if (message.html) {{
            viewEl.srcdoc = message.html;
            lastResultQuery = promptEl.value.trim() || message.data?.transcription || "";
            lastViewId = message.data?.view_id ? String(message.data.view_id) : "";
            replaceUrl(Boolean(lastViewId));
            const answer = (message.data?.view_elements || []).find((item) => item.type === "answer");
            addLog("system", answer?.text || "Gotowe.");
            setStatus("Gotowe");
            setBusy(false);
          }}
        }}
      }});
    }}

    function sendText() {{
      const text = promptEl.value.trim();
      if (!text) return;
      if (busy) {{
        addWorkflowLog("client", "blocked", "Trwa poprzednie query. Przerwij je albo poczekaj na wynik.");
        return;
      }}
      if (!socket || socket.readyState !== WebSocket.OPEN) {{
        addLog("error", "WebSocket nie jest połączony.");
        return;
      }}
      lastResultQuery = text;
      lastViewId = "";
      replaceUrl(false);
      setBusy(true);
      socket.send(JSON.stringify({{
        type: "text",
        text,
        speak: speakEl.checked,
        logs: workflowLogs.slice(-50)
      }}));
      addLog("user", text);
      addWorkflowLog("client", "sent", "Wysłano query do workflow.", {{ text }});
      setStatus("Wysłano");
    }}

    function cancelQuery() {{
      if (!busy || !socket || socket.readyState !== WebSocket.OPEN) return;
      socket.send(JSON.stringify({{ type: "cancel" }}));
      addWorkflowLog("client", "cancel", "Użytkownik przerwał aktualne query.");
      setStatus("Przerywam...");
      cancelBtn.disabled = true;
    }}

    function setupSpeechRecognition() {{
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {{
        dictateBtn.disabled = true;
        dictateBtn.title = "Ta przeglądarka nie udostępnia Web Speech API.";
        return;
      }}
      recognition = new SpeechRecognition();
      recognition.lang = "pl-PL";
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.onstart = () => {{
        recognizing = true;
        dictateBtn.textContent = "Zatrzymaj";
        setStatus("Dyktowanie...");
      }};
      recognition.onend = () => {{
        recognizing = false;
        dictateBtn.textContent = "Dyktuj";
        setStatus(socket?.readyState === WebSocket.OPEN ? "Połączono" : "Rozłączono", socket?.readyState !== WebSocket.OPEN);
      }};
      recognition.onerror = (event) => addLog("error", event.error || "Błąd dyktowania");
      recognition.onresult = (event) => {{
        let finalText = "";
        let interim = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {{
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) finalText += transcript;
          else interim += transcript;
        }}
        const text = (finalText || interim).trim();
        if (text) {{
          promptEl.value = text;
          syncQueryUrl();
        }}
        if (finalText.trim()) sendText();
      }};
    }}

    sendBtn.addEventListener("click", sendText);
    cancelBtn.addEventListener("click", cancelQuery);
    clearBtn.addEventListener("click", () => {{
      promptEl.value = "";
      lastResultQuery = "";
      lastViewId = "";
      replaceUrl(false);
      promptEl.focus();
    }});
    promptEl.addEventListener("input", syncQueryUrl);
    promptEl.addEventListener("keydown", (event) => {{
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") sendText();
    }});
    copyQueryBtn.addEventListener("click", () => copyShareUrl(false));
    copyResultBtn.addEventListener("click", () => copyShareUrl(true));
    copyWorkflowLogsBtn.addEventListener("click", copyWorkflowLogs);
    dictateBtn.addEventListener("click", () => {{
      if (!recognition) return;
      recognizing ? recognition.stop() : recognition.start();
    }});
    themeInputs.forEach((input) => {{
      input.addEventListener("change", () => applyTheme(input.value));
    }});

    applyTheme(localStorage.getItem("tellm-theme") || "light");
    setupSpeechRecognition();
    restoreUrlState();
    connect();
    promptEl.focus();
  </script>
</body>
</html>"""


def _docs_html(host: str) -> str:
    ws_url = "ws://" + host
    return """<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>tellm v4 API docs</title>
  <style>
    :root {
      --bg: #f6f7f9;
      --panel: #ffffff;
      --text: #20242a;
      --muted: #5d6673;
      --line: #d9dee7;
      --accent: #0f766e;
      --code: #101828;
      --code-bg: #eef2f7;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      line-height: 1.55;
    }
    main {
      width: min(1040px, calc(100vw - 32px));
      margin: 0 auto;
      padding: 24px 0 40px;
    }
    header {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      gap: 16px;
      padding-bottom: 16px;
      border-bottom: 1px solid var(--line);
    }
    h1 { margin: 0; font-size: 28px; line-height: 1.1; }
    h2 { margin: 0 0 12px; font-size: 18px; }
    h3 { margin: 18px 0 8px; font-size: 15px; }
    a { color: var(--accent); font-weight: 650; text-decoration: none; }
    .muted { color: var(--muted); font-size: 14px; }
    .grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 16px;
      margin-top: 20px;
    }
    section {
      min-width: 0;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 16px;
    }
    section.full { grid-column: 1 / -1; }
    code {
      padding: 2px 5px;
      border-radius: 4px;
      background: var(--code-bg);
      color: var(--code);
    }
    pre {
      overflow: auto;
      margin: 10px 0 0;
      padding: 12px;
      border-radius: 6px;
      background: #111827;
      color: #e5e7eb;
      font-size: 13px;
      line-height: 1.45;
    }
    pre code { padding: 0; background: transparent; color: inherit; }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }
    th, td {
      padding: 9px 8px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }
    th { color: var(--muted); font-size: 12px; text-transform: uppercase; }
    @media (max-width: 820px) {
      main { width: min(100vw - 20px, 720px); padding-top: 16px; }
      header { align-items: flex-start; flex-direction: column; }
      .grid { grid-template-columns: 1fr; }
      section.full { grid-column: auto; }
    }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>tellm v4 API docs</h1>
        <div class="muted">HTTP docs + realtime WebSocket API</div>
      </div>
      <div><a href="/">Panel</a> · <a href="/registry-ui">Registry UI</a> · <a href="/autoimprovement">Autoimprovement</a> · <a href="/healthz">Health</a></div>
    </header>

    <div class="grid">
      <section>
        <h2>HTTP endpoints</h2>
        <table>
          <thead><tr><th>Metoda</th><th>Ścieżka</th><th>Opis</th></tr></thead>
          <tbody>
            <tr><td><code>GET</code></td><td><code>/</code></td><td>Panel HTML z inputem tekstowym i dyktowaniem.</td></tr>
            <tr><td><code>GET</code></td><td><code>/docs</code></td><td>Ta dokumentacja API.</td></tr>
            <tr><td><code>GET</code></td><td><code>/healthz</code></td><td>Health-check, zwraca <code>ok</code>.</td></tr>
            <tr><td><code>GET</code></td><td><code>/registry</code></td><td>Lista zasobów widocznych dla LLM, bez sekretów i bez referencji callable.</td></tr>
            <tr><td><code>GET</code></td><td><code>/manifest</code></td><td>Pełny Tellm Resource Manifest 1.0 z JSON Schema 2020-12.</td></tr>
            <tr><td><code>GET</code></td><td><code>/openapi.json</code></td><td>OpenAPI 3.1 opis HTTP API.</td></tr>
            <tr><td><code>GET</code></td><td><code>/asyncapi.json</code></td><td>AsyncAPI 3.1 opis WebSocket/event contracts.</td></tr>
            <tr><td><code>POST</code></td><td><code>/execute</code></td><td>Docelowy kontrakt HTTP execute; obecny transport zwraca JSON 501 i używa WebSocket <code>type=execute</code>.</td></tr>
            <tr><td><code>POST</code></td><td><code>/query</code></td><td>Docelowy kontrakt HTTP query; obecny transport zwraca JSON 501.</td></tr>
            <tr><td><code>POST</code></td><td><code>/autoimprovement/run</code></td><td>Docelowy kontrakt HTTP autoimprovement; obecny transport zwraca JSON 501.</td></tr>
            <tr><td><code>GET</code></td><td><code>/registry-ui</code></td><td>Techniczny widok zasobów registry.</td></tr>
            <tr><td><code>GET</code></td><td><code>/autoimprovement</code></td><td>Panel ręcznego uruchamiania audytu autoimprovement.</td></tr>
            <tr><td><code>GET</code></td><td><code>/autoimprovement/latest</code></td><td>Ostatni zapisany raport autoimprovement jako JSON + HTML.</td></tr>
            <tr><td><code>GET</code></td><td><code>/resource?uri=tellm://...</code></td><td>Metadata jednego zasobu z registry.</td></tr>
            <tr><td><code>GET</code></td><td><code>/schema?uri=tellm://...</code></td><td>Wszystkie schema przypisane do zasobu.</td></tr>
            <tr><td><code>GET</code></td><td><code>/schema/input?uri=tellm://...</code></td><td>Input schema zasobu.</td></tr>
            <tr><td><code>GET</code></td><td><code>/schema/output?uri=tellm://...</code></td><td>Output schema zasobu.</td></tr>
            <tr><td><code>GET</code></td><td><code>/describe?uri=tellm://...</code></td><td>Skrócony opis zasobu dla LLM/UI.</td></tr>
            <tr><td><code>GET</code></td><td><code>/permissions?uri=tellm://...</code></td><td>Uprawnienia i ryzyko zasobu.</td></tr>
            <tr><td><code>GET</code></td><td><code>/health?uri=tellm://...</code></td><td>Status zasobu i ostatnie wykonania.</td></tr>
            <tr><td><code>GET</code></td><td><code>/history?uri=tellm://...</code></td><td>Historia wykonań zasobu.</td></tr>
            <tr><td><code>GET</code></td><td><code>/validate-input?uri=...&amp;input=%7B...%7D</code></td><td>Walidacja inputu w obecnym transporcie diagnostycznym.</td></tr>
            <tr><td><code>GET</code></td><td><code>/validate-output?uri=...&amp;output=%7B...%7D</code></td><td>Walidacja outputu w obecnym transporcie diagnostycznym.</td></tr>
            <tr><td><code>GET</code></td><td><code>/resolve?uri=tellm://...</code></td><td>Diagnostyka resolvera: canonical URI, transport, schema, permissions.</td></tr>
          </tbody>
        </table>
      </section>

      <section>
        <h2>Realtime endpoint</h2>
        <p>Przetwarzanie komend działa przez WebSocket:</p>
        <p><code>__WS_URL__</code></p>
        <p class="muted">Obecny transport na tym porcie to WebSocket + diagnostyczne HTTP GET. Wykonanie zasobu używa wiadomości <code>{"type":"execute"}</code>. Pełne <code>POST /execute</code>, <code>POST /validate-input</code> i <code>POST /validate-output</code> są kontraktem dla adaptera HTTP, bo obecny serwer WebSocket nie udostępnia body requestu w <code>process_request</code>.</p>
      </section>

      <section class="full">
        <h2>Tellm Resource Registry</h2>
        <p>URI nie wykonuje akcji samo z siebie. URI wskazuje zasób w registry, a resolver dopiero potem decyduje, czy to lokalna funkcja, usługa, dane, zmienna env, ustawienie, widok albo proces.</p>
        <pre><code>{
  "uri": "tellm://service/domain/check",
  "kind": "service",
  "transport": "local",
  "input_schema": {
    "type": "object",
    "required": ["domain"]
  },
  "permissions": {
    "llm_discover": true,
    "llm_read": true,
    "llm_execute": true,
    "requires_confirmation": false,
    "danger_level": "network"
  }
}</code></pre>
        <h3>Discovery</h3>
        <pre><code>curl http://localhost:8008/registry
curl http://localhost:8008/manifest
curl http://localhost:8008/openapi.json
curl http://localhost:8008/asyncapi.json
curl "http://localhost:8008/resource?uri=tellm://service/domain/check"
curl "http://localhost:8008/resource?uri=tellm://service/price/search"
curl "http://localhost:8008/resource?uri=tellm://schema/service/weather.current/input"
curl "http://localhost:8008/schema/input?uri=tellm://service/weather/current"
curl "http://localhost:8008/schema/output?uri=tellm://service/weather/current"
curl "http://localhost:8008/schema/input?uri=tellm://service/price/search"
curl "http://localhost:8008/describe?uri=tellm://service/weather/current"
curl "http://localhost:8008/permissions?uri=tellm://service/weather/current"
curl "http://localhost:8008/health?uri=tellm://service/weather/current"
curl "http://localhost:8008/history?uri=tellm://service/weather/current"
curl "http://localhost:8008/validate-input?uri=tellm://service/weather/current&amp;input=%7B%22location%22%3A%22Wejherowo%22%2C%22country%22%3A%22PL%22%7D"
curl "http://localhost:8008/resolve?uri=tellm://function/system/now"
curl "http://localhost:8008/resolve?uri=tellm://artifact/audio/weather-query-sample"
curl "http://localhost:8008/resolve?uri=tellm://function/weather_wejherowo"
curl "http://localhost:8008/resolve?uri=tellm://service/weather/get&amp;input=%7B%22city%22%3A%22Wejherowo%22%2C%22country_code%22%3A%22PL%22%7D"
curl "http://localhost:8008/resolve?uri=tellm://prompt/validator/workflow-result&amp;include_value=true"
curl "http://localhost:8008/resolve?uri=tellm://view/workflow/35&amp;include_value=true"</code></pre>
      </section>

      <section class="full">
        <h2>Adresowalne artefakty</h2>
        <p>Registry traktuje usługi, pliki, media, komendy, paczki, prompty i wyniki workflow jako zasoby z URI. URI jest stabilne, a fizyczny storage może być lokalnym plikiem, SQLite albo inline content.</p>
        <pre><code>tellm://artifact/audio/weather-query-sample
tellm://media/audio/weather-query-sample
tellm://file/project/tellm/server.py
tellm://file/output/test-audio/tellm-pl-pogoda.webm
tellm://command/shell/pytest
tellm://package/python/litellm
tellm://package/python/jsonschema
tellm://prompt/validator/workflow-result
tellm://python/module/tellm.bot
tellm://workflow/run/35
tellm://view/workflow/35
tellm://log/workflow/35
tellm://artifact/json/workflow-result/35</code></pre>
        <h3>Artefakty i storage</h3>
        <pre><code>curl "http://localhost:8008/resource?uri=tellm://artifact/audio/weather-query-sample"
curl "http://localhost:8008/resource?uri=tellm://media/audio/weather-query-sample"
curl "http://localhost:8008/resource?uri=tellm://command/shell/pytest"
curl "http://localhost:8008/resource?uri=tellm://package/python/litellm"
curl "http://localhost:8008/resource?uri=tellm://workflow/run/35"
curl "http://localhost:8008/resource?uri=tellm://log/workflow/35"
curl "http://localhost:8008/resolve?uri=tellm://artifact/audio/weather-query-sample"
curl "http://localhost:8008/resolve?uri=tellm://view/workflow/35&amp;include_value=true"
curl "http://localhost:8008/registry?kind=artifact"
curl "http://localhost:8008/registry?kind=command"
curl "http://localhost:8008/registry?kind=package"
curl "http://localhost:8008/registry?domain=weather"
curl "http://localhost:8008/registry?capability=weather.current"
curl "http://localhost:8008/registry?capability=price.search"
curl "http://localhost:8008/registry?status=deprecated"</code></pre>
      </section>

      <section class="full">
        <h2>Standards</h2>
        <table>
          <thead><tr><th>Obszar</th><th>Standard</th></tr></thead>
          <tbody>
            <tr><td>URI</td><td>RFC 3986 + scheme <code>tellm://</code></td></tr>
            <tr><td>JSON validation</td><td>JSON Schema Draft 2020-12</td></tr>
            <tr><td>HTTP API</td><td>OpenAPI 3.1</td></tr>
            <tr><td>Events/WebSocket</td><td>AsyncAPI 3.1</td></tr>
            <tr><td>Registry</td><td>TRM — Tellm Resource Manifest 1.0</td></tr>
            <tr><td>Service result</td><td>TSR — Tellm Service Result 1.0</td></tr>
          </tbody>
        </table>
        <p>Każdy wpis registry ma <code>manifest_version</code>, <code>version</code>, <code>schema_version</code>, <code>permissions</code>, <code>data_policy</code>, <code>render</code> oraz schema z <code>$schema</code>.</p>
      </section>

      <section class="full">
        <h2>Udostępnianie zapytań</h2>
        <p>Panel zapisuje aktualne pytanie w URL jako <code>?q=...</code>. Po wygenerowaniu wyniku link dostaje także <code>view_id</code>, np. <code>/?q=utworz%20raport&amp;view_id=12</code>. Taki link otwiera edytowalne zapytanie i odtwarza zapisany wynik z SQLite.</p>
        <table>
          <thead><tr><th>URL</th><th>Opis</th></tr></thead>
          <tbody>
            <tr><td><code>/?q=tekst</code></td><td>Wczytuje tekst do pola zapytania, gotowy do edycji albo wysłania.</td></tr>
            <tr><td><code>/?q=tekst&amp;view_id=12</code></td><td>Wczytuje tekst i pokazuje zapisany wynik.</td></tr>
            <tr><td><code>/views/12</code></td><td>Zwraca zapisany HTML wyniku.</td></tr>
          </tbody>
        </table>
      </section>

      <section class="full">
        <h2>Tekst przez WebSocket</h2>
        <h3>Request</h3>
        <pre><code>{
  "type": "text",
  "text": "utwórz zadanie na jutro",
  "speak": false
}</code></pre>
        <h3>JavaScript</h3>
        <pre><code>const ws = new WebSocket("__WS_URL__");
ws.onmessage = (event) => console.log(JSON.parse(event.data));
ws.onopen = () => ws.send(JSON.stringify({
  type: "text",
  text: "utwórz zadanie na jutro",
  speak: false
}));</code></pre>
      </section>

      <section class="full">
        <h2>Execute przez Registry</h2>
        <p>Dla zadań wykonawczych LLM powinien wybrać istniejące URI albo wygenerować bezpieczny proces. Końcowe dane użytkownika pochodzą z lokalnej funkcji/usługi jako schema-valid JSON, a nie z wolnego tekstu LLM.</p>
        <h3>WebSocket</h3>
        <pre><code>{
  "type": "execute",
  "uri": "tellm://service/domain/check",
  "input": {"domain": "example.pl"},
  "speak": false
}</code></pre>
        <h3>Aktualna pogoda</h3>
        <pre><code>{
  "type": "execute",
  "uri": "tellm://service/weather/current",
  "input": {"city": "Wejherowo", "country": "PL"}
}</code></pre>
        <h3>Cena produktu</h3>
        <pre><code>{
  "type": "execute",
  "uri": "tellm://service/price/search",
  "input": {"query": "cukier", "site": "skapiec.pl"}
}</code></pre>
        <h3>Docelowy REST kontrakt</h3>
        <pre><code>POST /execute
Content-Type: application/json

{
  "uri": "tellm://function/system/now",
  "input": {}
}</code></pre>
        <h3>Standardowy wynik usługi</h3>
        <pre><code>{
  "ok": true,
  "type": "domain.availability.result",
  "uri": "tellm://service/domain/check",
  "data": {},
  "message": {
    "title": "...",
    "summary": "...",
    "details": "To wynik lokalnej usługi, nie bezpośrednia odpowiedź LLM."
  },
  "view": {"renderer": "auto"},
  "errors": []
}</code></pre>
      </section>

      <section class="full">
        <h2>Autoimprovement</h2>
        <p>Autoimprovement działa jako kontrolowany audyt. Domyślnie <code>dry_run=true</code> i <code>allow_auto_apply=false</code>, więc system zapisuje raport oraz pending patch descriptors, ale nie nadpisuje kodu.</p>
        <pre><code>{
  "type": "execute",
  "uri": "tellm://service/system/autoimprove",
  "input": {
    "mode": "manual",
    "scope": "registry",
    "max_cycles": 10,
    "dry_run": true,
    "allow_auto_apply": false
  }
}</code></pre>
        <p>Powiązane zasoby: <code>tellm://event/cron/hourly</code>, <code>tellm://event/workflow/every-10-cycles</code>, <code>tellm://data/system/execution-history</code>, <code>tellm://data/system/registry-health</code>, <code>tellm://data/system/autoimprovement-report/latest</code>.</p>
      </section>

      <section class="full">
        <h2>Data source validation</h2>
        <p>Zapytania wymagające aktualnych danych zewnętrznych, np. pogoda, ceny albo domeny, dostają dodatkowy etap <code>data_source</code>. Jeśli wynik używa <code>local_simulation</code>, <code>mock</code> albo <code>llm_generated</code>, workflow pokazuje ostrzeżenie i zapisuje finding dla autoimprovement.</p>
        <p>Pytania o ceny powinny używać <code>tellm://service/price/search</code>. <code>tellm://service/domain/check</code> sprawdza tylko status domeny i nie jest poprawną odpowiedzią na pytanie o cenę produktu.</p>
        <pre><code>{
  "type": "log",
  "stage": "data_source",
  "status": "warning",
  "message": "Wykryto problem jakości źródła danych."
}</code></pre>
      </section>

      <section class="full">
        <h2>Kontrakt LLM JSON</h2>
        <p>LLM powinien zwrócić JSON. Pole <code>function_name</code> może być URI z registry. Pole <code>view</code> jest strukturą danych dla dynamicznego renderera, a <code>processes</code> opisuje funkcje Python wykonywane jako procesy backendu, gdy nie ma jeszcze gotowej usługi.</p>
        <pre><code>{
  "type": "now",
  "function_name": "tellm://service/domain/check",
  "parameters": {"domain": "example.pl"},
  "view": {
    "title": "Sprawdzenie domeny",
    "blocks": [
      {"type": "heading", "text": "Wynik lokalnej usługi", "level": 2},
      {"type": "metric", "label": "Źródło", "value": "registry"},
      {"type": "json", "data": {"source": "registry"}}
    ]
  },
  "processes": [
    {
      "name": "run",
      "language": "python",
      "entrypoint": "run",
      "parameters": {"city": "Warszawa"},
      "code": "def run(params):\\n    return {'city': params['city'], 'ok': True}"
    }
  ]
}</code></pre>
        <p class="muted">Renderer obsługuje bloki <code>heading</code>, <code>text</code>, <code>metric</code>, <code>list</code>, <code>table</code>, <code>code</code> i <code>json</code>. Kod procesu ma definiować funkcję przyjmującą jeden argument <code>params</code>.</p>
      </section>

      <section class="full">
        <h2>Workflow z walidacją</h2>
        <p>Podczas jednego query panel blokuje kolejne wysyłki. Użytkownik może wysłać <code>{"type": "cancel"}</code>, aby przerwać aktywną pracę. Backend emituje logi, które panel pokazuje i dołącza do kolejnych zapytań.</p>
        <pre><code>user query
  -> LLM JSON task/view/processes
  -> Python functions/processes
  -> dynamic HTML render
  -> renderer logs + client logs
  -> LLM validation
  -> OK albo repair view/result i ponowny render</code></pre>
        <h3>Event log</h3>
        <pre><code>{
  "type": "log",
  "stage": "renderer",
  "status": "ok",
  "message": "HTML wyrenderowany",
  "details": {"html_length": 1234}
}</code></pre>
        <h3>Cancel</h3>
        <pre><code>{
  "type": "cancel"
}</code></pre>
      </section>

      <section class="full">
        <h2>Speech z WebRTC media capture</h2>
        <p>Przeglądarka pobiera mikrofon przez <code>navigator.mediaDevices.getUserMedia</code>, nagrywa fragment przez <code>MediaRecorder</code>, a potem wysyła data URL audio do WebSocket. Backend rozpoznaje typy <code>audio/webm</code>, <code>audio/wav</code>, <code>audio/ogg</code> i <code>audio/mp4</code>.</p>
        <pre><code>const ws = new WebSocket("__WS_URL__");

async function recordAndSend() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
  const chunks = [];

  recorder.ondataavailable = (event) => chunks.push(event.data);
  recorder.onstop = () => {
    const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
    const reader = new FileReader();
    reader.onloadend = () => ws.send(JSON.stringify({
      type: "audio",
      audio: reader.result,
      speak: false
    }));
    reader.readAsDataURL(blob);
    stream.getTracks().forEach((track) => track.stop());
  };

  recorder.start();
  setTimeout(() => recorder.stop(), 3500);
}</code></pre>
      </section>

      <section class="full">
        <h2>Response events</h2>
        <h3>Analiza rozpoczęta</h3>
        <pre><code>{
  "type": "view",
  "data": {
    "transcription": "utwórz zadanie na jutro",
    "status": "analyzing"
  }
}</code></pre>
        <h3>Wynik końcowy</h3>
        <pre><code>{
  "type": "view",
  "data": {
    "transcription": "...",
    "task": {"type": "now", "function": "name", "parameters": {}},
    "result": {},
    "view_elements": []
  },
  "html": "&lt;html&gt;...&lt;/html&gt;"
}</code></pre>
        <h3>Błąd</h3>
        <pre><code>{
  "type": "error",
  "message": "opis błędu"
}</code></pre>
      </section>
    </div>
  </main>
</body>
</html>""".replace("__WS_URL__", ws_url)


def _registry_ui_html(bot: TellmBot, host: str) -> str:
    rows = []
    for entry in bot.registry.discover_for_llm():
        perms = entry.get("permissions") or {}
        rows.append(
            "<tr>"
            + "<td><code>" + html_lib.escape(str(entry.get("uri", ""))) + "</code></td>"
            + "<td>" + html_lib.escape(str(entry.get("kind", ""))) + "</td>"
            + "<td>" + html_lib.escape(str(entry.get("name", ""))) + "</td>"
            + "<td>" + html_lib.escape(str(perms.get("danger_level", ""))) + "</td>"
            + "<td>" + ("yes" if perms.get("llm_execute") else "no") + "</td>"
            + "<td>" + ("yes" if perms.get("requires_confirmation") else "no") + "</td>"
            + "<td>" + html_lib.escape(", ".join(entry.get("tags") or [])) + "</td>"
            + "</tr>"
        )
    return """<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>tellm registry UI</title>
  <style>
    body { margin: 0; background: #f6f7f9; color: #20242a; font-family: system-ui, sans-serif; }
    main { width: min(1180px, calc(100vw - 32px)); margin: 0 auto; padding: 24px 0 40px; }
    header { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; padding-bottom: 16px; border-bottom: 1px solid #d9dee7; }
    h1 { margin: 0; font-size: 28px; }
    a { color: #0f766e; font-weight: 650; text-decoration: none; }
    table { width: 100%; border-collapse: collapse; margin-top: 18px; background: #fff; border: 1px solid #d9dee7; }
    th, td { padding: 9px 8px; border-bottom: 1px solid #d9dee7; text-align: left; vertical-align: top; font-size: 14px; }
    th { color: #5d6673; font-size: 12px; text-transform: uppercase; }
    code { padding: 2px 5px; border-radius: 4px; background: #eef2f7; color: #101828; }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Registry UI</h1>
        <div>""" + html_lib.escape(str(len(rows))) + """ LLM-discoverable resources</div>
      </div>
      <div><a href="/">Panel</a> · <a href="/autoimprovement">Autoimprovement</a> · <a href="/registry">JSON</a> · <a href="/docs">Docs</a></div>
    </header>
    <table>
      <thead><tr><th>URI</th><th>Kind</th><th>Name</th><th>Risk</th><th>Exec</th><th>Confirm</th><th>Tags</th></tr></thead>
      <tbody>""" + "".join(rows) + """</tbody>
    </table>
  </main>
</body>
</html>"""


def _autoimprovement_html(host: str) -> str:
    ws_url = "ws://" + host
    return """<!doctype html>
<html lang="pl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>tellm autoimprovement</title>
  <style>
    body { margin: 0; background: #f6f7f9; color: #20242a; font-family: system-ui, sans-serif; }
    main { width: min(1180px, calc(100vw - 32px)); margin: 0 auto; padding: 24px 0 40px; }
    header { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; padding-bottom: 16px; border-bottom: 1px solid #d9dee7; }
    h1 { margin: 0; font-size: 28px; }
    h2 { margin: 0 0 12px; font-size: 16px; }
    a { color: #0f766e; font-weight: 650; text-decoration: none; }
    .grid { display: grid; grid-template-columns: minmax(0, 360px) minmax(0, 1fr); gap: 16px; margin-top: 18px; }
    .panel { min-width: 0; background: #fff; border: 1px solid #d9dee7; border-radius: 8px; padding: 16px; }
    button { min-height: 38px; border: 1px solid #0f766e; border-radius: 6px; padding: 0 12px; background: #0f766e; color: #fff; font: inherit; font-weight: 650; cursor: pointer; }
    button:disabled { opacity: .55; cursor: not-allowed; }
    pre { overflow: auto; max-height: 330px; margin: 0; padding: 12px; border-radius: 6px; background: #111827; color: #e5e7eb; font-size: 13px; line-height: 1.45; }
    iframe { width: 100%; min-height: 560px; border: 1px solid #d9dee7; border-radius: 6px; background: #fff; }
    .status { color: #5d6673; margin-top: 10px; }
    @media (max-width: 840px) { .grid { grid-template-columns: 1fr; } }
  </style>
</head>
<body>
  <main>
    <header>
      <div>
        <h1>Autoimprovement</h1>
        <div>tellm://service/system/autoimprove</div>
      </div>
      <div><a href="/">Panel</a> · <a href="/registry-ui">Registry UI</a> · <a href="/docs">Docs</a></div>
    </header>
    <div class="grid">
      <section class="panel">
        <h2>Run</h2>
        <button id="run" type="button">Run dry-run audit</button>
        <div id="status" class="status">Idle</div>
      </section>
      <section class="panel">
        <h2>Latest JSON</h2>
        <pre id="json">Loading...</pre>
      </section>
      <section class="panel">
        <h2>Events</h2>
        <pre id="events"></pre>
      </section>
      <section class="panel">
        <h2>Report HTML</h2>
        <iframe id="view" title="autoimprovement report"></iframe>
      </section>
    </div>
  </main>
  <script>
    const endpoint = "__WS_URL__";
    const runBtn = document.getElementById("run");
    const statusEl = document.getElementById("status");
    const jsonEl = document.getElementById("json");
    const eventsEl = document.getElementById("events");
    const viewEl = document.getElementById("view");
    let socket;

    function log(event) {
      eventsEl.textContent = JSON.stringify(event, null, 2) + "\\n\\n" + eventsEl.textContent;
    }
    async function loadLatest() {
      const response = await fetch("/autoimprovement/latest");
      const data = await response.json();
      jsonEl.textContent = JSON.stringify(data.report || data, null, 2);
      if (data.html) viewEl.srcdoc = data.html;
    }
    function connect() {
      socket = new WebSocket(endpoint);
      socket.addEventListener("open", () => statusEl.textContent = "Connected");
      socket.addEventListener("close", () => {
        statusEl.textContent = "Disconnected";
        setTimeout(connect, 1200);
      });
      socket.addEventListener("message", (event) => {
        const message = JSON.parse(event.data);
        log(message);
        if (message.type === "state") {
          runBtn.disabled = message.state === "busy";
          statusEl.textContent = message.label || message.state;
        }
        if (message.html) {
          viewEl.srcdoc = message.html;
          jsonEl.textContent = JSON.stringify(message.data.result, null, 2);
          loadLatest();
        }
      });
    }
    runBtn.addEventListener("click", () => {
      if (!socket || socket.readyState !== WebSocket.OPEN) return;
      runBtn.disabled = true;
      socket.send(JSON.stringify({
        type: "execute",
        uri: "tellm://service/system/autoimprove",
        input: {
          mode: "manual",
          scope: "registry",
          max_cycles: 10,
          dry_run: true,
          allow_auto_apply: false,
          allow_code_generation: true
        }
      }));
    });
    loadLatest();
    connect();
  </script>
</body>
</html>""".replace("__WS_URL__", ws_url)


def _openapi_document(host: str) -> dict:
    return {
        "openapi": "3.1.0",
        "jsonSchemaDialect": "https://json-schema.org/draft/2020-12/schema",
        "info": {
            "title": "tellm API",
            "version": "4.0.3",
            "description": "HTTP discovery endpoints for tellm Resource Manifest and WebSocket execution contract.",
        },
        "servers": [{"url": "http://" + host}],
        "paths": {
            "/registry": {
                "get": {
                    "summary": "List LLM-discoverable registry resources.",
                    "responses": {"200": {"description": "Registry entries"}},
                }
            },
            "/execute": {
                "post": {
                    "summary": "Execute a registry resource by URI.",
                    "description": "Contract for HTTP adapters. The current WebSocket-backed server returns 501 and supports the same payload via WebSocket type=execute.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ExecuteRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Service result",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TellmServiceResult"}
                                }
                            },
                        },
                        "501": {"description": "HTTP body transport not enabled"},
                    },
                }
            },
            "/query": {
                "post": {
                    "summary": "Submit a text query.",
                    "description": "Contract for HTTP adapters. The current server accepts query execution over WebSocket.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/QueryRequest"}
                            }
                        },
                    },
                    "responses": {
                        "200": {"description": "Rendered workflow result"},
                        "501": {"description": "HTTP body transport not enabled"},
                    },
                }
            },
            "/autoimprovement/run": {
                "post": {
                    "summary": "Run autoimprovement audit.",
                    "description": "Contract for HTTP adapters. The current server supports this through WebSocket type=execute with tellm://service/system/autoimprove.",
                    "requestBody": {
                        "required": False,
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Autoimprovement service result",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TellmServiceResult"}
                                }
                            },
                        },
                        "501": {"description": "HTTP body transport not enabled"},
                    },
                }
            },
            "/manifest": {
                "get": {
                    "summary": "Return Tellm Resource Manifest 1.0.",
                    "responses": {
                        "200": {
                            "description": "Tellm Resource Manifest",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TellmRegistryManifest"}
                                }
                            },
                        }
                    },
                }
            },
            "/resource": {
                "get": {
                    "summary": "Resolve one resource manifest by URI.",
                    "parameters": [
                        {
                            "name": "uri",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uri"},
                        }
                    ],
                    "responses": {"200": {"description": "Resource manifest"}},
                }
            },
            "/schema": {
                "get": {
                    "summary": "Return all schemas for a registry resource.",
                    "parameters": [
                        {
                            "name": "uri",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uri"},
                        }
                    ],
                    "responses": {"200": {"description": "Schema bundle"}},
                }
            },
            "/schema/input": {
                "get": {
                    "summary": "Return input schema for a registry resource.",
                    "parameters": [
                        {
                            "name": "uri",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uri"},
                        }
                    ],
                    "responses": {"200": {"description": "Input schema"}},
                }
            },
            "/schema/output": {
                "get": {
                    "summary": "Return output schema for a registry resource.",
                    "parameters": [
                        {
                            "name": "uri",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uri"},
                        }
                    ],
                    "responses": {"200": {"description": "Output schema"}},
                }
            },
            "/describe": {
                "get": {
                    "summary": "Return a compact resource description for LLM/UI.",
                    "parameters": [
                        {
                            "name": "uri",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uri"},
                        }
                    ],
                    "responses": {"200": {"description": "Resource description"}},
                }
            },
            "/permissions": {
                "get": {
                    "summary": "Return resource permissions.",
                    "parameters": [
                        {
                            "name": "uri",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uri"},
                        }
                    ],
                    "responses": {"200": {"description": "Resource permissions"}},
                }
            },
            "/health": {
                "get": {
                    "summary": "Return resource health based on execution history.",
                    "parameters": [
                        {
                            "name": "uri",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uri"},
                        }
                    ],
                    "responses": {"200": {"description": "Resource health"}},
                }
            },
            "/history": {
                "get": {
                    "summary": "Return recent execution history for a resource.",
                    "parameters": [
                        {
                            "name": "uri",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uri"},
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "integer", "default": 20},
                        },
                    ],
                    "responses": {"200": {"description": "Execution history"}},
                }
            },
            "/validate-input": {
                "get": {
                    "summary": "Validate input JSON against a resource input schema.",
                    "description": "Diagnostic GET variant for this WebSocket-backed server. HTTP adapters should expose the same contract as POST with JSON body.",
                    "parameters": [
                        {
                            "name": "uri",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uri"},
                        },
                        {
                            "name": "input",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "description": "JSON object encoded as a query parameter"},
                        },
                    ],
                    "responses": {"200": {"description": "Validation result"}, "400": {"description": "Invalid input"}},
                }
            },
            "/validate-output": {
                "get": {
                    "summary": "Validate output JSON against a resource output schema.",
                    "description": "Diagnostic GET variant for this WebSocket-backed server. HTTP adapters should expose the same contract as POST with JSON body.",
                    "parameters": [
                        {
                            "name": "uri",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uri"},
                        },
                        {
                            "name": "output",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "description": "JSON object encoded as a query parameter"},
                        },
                    ],
                    "responses": {"200": {"description": "Validation result"}, "400": {"description": "Invalid output"}},
                }
            },
            "/resolve": {
                "get": {
                    "summary": "Resolve one resource including diagnostic private flags.",
                    "parameters": [
                        {
                            "name": "uri",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string", "format": "uri"},
                        }
                    ],
                    "responses": {"200": {"description": "Resolved resource"}},
                }
            },
            "/views/{view_id}": {
                "get": {
                    "summary": "Return saved HTML view.",
                    "parameters": [
                        {
                            "name": "view_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "integer"},
                        }
                    ],
                    "responses": {"200": {"description": "Saved HTML view"}},
                }
            },
            "/autoimprovement/latest": {
                "get": {
                    "summary": "Return latest autoimprovement report JSON and HTML.",
                    "responses": {"200": {"description": "Latest report"}},
                }
            },
        },
        "components": {
            "schemas": {
                "TellmResourceManifest": registry_manifest_schema(),
                "TellmServiceResult": service_result_schema(),
                "ExecuteRequest": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": ["uri"],
                    "properties": {
                        "uri": {"type": "string", "format": "uri"},
                        "input": {"type": "object"},
                    },
                    "additionalProperties": False,
                },
                "QueryRequest": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {"type": "string"},
                        "speak": {"type": "boolean"},
                    },
                    "additionalProperties": False,
                },
                "TellmRegistryManifest": {
                    "$schema": "https://json-schema.org/draft/2020-12/schema",
                    "type": "object",
                    "required": ["manifest_version", "schema_version", "resources"],
                    "properties": {
                        "manifest_version": {"type": "string"},
                        "schema_version": {"type": "string"},
                        "resources": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/TellmResourceManifest"},
                        },
                    },
                },
            }
        },
    }


def _asyncapi_document(host: str) -> dict:
    return {
        "asyncapi": "3.1.0",
        "info": {
            "title": "tellm Events",
            "version": "4.0.3",
            "description": "WebSocket events and registry event resources for tellm.",
        },
        "servers": {
            "localWebSocket": {
                "host": host,
                "protocol": "ws",
                "pathname": "/",
            }
        },
        "channels": {
            "workflow": {
                "address": "/",
                "messages": {
                    "clientText": {"$ref": "#/components/messages/ClientText"},
                    "clientExecute": {"$ref": "#/components/messages/ClientExecute"},
                    "serverLog": {"$ref": "#/components/messages/ServerLog"},
                    "serverState": {"$ref": "#/components/messages/ServerState"},
                    "serverView": {"$ref": "#/components/messages/ServerView"},
                },
            },
            "tellm://event/cron/hourly": {
                "address": "tellm://event/cron/hourly",
                "messages": {"event": {"$ref": "#/components/messages/RegistryEvent"}},
            },
            "tellm://event/workflow/every-10-cycles": {
                "address": "tellm://event/workflow/every-10-cycles",
                "messages": {"event": {"$ref": "#/components/messages/RegistryEvent"}},
            },
        },
        "operations": {
            "sendTextQuery": {
                "action": "send",
                "channel": {"$ref": "#/channels/workflow"},
                "messages": [{"$ref": "#/components/messages/ClientText"}],
            },
            "executeRegistryResource": {
                "action": "send",
                "channel": {"$ref": "#/channels/workflow"},
                "messages": [{"$ref": "#/components/messages/ClientExecute"}],
            },
            "receiveWorkflowEvents": {
                "action": "receive",
                "channel": {"$ref": "#/channels/workflow"},
                "messages": [
                    {"$ref": "#/components/messages/ServerLog"},
                    {"$ref": "#/components/messages/ServerState"},
                    {"$ref": "#/components/messages/ServerView"},
                ],
            },
        },
        "components": {
            "messages": {
                "ClientText": {
                    "payload": {
                        "type": "object",
                        "required": ["type", "text"],
                        "properties": {
                            "type": {"const": "text"},
                            "text": {"type": "string"},
                            "speak": {"type": "boolean"},
                            "logs": {"type": "array"},
                        },
                    }
                },
                "ClientExecute": {
                    "payload": {
                        "type": "object",
                        "required": ["type", "uri"],
                        "properties": {
                            "type": {"const": "execute"},
                            "uri": {"type": "string"},
                            "input": {"type": "object"},
                            "speak": {"type": "boolean"},
                        },
                    }
                },
                "ServerLog": {
                    "payload": {
                        "type": "object",
                        "required": ["type", "stage", "status", "message"],
                        "properties": {
                            "type": {"const": "log"},
                            "stage": {"type": "string"},
                            "status": {"type": "string"},
                            "message": {"type": "string"},
                            "details": {"type": "object"},
                        },
                    }
                },
                "ServerState": {
                    "payload": {
                        "type": "object",
                        "required": ["type", "state"],
                        "properties": {
                            "type": {"const": "state"},
                            "state": {"type": "string"},
                            "label": {"type": "string"},
                        },
                    }
                },
                "ServerView": {
                    "payload": {
                        "type": "object",
                        "required": ["type", "data"],
                        "properties": {
                            "type": {"const": "view"},
                            "data": {"type": "object"},
                            "html": {"type": "string"},
                        },
                    }
                },
                "RegistryEvent": {
                    "payload": registry_manifest_schema(),
                },
            }
        },
    }


class TellmServer:
    def __init__(self, host: str = "localhost", port: int = 8000, db_path: str = "tellm.db"):
        self.host = host
        self.port = port
        self.bot = TellmBot(db_path=db_path)

    def register_function(self, name: str, func):
        self.bot.register_function(name, func)

    def _http_response(
        self, body: bytes, content_type: str, status: HTTPStatus = HTTPStatus.OK
    ) -> Response:
        headers = Headers()
        headers["Content-Type"] = content_type
        headers["Content-Length"] = str(len(body))
        return Response(status, status.phrase, headers, body)

    def _json_response(
        self, data, status: HTTPStatus = HTTPStatus.OK
    ) -> Response:
        return self._http_response(
            json.dumps(data, ensure_ascii=False, default=str).encode("utf-8"),
            "application/json; charset=utf-8",
            status,
        )

    def _resource_entry_response(self, uri: str):
        if not uri:
            return None, self._json_response(
                {"ok": False, "error": {"code": "MISSING_URI", "message": "missing uri"}},
                HTTPStatus.BAD_REQUEST,
            )
        entry = self.bot.registry.get(uri)
        if entry is None or not entry.permissions.get("llm_discover"):
            return None, self._json_response(
                {
                    "ok": False,
                    "error": {
                        "code": "RESOURCE_NOT_FOUND",
                        "message": "resource not found",
                        "uri": uri,
                    },
                },
                HTTPStatus.NOT_FOUND,
            )
        return entry, None

    @staticmethod
    def _registry_item_summary(entry):
        return {
            "uri": entry.uri,
            "kind": entry.kind,
            "name": entry.name,
            "description": entry.description,
            "canonical_uri": entry.canonical_uri,
            "domain": entry.domain,
            "has_input_schema": bool(entry.input_schema),
            "has_output_schema": bool(entry.output_schema),
            "has_value_schema": bool(entry.value_schema),
            "llm_execute": bool(entry.permissions.get("llm_execute")),
            "requires_confirmation": bool(entry.permissions.get("requires_confirmation")),
            "danger_level": entry.permissions.get("danger_level", "read_only"),
            "storage_type": entry.storage.get("type", "") if entry.storage else "",
            "content_type": entry.content_type,
            "media_type": entry.media_type,
            "capabilities": entry.capabilities,
            "tags": entry.tags,
            "status": entry.status,
            "replacement": entry.replacement,
        }

    def _virtual_schema_resource(self, uri: str):
        for entry in self.bot.registry.list():
            schemas = [
                ("input", entry.input_schema),
                ("output", entry.output_schema),
                ("value", entry.value_schema),
                ("metadata", entry.metadata_schema),
            ]
            for schema_kind, schema in schemas:
                if not isinstance(schema, dict) or schema.get("$id") != uri:
                    continue
                return {
                    "manifest_version": "1.0.0",
                    "uri": uri,
                    "kind": "schema",
                    "name": entry.name + "." + schema_kind,
                    "description": "%s schema for %s." % (schema_kind, entry.uri),
                    "version": entry.version,
                    "schema_version": entry.schema_version,
                    "compatibility": entry.compatibility,
                    "transport": {
                        "type": "registry-ref",
                        "resource_uri": entry.uri,
                        "schema": schema_kind,
                    },
                    "input_schema": None,
                    "output_schema": None,
                    "value_schema": schema,
                    "metadata_schema": None,
                    "permissions": {
                        "llm_discover": True,
                        "llm_read": True,
                        "llm_write": False,
                        "llm_execute": False,
                        "requires_confirmation": False,
                        "network": False,
                        "filesystem_read": False,
                        "filesystem_write": False,
                        "shell": False,
                        "env_read": False,
                        "env_write": False,
                        "danger_level": "safe",
                    },
                    "data_policy": {},
                    "render": {"renderer": "auto"},
                    "tags": ["schema", entry.kind, schema_kind],
                    "status": entry.status,
                    "metadata": {"resource_uri": entry.uri, "schema": schema_kind},
                    "aliases": [],
                    "masked": False,
                }
        return None

    def _virtual_view_resource(self, uri: str):
        prefixes = [
            ("tellm://workflow/run/", "workflow", "application/json", "workflow_run"),
            ("tellm://log/workflow/", "log", "application/json", "workflow_log"),
            ("tellm://view/workflow/", "view", "text/html", "workflow_view"),
            ("tellm://artifact/html/view/", "artifact", "text/html", "html_artifact"),
            ("tellm://artifact/json/workflow-result/", "artifact", "application/json", "json_artifact"),
        ]
        matched = None
        for prefix, kind, content_type, resource_type in prefixes:
            if uri.startswith(prefix):
                matched = (prefix, kind, content_type, resource_type)
                break
        if not matched:
            return None
        prefix, kind, content_type, resource_type = matched
        try:
            view_id = int(uri[len(prefix) :])
        except ValueError:
            return None
        record = self.bot.get_view_record(view_id)
        if not record:
            return None
        if resource_type == "workflow_run":
            value_schema = {"type": "object"}
            storage_column = "record"
            relations = {
                "output_artifacts": [
                    "tellm://artifact/json/workflow-result/%d" % view_id,
                    "tellm://view/workflow/%d" % view_id,
                    "tellm://log/workflow/%d" % view_id,
                ],
                "rendered_as": ["tellm://view/workflow/%d" % view_id],
                "log": ["tellm://log/workflow/%d" % view_id],
            }
            name = "workflow_run_%d" % view_id
            description = "Runtime workflow run reconstructed from the views table."
            tags = ["workflow", "run", "artifact"]
        elif resource_type == "workflow_log":
            value_schema = {"type": "object"}
            storage_column = "result_data"
            relations = {
                "describes": ["tellm://workflow/run/%d" % view_id],
                "derived_from": ["tellm://artifact/json/workflow-result/%d" % view_id],
            }
            name = "workflow_log_%d" % view_id
            description = "Runtime workflow log resource reconstructed from persisted workflow data."
            tags = ["workflow", "log", "artifact"]
        elif content_type == "application/json":
            value_schema = {"type": "object"}
            storage_column = "result_data"
            relations = {"rendered_as": ["tellm://view/workflow/%d" % view_id]}
            name = "workflow_result_%d" % view_id
            description = "Runtime JSON artifact stored in the views table."
            tags = ["workflow", "view", "artifact"]
        else:
            value_schema = {"type": "string"}
            storage_column = "html"
            relations = {"derived_from": ["tellm://artifact/json/workflow-result/%d" % view_id]}
            name = "workflow_view_%d" % view_id
            description = "Runtime HTML view stored in the views table."
            tags = ["workflow", "view", "artifact"]
        return {
            "manifest_version": "1.0.0",
            "uri": uri,
            "kind": kind,
            "name": name,
            "description": description,
            "version": "1.0.0",
            "schema_version": "2020-12",
            "compatibility": {"breaking_change": False, "deprecated": False},
            "transport": {"type": "sqlite", "table": "views", "id": view_id},
            "input_schema": None,
            "output_schema": None,
            "value_schema": value_schema,
            "metadata_schema": None,
            "permissions": {
                "llm_discover": True,
                "llm_read": True,
                "llm_write": False,
                "llm_execute": False,
                "requires_confirmation": False,
                "network": False,
                "filesystem_read": False,
                "filesystem_write": False,
                "shell": False,
                "env_read": False,
                "env_write": False,
                "danger_level": "read_only",
            },
            "data_policy": {},
            "render": {"renderer": "auto"},
            "storage": {
                "type": "sqlite",
                "table": "views",
                "id": view_id,
                "column": storage_column,
            },
            "relations": relations,
            "dependencies": [],
            "capabilities": [],
            "content_type": content_type,
            "media_type": "",
            "command_template": "",
            "ecosystem": "",
            "import_name": "",
            "tags": tags,
            "status": "active",
            "metadata": {
                "view_id": view_id,
                "transcription": record.get("transcription", ""),
                "task": record.get("task", {}),
            },
            "aliases": [],
            "masked": False,
        }

    @staticmethod
    def _schema_bundle(entry):
        return {
            "uri": entry.uri,
            "schemas": {
                "input": entry.input_schema,
                "output": entry.output_schema,
                "value": entry.value_schema,
                "metadata": entry.metadata_schema,
                "view": entry.render or {"renderer": "auto"},
            },
        }

    @staticmethod
    def _describe_entry(entry):
        output_type = entry.metadata.get("result_type", "")
        if not output_type and isinstance(entry.output_schema, dict):
            output_type = entry.output_schema.get("$id", "")
        input_required = []
        if isinstance(entry.input_schema, dict):
            input_required = entry.input_schema.get("required") or []
        return {
            "uri": entry.uri,
            "kind": entry.kind,
            "name": entry.name,
            "description": entry.description,
            "can_execute": bool(entry.permissions.get("llm_execute")),
            "requires_confirmation": bool(entry.permissions.get("requires_confirmation")),
            "input_required": input_required,
            "output_type": output_type,
            "danger_level": entry.permissions.get("danger_level", "read_only"),
            "permissions": entry.permissions,
            "transport": entry.to_dict().get("transport", {}),
            "render": entry.render or {"renderer": "auto"},
            "tags": entry.tags,
            "status": entry.status,
        }

    @staticmethod
    def _validation_error(message: str):
        path = "$"
        if message.startswith("$."):
            path = message.split(" ", 1)[0]
        return {
            "code": "SCHEMA_VALIDATION_FAILED",
            "path": path,
            "message": message,
        }

    def _validate_payload(self, uri: str, payload, schema_kind: str):
        entry, error = self._resource_entry_response(uri)
        if error:
            return error
        schema = entry.input_schema if schema_kind == "input" else entry.output_schema
        try:
            validate_schema(schema, payload)
            return self._json_response(
                {
                    "ok": True,
                    "uri": entry.uri,
                    "schema": schema_kind,
                    "valid": True,
                    "errors": [],
                }
            )
        except Exception as exc:
            return self._json_response(
                {
                    "ok": False,
                    "uri": entry.uri,
                    "schema": schema_kind,
                    "valid": False,
                    "errors": [self._validation_error(str(exc))],
                },
                HTTPStatus.BAD_REQUEST,
            )

    def _payload_from_query(self, params, field: str):
        raw = (params.get(field) or ["{}"])[0]
        try:
            payload = json.loads(raw)
        except Exception as exc:
            raise RegistryValidationError("Invalid JSON in %s: %s" % (field, exc))
        if not isinstance(payload, dict):
            raise RegistryValidationError("%s must be a JSON object" % field)
        return payload

    def process_request(self, connection, request):
        raw_path = request.path
        path = raw_path.split("?", 1)[0]
        query = raw_path.split("?", 1)[1] if "?" in raw_path else ""
        params = parse_qs(query)
        upgrade = request.headers.get("Upgrade", "").lower()
        if upgrade == "websocket":
            return None

        if path == "/healthz":
            return self._http_response(b"ok\n", "text/plain; charset=utf-8")
        if path == "/registry-ui":
            host = request.headers.get("Host", f"{self.host}:{self.port}")
            return self._http_response(
                _registry_ui_html(self.bot, host).encode("utf-8"),
                "text/html; charset=utf-8",
            )
        if path == "/autoimprovement":
            host = request.headers.get("Host", f"{self.host}:{self.port}")
            return self._http_response(
                _autoimprovement_html(host).encode("utf-8"),
                "text/html; charset=utf-8",
            )
        if path == "/autoimprovement/latest":
            report = self.bot.get_latest_autoimprovement_report()
            html = self.bot.get_latest_autoimprovement_html()
            return self._json_response(
                {"ok": bool(report), "report": report or {}, "html": html or ""}
            )
        if path in {"/execute", "/query", "/autoimprovement/run"}:
            return self._json_response(
                {
                    "ok": False,
                    "error": {
                        "code": "HTTP_BODY_TRANSPORT_NOT_ENABLED",
                        "message": "This WebSocket-backed server cannot read HTTP request bodies. Use WebSocket JSON messages or an HTTP adapter.",
                    },
                },
                HTTPStatus.NOT_IMPLEMENTED,
            )
        if path == "/manifest":
            return self._json_response(self.bot.registry.manifest())
        if path == "/openapi.json":
            host = request.headers.get("Host", f"{self.host}:{self.port}")
            return self._json_response(_openapi_document(host))
        if path == "/asyncapi.json":
            host = request.headers.get("Host", f"{self.host}:{self.port}")
            return self._json_response(_asyncapi_document(host))
        if path == "/registry":
            registry_entries = [
                entry
                for entry in self.bot.registry.list()
                if bool(entry.permissions.get("llm_discover"))
            ]
            kinds = params.get("kind") or []
            if kinds:
                wanted = set(kinds)
                registry_entries = [
                    entry for entry in registry_entries if entry.kind in wanted
                ]
            tags = params.get("tag") or []
            if tags:
                wanted_tags = set(tags)
                registry_entries = [
                    entry
                    for entry in registry_entries
                    if wanted_tags.intersection(set(entry.tags))
                ]
            domains = params.get("domain") or []
            if domains:
                wanted_domains = set(domains)
                registry_entries = [
                    entry for entry in registry_entries if entry.domain in wanted_domains
                ]
            statuses = params.get("status") or []
            if statuses:
                wanted_statuses = set(statuses)
                registry_entries = [
                    entry for entry in registry_entries if entry.status in wanted_statuses
                ]
            capabilities = params.get("capability") or []
            if capabilities:
                wanted_capabilities = set(capabilities)
                registry_entries = [
                    entry
                    for entry in registry_entries
                    if wanted_capabilities.intersection(set(entry.capabilities))
                ]
            entries = [entry.to_dict() for entry in registry_entries]
            items = [self._registry_item_summary(entry) for entry in registry_entries]
            return self._json_response({"ok": True, "items": items, "entries": entries})
        if path == "/resource":
            uri = (params.get("uri") or [""])[0]
            if not uri:
                return self._json_response(
                    {"ok": False, "error": {"code": "MISSING_URI", "message": "missing uri"}},
                    HTTPStatus.BAD_REQUEST,
                )
            entry = self.bot.registry.get(uri)
            if entry is None or not entry.permissions.get("llm_discover"):
                schema_resource = self._virtual_schema_resource(uri)
                if schema_resource:
                    return self._json_response({"ok": True, "resource": schema_resource})
                view_resource = self._virtual_view_resource(uri)
                if view_resource:
                    return self._json_response({"ok": True, "resource": view_resource})
                return self._json_response(
                    {
                        "ok": False,
                        "error": {
                            "code": "RESOURCE_NOT_FOUND",
                            "message": "resource not found",
                            "uri": uri,
                        },
                    },
                    HTTPStatus.NOT_FOUND,
                )
            return self._json_response({"ok": True, "resource": entry.to_dict()})
        if path in {"/schema", "/schema/input", "/schema/output"}:
            uri = (params.get("uri") or [""])[0]
            entry, error = self._resource_entry_response(uri)
            if error:
                return error
            if path == "/schema/input":
                return self._json_response(
                    {"ok": True, "uri": entry.uri, "schema": "input", "value": entry.input_schema}
                )
            if path == "/schema/output":
                return self._json_response(
                    {"ok": True, "uri": entry.uri, "schema": "output", "value": entry.output_schema}
                )
            return self._json_response({"ok": True, **self._schema_bundle(entry)})
        if path == "/describe":
            uri = (params.get("uri") or [""])[0]
            entry, error = self._resource_entry_response(uri)
            if error:
                return error
            return self._json_response({"ok": True, "description": self._describe_entry(entry)})
        if path == "/permissions":
            uri = (params.get("uri") or [""])[0]
            entry, error = self._resource_entry_response(uri)
            if error:
                return error
            return self._json_response(
                {"ok": True, "uri": entry.uri, "permissions": entry.permissions}
            )
        if path == "/history":
            uri = (params.get("uri") or [""])[0]
            entry, error = self._resource_entry_response(uri)
            if error:
                return error
            limit = int((params.get("limit") or ["20"])[0] or 20)
            return self._json_response(
                {
                    "ok": True,
                    "uri": entry.uri,
                    "history": self.bot.history.recent(limit=max(1, min(limit, 100)), uri=entry.uri),
                }
            )
        if path == "/health":
            uri = (params.get("uri") or [""])[0]
            entry, error = self._resource_entry_response(uri)
            if error:
                return error
            recent = self.bot.history.recent(limit=20, uri=entry.uri)
            failures = [
                item
                for item in recent
                if not item.get("ok")
                or (
                    isinstance(item.get("result"), dict)
                    and item["result"].get("ok") is False
                )
            ]
            return self._json_response(
                {
                    "ok": not failures,
                    "uri": entry.uri,
                    "status": entry.status,
                    "recent_executions": len(recent),
                    "recent_failures": len(failures),
                    "last_execution": recent[0] if recent else None,
                }
            )
        if path in {"/validate", "/validate-input", "/validate-output"}:
            uri = (params.get("uri") or [""])[0]
            schema_kind = "output" if path == "/validate-output" else "input"
            if path == "/validate":
                schema_kind = (params.get("schema") or ["input"])[0]
                if schema_kind not in {"input", "output"}:
                    return self._json_response(
                        {
                            "ok": False,
                            "valid": False,
                            "errors": [
                                {
                                    "code": "UNSUPPORTED_SCHEMA_KIND",
                                    "path": "$.schema",
                                    "message": "schema must be input or output",
                                }
                            ],
                        },
                        HTTPStatus.BAD_REQUEST,
                    )
            field = "output" if schema_kind == "output" else "input"
            try:
                payload = self._payload_from_query(params, field)
            except Exception as exc:
                return self._json_response(
                    {
                        "ok": False,
                        "uri": uri,
                        "schema": schema_kind,
                        "valid": False,
                        "errors": [self._validation_error(str(exc))],
                    },
                    HTTPStatus.BAD_REQUEST,
                )
            return self._validate_payload(uri, payload, schema_kind)
        if path == "/resolve":
            uri = (params.get("uri") or [""])[0]
            if not uri:
                return self._json_response(
                    {"ok": False, "error": "missing uri"},
                    HTTPStatus.BAD_REQUEST,
                )
            include_value = (params.get("include_value") or ["false"])[0].lower() in {
                "1",
                "true",
                "yes",
            }
            try:
                max_bytes = int((params.get("max_bytes") or ["65536"])[0] or 65536)
            except ValueError:
                max_bytes = 65536
            try:
                input_data = self._payload_from_query(params, "input") if "input" in params else {}
            except Exception as exc:
                return self._json_response(
                    {
                        "ok": False,
                        "uri": uri,
                        "valid": False,
                        "errors": [self._validation_error(str(exc))],
                    },
                    HTTPStatus.BAD_REQUEST,
                )
            try:
                entry = self.bot.registry.get(uri)
                if entry is not None:
                    resolved = self.bot.resolve_resource(
                        uri,
                        input_data=input_data,
                        include_value=include_value,
                        max_bytes=max(0, min(max_bytes, 1048576)),
                    )
                else:
                    virtual_resource = self._virtual_schema_resource(uri) or self._virtual_view_resource(uri)
                    if not virtual_resource:
                        raise KeyError("Unknown registry URI: %s" % uri)
                    resolved = self.bot.resolve_resource_document(
                        virtual_resource,
                        include_value=include_value,
                        max_bytes=max(0, min(max_bytes, 1048576)),
                    )
                return self._json_response(
                    {"ok": True, **resolved}
                )
            except Exception as exc:
                return self._json_response(
                    {"ok": False, "error": str(exc)},
                    HTTPStatus.NOT_FOUND,
                )
        if path == "/favicon.ico":
            return self._http_response(b"", "image/x-icon", HTTPStatus.NO_CONTENT)
        if path.startswith("/views/"):
            view_id_text = path.rsplit("/", 1)[-1]
            try:
                view_id = int(view_id_text)
            except ValueError:
                return self._http_response(b"invalid view id\n", "text/plain; charset=utf-8", HTTPStatus.BAD_REQUEST)
            html = self.bot.get_view_html(view_id)
            if html is None:
                return self._http_response(b"view not found\n", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND)
            return self._http_response(html.encode("utf-8"), "text/html; charset=utf-8")
        if path == "/docs":
            host = request.headers.get("Host", f"{self.host}:{self.port}")
            body = _docs_html(host).encode("utf-8")
            return self._http_response(body, "text/html; charset=utf-8")
        else:
            host = request.headers.get("Host", f"{self.host}:{self.port}")
            body = _browser_client_html(host).encode("utf-8")
            return self._http_response(body, "text/html; charset=utf-8")

    @staticmethod
    def _call_maybe_async(func, *args, **kwargs):
        result = func(*args, **kwargs)
        if inspect.isawaitable(result):
            return asyncio.run(result)
        return result

    async def _run_blocking(self, func, *args, **kwargs):
        return await asyncio.to_thread(self._call_maybe_async, func, *args, **kwargs)

    async def _send_log(
        self,
        websocket,
        stage: str,
        status: str,
        message: str,
        details=None,
    ):
        await websocket.send(
            json.dumps(
                {
                    "type": "log",
                    "stage": stage,
                    "status": status,
                    "message": message,
                    "details": details or {},
                },
                ensure_ascii=False,
                default=str,
            )
        )

    async def _send_state(self, websocket, state: str, label: str):
        try:
            await websocket.send(
                json.dumps(
                    {"type": "state", "state": state, "label": label},
                    ensure_ascii=False,
                )
            )
        except Exception:
            pass

    @staticmethod
    def _compact(value, max_chars: int = 2200):
        text = json.dumps(value, ensure_ascii=False, default=str)
        if len(text) > max_chars:
            return text[:max_chars] + "...[truncated]"
        return text

    @staticmethod
    def _collect_source_values(value):
        sources = []
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() == "source":
                    sources.append(str(item))
                sources.extend(TellmServer._collect_source_values(item))
        elif isinstance(value, list):
            for item in value:
                sources.extend(TellmServer._collect_source_values(item))
        return sources

    @staticmethod
    def _requires_real_world_data(text: str, task: Task) -> bool:
        lowered = text.lower()
        keywords = [
            "aktual",
            "teraz",
            "dzisiaj",
            "pogoda",
            "temperatura",
            "weather",
            "domena",
            "domain",
            "kurs",
            "cena",
            "price",
            "stock",
        ]
        if any(keyword in lowered for keyword in keywords):
            return True
        return False

    def _registry_entry_for_task(self, task: Task):
        if not task.function_name.startswith("tellm://"):
            return None
        return self.bot.registry.get(task.function_name)

    def _data_source_findings(self, transcription: str, task: Task, result) -> list:
        disallowed = {"local_simulation", "mock", "test", "llm_generated", "generated"}
        allowed = set()
        entry = self._registry_entry_for_task(task)
        requires_real_world = self._requires_real_world_data(transcription, task)
        if (
            isinstance(result, dict)
            and result.get("ok") is False
            and isinstance(result.get("errors"), list)
            and result.get("errors")
        ):
            return []
        if entry and entry.metadata:
            requires_real_world = requires_real_world or bool(
                entry.metadata.get("requires_real_world_data")
            )
            allowed.update(str(item) for item in entry.metadata.get("allowed_sources", []) or [])
            disallowed.update(
                str(item) for item in entry.metadata.get("disallowed_sources", []) or []
            )
        sources = [source.strip().lower() for source in self._collect_source_values(result)]
        findings = []
        for source in sources:
            if requires_real_world and source in disallowed:
                findings.append(
                    {
                        "severity": "warning",
                        "type": "simulated_data_used_for_real_world_query",
                        "source": source,
                        "problem": "Zapytanie wymaga aktualnych danych zewnętrznych, ale wynik użył source=%s." % source,
                        "recommendation": "Użyj typowanej usługi registry z realnym providerem albo jawnie oznacz wynik jako symulację/test.",
                    }
                )
        if requires_real_world and allowed and sources:
            if not any(source in allowed for source in sources):
                findings.append(
                    {
                        "severity": "warning",
                        "type": "unexpected_data_source",
                        "source": ", ".join(sources),
                        "problem": "Wynik nie użył żadnego dozwolonego źródła danych: %s." % ", ".join(sorted(allowed)),
                        "recommendation": "Przekieruj workflow na właściwą usługę registry albo zaktualizuj allowed_sources.",
                    }
                )
        return findings

    @staticmethod
    def _append_data_quality_warnings(view, findings):
        if not findings:
            return
        render_data = view.render_data if isinstance(view.render_data, dict) else {}
        blocks = render_data.get("blocks")
        if not isinstance(blocks, list):
            blocks = []
            render_data["blocks"] = blocks
        if any(block.get("data_quality_warning") for block in blocks if isinstance(block, dict)):
            return
        blocks.insert(
            0,
            {
                "type": "text",
                "text": "Ostrzeżenie: wynik wymaga weryfikacji źródła danych. "
                + " ".join(item.get("problem", "") for item in findings),
                "data_quality_warning": True,
            },
        )
        view.render_data = render_data
        view.task.view = render_data
        view.view_elements.append({"type": "data_quality", "findings": findings})

    @staticmethod
    def _log_details(logs, stage: str):
        for log in reversed(logs or []):
            if log.get("stage") == stage:
                return log.get("details", {})
        return {}

    @staticmethod
    def _result_business_ok(result) -> bool:
        if not isinstance(result, dict):
            return True
        if isinstance(result.get("ok"), bool):
            return bool(result["ok"])
        if str(result.get("status", "")).lower() == "failed":
            return False
        processes = result.get("processes")
        if isinstance(processes, list):
            for item in processes:
                if not isinstance(item, dict):
                    continue
                if item.get("ok") is False:
                    return False
                nested = item.get("result")
                if isinstance(nested, dict) and nested.get("ok") is False:
                    return False
        return True

    @classmethod
    def _service_result_log(cls, result):
        business_ok = cls._result_business_ok(result)
        return {
            "stage": "service_result",
            "status": "ok" if business_ok else "failed",
            "message": "Wynik usługi OK."
            if business_ok
            else "Usługa zwróciła błąd biznesowy.",
            "details": {
                "business_status": "ok" if business_ok else "failed",
                "result_ok": result.get("ok") if isinstance(result, dict) else None,
                "errors": result.get("errors", []) if isinstance(result, dict) else [],
                "uri": result.get("uri", "") if isinstance(result, dict) else "",
                "type": result.get("type", "") if isinstance(result, dict) else "",
            },
        }

    @classmethod
    def _workflow_history_status(cls, result, data_quality_findings) -> str:
        if not cls._result_business_ok(result):
            return "completed_with_service_error"
        if data_quality_findings:
            return "completed_with_warnings"
        return "completed"

    def _render_logs(
        self,
        transcription: str,
        task: Task,
        result,
        view,
        html: str,
        client_logs=None,
    ):
        render_data = view.render_data if isinstance(view.render_data, dict) else {}
        blocks = render_data.get("blocks") if isinstance(render_data, dict) else []
        logs = [
            {
                "stage": "query",
                "status": "ok" if transcription else "error",
                "message": "Transkrypcja gotowa" if transcription else "Brak transkrypcji",
                "details": {"length": len(transcription)},
            },
            {
                "stage": "llm_json",
                "status": "ok",
                "message": "LLM zwrócił strukturę task/view/processes",
                "details": {
                    "task_type": task.type.value,
                    "function": task.function_name,
                    "registry_uri": task.function_name
                    if task.function_name.startswith("tellm://")
                    else "",
                    "process_count": len(task.processes),
                    "has_view": bool(task.view),
                },
            },
            {
                "stage": "functions",
                "status": "completed",
                "message": "Warstwa wykonawcza zakończyła pracę.",
                "details": {
                    "execution_status": "completed",
                    "result": result,
                },
            },
            self._service_result_log(result),
            {
                "stage": "renderer",
                "status": "ok" if html and "<html" in html.lower() else "error",
                "message": "HTML wyrenderowany",
                "details": {
                    "html_length": len(html),
                    "view_id": view.view_id,
                    "block_count": len(blocks) if isinstance(blocks, list) else 0,
                },
            },
        ]
        data_source_findings = self._data_source_findings(transcription, task, result)
        if data_source_findings:
            logs.append(
                {
                    "stage": "data_source",
                    "status": "warning",
                    "message": "Wykryto problem jakości źródła danych.",
                    "details": {"findings": data_source_findings},
                }
            )
        elif self._requires_real_world_data(transcription, task):
            logs.append(
                {
                    "stage": "data_source",
                    "status": "ok",
                    "message": "Źródło danych nie wygląda na symulację/mock.",
                    "details": {"sources": self._collect_source_values(result)},
                }
            )
        if client_logs:
            logs.append(
                {
                    "stage": "client_logs",
                    "status": "info",
                    "message": "Dołączono logi z poprzedniej interakcji klienta",
                    "details": {"count": len(client_logs), "tail": client_logs[-10:]},
                }
                )
        return logs

    def _local_validation_verdict(self, task: Task, result, view, render_logs):
        if not task.function_name.startswith("tellm://"):
            return None
        if task.processes:
            return None
        if not isinstance(result, dict):
            return None
        business_ok = self._result_business_ok(result)
        errors = result.get("errors")
        if business_ok and errors:
            return None
        if not business_ok and not (
            isinstance(errors, list)
            and errors
            and all(isinstance(error, dict) for error in errors)
        ):
            return None
        renderer_ok = any(
            log.get("stage") == "renderer" and log.get("status") == "ok"
            for log in render_logs or []
        )
        if not renderer_ok:
            return None
        if any(
            log.get("stage") == "data_source" and log.get("status") == "warning"
            for log in render_logs or []
        ):
            return None
        if not isinstance(view.render_data, dict):
            return None
        entry = self.bot.registry.get(task.function_name)
        if entry is None:
            return None
        try:
            validate_schema(entry.output_schema, result)
        except RegistryValidationError:
            return None
        return {
            "status": "ok",
            "answer": self._answer_from_service_result(result) or "OK",
            "reason": (
                "Lokalna walidacja potwierdziła schema-valid wynik lub błąd "
                "z zaufanej usługi registry, poprawny renderer i brak ostrzeżeń data_source."
            ),
        }

    async def _validate_and_repair(
        self,
        websocket,
        transcription: str,
        task: Task,
        result,
        view,
        render_logs,
        client_logs,
        max_attempts: int = 3,
    ):
        config = load_config()
        answer = ""
        local_started = time.perf_counter()
        local_verdict = self._local_validation_verdict(task, result, view, render_logs)
        if local_verdict is not None:
            await self._send_log(
                websocket,
                "local_validation",
                "ok",
                "Lokalny walidator potwierdził wynik bez wywołania LLM.",
                {
                    "duration_ms": self._duration_ms(local_started),
                    "reason": local_verdict["reason"],
                    "llm_validation": "skipped",
                },
            )
            return view, local_verdict["answer"], render_logs
        for attempt in range(1, max_attempts + 1):
            attempt_started = time.perf_counter()
            await self._send_log(
                websocket,
                "llm_validation",
                "checking",
                "Wysyłam render/logi do LLM do potwierdzenia.",
                {"attempt": attempt, "max_attempts": max_attempts},
            )
            html = view.to_html()
            prompt = (
                "Sprawdź, czy odpowiedź tellm jest poprawna. "
                "Masz query użytkownika, task JSON, result, render_data, HTML oraz logi renderera/funkcji. "
                "Dla zadań wykonawczych opartych o tellm:// nie wymyślaj danych faktograficznych; "
                "potwierdź OK albo napraw wyłącznie strukturę view/result zgodnie z danymi lokalnej usługi. "
                "Jeżeli log data_source ma status warning, nie ukrywaj ostrzeżenia i nie uznawaj symulacji/mocka za realne dane. "
                "Zwróć wyłącznie JSON bez markdown w formacie: "
                '{"status":"ok|repair","answer":"krótka odpowiedź dla użytkownika",'
                '"reason":"diagnoza","view":null,"result":null}. '
                "Jeśli status=repair, podaj naprawione pola view i/lub result. "
                "Nie zmieniaj danych bez powodu.\n\n"
                + "QUERY:\n"
                + transcription
                + "\n\nTASK:\n"
                + self._compact(task.__dict__)
                + "\n\nRESULT:\n"
                + self._compact(result)
                + "\n\nRENDER_DATA:\n"
                + self._compact(view.render_data)
                + "\n\nHTML:\n"
                + html[:4000]
                + "\n\nRENDER_LOGS:\n"
                + self._compact(render_logs)
                + "\n\nCLIENT_LOGS:\n"
                + self._compact(client_logs or [])
            )
            resp = await self._run_blocking(
                completion,
                model=config.llm_model,
                messages=[{"role": "user", "content": prompt}],
                api_key=config.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
            )
            content = self.bot._message_text(resp.choices[0].message)
            try:
                verdict = self.bot._parse_json_response(content)
            except Exception:
                await self._send_log(
                    websocket,
                    "llm_validation",
                    "ok",
                    "Walidator nie zwrócił JSON; traktuję odpowiedź jako finalny tekst.",
                    {"attempt": attempt, "duration_ms": self._duration_ms(attempt_started)},
                )
                return view, content, render_logs

            status = str(verdict.get("status", "ok")).lower()
            answer = str(verdict.get("answer") or verdict.get("reason") or "OK")
            if status == "ok":
                await self._send_log(
                    websocket,
                    "llm_validation",
                    "ok",
                    "LLM potwierdził poprawność wyniku.",
                    {
                        "attempt": attempt,
                        "duration_ms": self._duration_ms(attempt_started),
                        "reason": verdict.get("reason", ""),
                    },
                )
                return view, answer, render_logs

            repaired = False
            if isinstance(verdict.get("view"), dict):
                task.view = verdict["view"]
                repaired = True
            if "result" in verdict and verdict.get("result") is not None:
                result = verdict["result"]
                repaired = True
            await self._send_log(
                websocket,
                "llm_validation",
                "repair",
                "LLM zażądał naprawy danych i ponownego renderowania.",
                {
                    "attempt": attempt,
                    "duration_ms": self._duration_ms(attempt_started),
                    "reason": verdict.get("reason", ""),
                    "repaired": repaired,
                },
            )
            view = await self._run_blocking(
                self.bot.generate_view, transcription, task, result
            )
            html = view.to_html()
            render_logs = self._render_logs(
                transcription, task, result, view, html, client_logs=client_logs
            )
            await self._send_log(
            websocket,
            "renderer",
            "ok",
            "Widok po naprawie wyrenderowany ponownie.",
            self._log_details(render_logs, "renderer"),
        )

        await self._send_log(
            websocket,
            "llm_validation",
            "error",
            "Limit prób walidacji został osiągnięty.",
            {"max_attempts": max_attempts},
        )
        return view, answer or "Nie udało się jednoznacznie potwierdzić wyniku.", render_logs

    @staticmethod
    def _answer_from_service_result(result) -> str:
        if not isinstance(result, dict):
            return ""
        message = result.get("message")
        if not isinstance(message, dict):
            return ""
        return str(message.get("summary") or message.get("title") or "")

    @staticmethod
    def _looks_executable_query(text: str) -> bool:
        lowered = text.lower()
        keywords = [
            "sprawdź",
            "sprawdz",
            "wykonaj",
            "uruchom",
            "pobierz",
            "opublikuj",
            "zapisz",
            "domena",
            "domain",
            "check",
            "pogoda",
            "weather",
            "temperatura",
        ]
        return any(keyword in lowered for keyword in keywords)

    @staticmethod
    def _repair_count(logs) -> int:
        return len(
            [
                log
                for log in logs or []
                if log.get("stage") == "llm_validation" and log.get("status") == "repair"
            ]
        )

    @staticmethod
    def _duration_ms(start: float) -> int:
        return int(round((time.perf_counter() - start) * 1000))

    async def _handle_transcription(self, websocket, transcription: str, speak: bool, client_logs=None):
        workflow_started = time.perf_counter()
        print("TEXT:", transcription)
        await websocket.send(json.dumps({"type": "view", "data": {"transcription": transcription, "status": "analyzing"}}))
        await self._send_log(websocket, "query", "received", "Przyjęto query.", {"text": transcription})
        llm_started = time.perf_counter()
        local_task = self.bot._local_task_from_query(transcription)
        if local_task is not None:
            task = local_task
            await self._send_log(
                websocket,
                "router",
                "ok",
                "Lokalny router rozpoznał stałą usługę registry bez wywołania LLM.",
                {
                    "task_type": task.type.value,
                    "function": task.function_name,
                    "processes": len(task.processes),
                    "router": task.view.get("_router") if isinstance(task.view, dict) else "local",
                    "duration_ms": self._duration_ms(llm_started),
                },
            )
        else:
            await self._send_log(websocket, "llm_answer", "running", "Wysyłam query do LLM po JSON task/view/processes.")
            task = await self._run_blocking(self.bot.analyze_query, transcription)
            await self._send_log(
                websocket,
                "llm_answer",
                "ok",
                "LLM zwrócił JSON do wykonania i renderowania.",
                {
                    "task_type": task.type.value,
                    "function": task.function_name,
                    "processes": len(task.processes),
                    "duration_ms": self._duration_ms(llm_started),
                },
            )
        await self._send_log(websocket, "functions", "running", "Uruchamiam funkcje/procesy Python.")
        execution_started = time.perf_counter()
        result = await self._run_blocking(self.bot.execute_task, task)
        await self._send_log(
            websocket,
            "functions",
            "completed",
            "Warstwa wykonawcza zakończyła pracę.",
            {
                "execution_status": "completed",
                "duration_ms": self._duration_ms(execution_started),
                "result": result,
            },
        )
        service_log = self._service_result_log(result)
        await self._send_log(
            websocket,
            service_log["stage"],
            service_log["status"],
            service_log["message"],
            service_log["details"],
        )
        await self._send_log(websocket, "renderer", "running", "Renderuję HTML z danych JSON.")
        renderer_started = time.perf_counter()
        view = await self._run_blocking(self.bot.generate_view, transcription, task, result)
        data_quality_findings = self._data_source_findings(transcription, task, result)
        self._append_data_quality_warnings(view, data_quality_findings)
        html = view.to_html()
        render_logs = self._render_logs(
            transcription, task, result, view, html, client_logs=client_logs
        )
        for log in render_logs:
            if log.get("stage") == "data_source" and log.get("status") == "warning":
                await self._send_log(
                    websocket,
                    "data_source",
                    "warning",
                    log.get("message", "Wykryto problem jakości źródła danych."),
                    log.get("details", {}),
                )
        await self._send_log(
            websocket,
            "renderer",
            "ok",
            "Renderer zakończył pracę. Logi idą do walidacji LLM.",
            {
                **self._log_details(render_logs, "renderer"),
                "duration_ms": self._duration_ms(renderer_started),
            },
        )
        validation_started = time.perf_counter()
        view, answer, render_logs = await self._validate_and_repair(
            websocket,
            transcription,
            task,
            result,
            view,
            render_logs,
            client_logs,
        )
        validation_duration_ms = self._duration_ms(validation_started)
        data_quality_findings = self._data_source_findings(transcription, task, view.result)
        self._append_data_quality_warnings(view, data_quality_findings)
        answer = self._answer_from_service_result(view.result) or answer
        view.view_elements.append({"type": "answer", "text": answer})
        await self._run_blocking(self.bot.save_view, view)
        html = view.to_html()
        direct_answer_violation = (
            self._looks_executable_query(transcription)
            and not task.function_name.startswith("tellm://")
            and not task.processes
        )
        service_result_status = "ok" if self._result_business_ok(view.result) else "failed"
        workflow_status = self._workflow_history_status(view.result, data_quality_findings)
        await self._run_blocking(
            self.bot.record_execution,
            uri=task.function_name,
            kind="workflow",
            ok=True,
            status=workflow_status,
            result=view.result,
            logs=render_logs,
            metadata={
                "query": transcription,
                "llm_direct_answer_violation": direct_answer_violation,
                "data_quality_findings": data_quality_findings,
                "execution_status": "completed",
                "service_result_status": service_result_status,
                "repair_count": self._repair_count(render_logs),
                "view_id": view.view_id,
            },
        )
        if service_result_status == "failed":
            await self._send_log(
                websocket,
                "workflow",
                "completed_with_service_error",
                "Workflow zakończony, ale wynik usługi jest błędem.",
                {
                    "service_result_status": service_result_status,
                    "validation_duration_ms": validation_duration_ms,
                    "total_duration_ms": self._duration_ms(workflow_started),
                },
            )
        elif data_quality_findings:
            await self._send_log(
                websocket,
                "workflow",
                "warning",
                "Workflow zakończony z ostrzeżeniem jakości danych.",
                {
                    "data_quality_findings": data_quality_findings,
                    "validation_duration_ms": validation_duration_ms,
                    "total_duration_ms": self._duration_ms(workflow_started),
                },
            )
        else:
            await self._send_log(
                websocket,
                "workflow",
                "ok",
                "Workflow potwierdzony i zakończony.",
                {
                    "validation_duration_ms": validation_duration_ms,
                    "total_duration_ms": self._duration_ms(workflow_started),
                },
            )
        await websocket.send(json.dumps({"type": "view", "data": view.to_dict(), "html": html}))
        if speak:
            await self._run_blocking(self.bot.speak, answer)

    async def _handle_resource_execution(self, websocket, uri: str, payload, speak: bool, client_logs=None):
        workflow_started = time.perf_counter()
        if not isinstance(payload, dict):
            payload = {}
        await websocket.send(
            json.dumps(
                {
                    "type": "view",
                    "data": {
                        "transcription": uri,
                        "status": "analyzing",
                    },
                },
                ensure_ascii=False,
            )
        )
        await self._send_log(
            websocket,
            "registry",
            "resolve",
            "Rozwiązuję URI w registry.",
            {"uri": uri, "input": payload},
        )
        task = Task(TaskType.NOW, uri, payload)
        await self._send_log(
            websocket,
            "registry",
            "execute",
            "Uruchamiam lokalny zasób przez resolver.",
            {"uri": uri},
        )
        execution_started = time.perf_counter()
        result = await self._run_blocking(self.bot.execute_resource, uri, payload)
        await self._send_log(
            websocket,
            "registry",
            "completed",
            "Lokalny resolver zakończył pracę.",
            {
                "execution_status": "completed",
                "duration_ms": self._duration_ms(execution_started),
                "result": result,
            },
        )
        service_log = self._service_result_log(result)
        await self._send_log(
            websocket,
            service_log["stage"],
            service_log["status"],
            service_log["message"],
            service_log["details"],
        )
        renderer_started = time.perf_counter()
        view = await self._run_blocking(self.bot.generate_view, uri, task, result)
        data_quality_findings = self._data_source_findings(uri, task, result)
        self._append_data_quality_warnings(view, data_quality_findings)
        html = view.to_html()
        render_logs = self._render_logs(
            uri, task, result, view, html, client_logs=client_logs
        )
        for log in render_logs:
            if log.get("stage") == "data_source" and log.get("status") == "warning":
                await self._send_log(
                    websocket,
                    "data_source",
                    "warning",
                    log.get("message", "Wykryto problem jakości źródła danych."),
                    log.get("details", {}),
                )
        await self._send_log(
            websocket,
            "renderer",
            "ok",
            "Renderer utworzył HTML z wyniku lokalnego zasobu.",
            {
                **self._log_details(render_logs, "renderer"),
                "duration_ms": self._duration_ms(renderer_started),
            },
        )
        validation_started = time.perf_counter()
        view, answer, render_logs = await self._validate_and_repair(
            websocket,
            uri,
            task,
            result,
            view,
            render_logs,
            client_logs,
        )
        validation_duration_ms = self._duration_ms(validation_started)
        data_quality_findings = self._data_source_findings(uri, task, view.result)
        self._append_data_quality_warnings(view, data_quality_findings)
        answer = self._answer_from_service_result(view.result) or answer
        view.view_elements.append({"type": "answer", "text": answer})
        await self._run_blocking(self.bot.save_view, view)
        html = view.to_html()
        if isinstance(view.result, dict) and view.result.get("type") == "system.autoimprovement.report":
            report_id = view.result.get("data", {}).get("report_id")
            if report_id:
                await self._run_blocking(
                    self.bot.update_autoimprovement_report_html,
                    int(report_id),
                    view.result,
                    html,
                )
        service_result_status = "ok" if self._result_business_ok(view.result) else "failed"
        workflow_status = self._workflow_history_status(view.result, data_quality_findings)
        await self._run_blocking(
            self.bot.record_execution,
            uri=uri,
            kind="registry_workflow",
            ok=True,
            status=workflow_status,
            result=view.result,
            logs=render_logs,
            metadata={
                "query": uri,
                "input": payload,
                "data_quality_findings": data_quality_findings,
                "execution_status": "completed",
                "service_result_status": service_result_status,
                "repair_count": self._repair_count(render_logs),
                "view_id": view.view_id,
            },
        )
        if service_result_status == "failed":
            await self._send_log(
                websocket,
                "workflow",
                "completed_with_service_error",
                "Registry execute zakończony, ale wynik usługi jest błędem.",
                {
                    "service_result_status": service_result_status,
                    "validation_duration_ms": validation_duration_ms,
                    "total_duration_ms": self._duration_ms(workflow_started),
                },
            )
        elif data_quality_findings:
            await self._send_log(
                websocket,
                "workflow",
                "warning",
                "Registry execute zakończony z ostrzeżeniem jakości danych.",
                {
                    "data_quality_findings": data_quality_findings,
                    "validation_duration_ms": validation_duration_ms,
                    "total_duration_ms": self._duration_ms(workflow_started),
                },
            )
        else:
            await self._send_log(
                websocket,
                "workflow",
                "ok",
                "Registry execute potwierdzony i zakończony.",
                {
                    "validation_duration_ms": validation_duration_ms,
                    "total_duration_ms": self._duration_ms(workflow_started),
                },
            )
        await websocket.send(json.dumps({"type": "view", "data": view.to_dict(), "html": html}))
        if speak and answer:
            await self._run_blocking(self.bot.speak, answer)

    async def _handle_test_transcription(
        self, websocket, transcription: str, source: str, speak: bool
    ):
        print("TEST:", source, transcription)
        await websocket.send(json.dumps({"type": "view", "data": {"transcription": transcription, "status": "analyzing"}}))
        task = Task(TaskType.NOW, "protocol_test", {"source": source, "text": transcription})
        result = {"ok": True, "source": source, "echo": transcription}
        view = await self._run_blocking(self.bot.generate_view, transcription, task, result)
        answer = "Protocol test OK: " + transcription
        view.view_elements.append({"type": "answer", "text": answer})
        await self._run_blocking(self.bot.save_view, view)
        html = view.to_html()
        await websocket.send(json.dumps({"type": "view", "data": view.to_dict(), "html": html}))
        if speak:
            await self._run_blocking(self.bot.speak, answer)

    def _audio_payload(self, audio) -> tuple[bytes, str]:
        if isinstance(audio, bytes):
            return audio, ".wav"
        if isinstance(audio, str):
            suffix = ".wav"
            if audio.startswith("data:"):
                header, audio = audio.split(",", 1)
                mime = header[5:].split(";", 1)[0].lower()
                suffix = {
                    "audio/webm": ".webm",
                    "audio/wav": ".wav",
                    "audio/wave": ".wav",
                    "audio/x-wav": ".wav",
                    "audio/ogg": ".ogg",
                    "audio/mp4": ".mp4",
                    "audio/mpeg": ".mp3",
                }.get(mime, ".wav")
            try:
                return base64.b64decode(audio), suffix
            except Exception:
                return audio.encode("utf-8"), suffix
        return bytes(audio), ".wav"

    async def _process_message(self, websocket, data):
        try:
            await self._send_state(websocket, "busy", "Pracuję")
            source = str(data.get("type") or "text")
            if source == "execute":
                uri = str(data.get("uri") or "").strip()
                if not uri:
                    await websocket.send(json.dumps({"type": "error", "message": "Brak uri."}))
                    return
                logs = data.get("logs", [])
                if not isinstance(logs, list):
                    logs = []
                await self._handle_resource_execution(
                    websocket,
                    uri=uri,
                    payload=data.get("input", {}),
                    speak=bool(data.get("speak", False)),
                    client_logs=logs,
                )
                return
            transcription = str(data.get("text", "")).strip()
            if data.get("test") and not transcription:
                transcription = str(data.get("transcription", "")).strip()
            if not transcription and data.get("audio"):
                audio_data, audio_suffix = self._audio_payload(data["audio"])
                transcription = await self._run_blocking(
                    self.bot.transcribe,
                    audio_data,
                    audio_suffix,
                )
            if not transcription:
                await websocket.send(json.dumps({"type": "error", "message": "Brak tekstu lub audio."}))
                return
            if data.get("test"):
                await self._handle_test_transcription(
                    websocket,
                    transcription,
                    source=source,
                    speak=bool(data.get("speak", False)),
                )
                return
            logs = data.get("logs", [])
            if not isinstance(logs, list):
                logs = []
            await self._handle_transcription(
                websocket,
                transcription,
                speak=bool(data.get("speak", False)),
                client_logs=logs,
            )
        except asyncio.CancelledError:
            await self._send_log(websocket, "workflow", "cancelled", "Praca nad query została przerwana.")
            raise
        except Exception as e:
            print("Bqd:", e)
            await websocket.send(json.dumps({"type": "error", "message": str(e)}))
        finally:
            await self._send_state(websocket, "idle", "Gotowe")

    async def handle(self, websocket, path=None):
        active_task = None

        def consume_task_result(task):
            try:
                task.exception()
            except asyncio.CancelledError:
                pass
            except Exception:
                pass

        async for message in websocket:
            try:
                data = json.loads(message)
                if data.get("type") == "cancel":
                    if active_task and not active_task.done():
                        active_task.cancel()
                        await self._send_state(websocket, "idle", "Przerwano")
                    else:
                        await self._send_log(websocket, "workflow", "idle", "Nie ma aktywnego query do przerwania.")
                    continue
                if active_task and not active_task.done():
                    await websocket.send(
                        json.dumps(
                            {
                                "type": "error",
                                "message": "Trwa poprzednie query. Poczekaj na OK albo przerwij pracę.",
                            },
                            ensure_ascii=False,
                        )
                    )
                    continue
                active_task = asyncio.create_task(self._process_message(websocket, data))
                active_task.add_done_callback(consume_task_result)
            except Exception as e:
                print("Bqd:", e)
                await websocket.send(json.dumps({"type": "error", "message": str(e)}))
        if active_task and not active_task.done():
            active_task.cancel()

    async def serve_forever(self):
        print("tellm v4 na " + self.host + ":" + str(self.port))
        async with websockets.serve(
            self.handle,
            self.host,
            self.port,
            process_request=self.process_request,
            logger=_websocket_logger(),
        ):
            await asyncio.Future()

    def run(self):
        try:
            asyncio.run(self.serve_forever())
        except KeyboardInterrupt:
            print("\ntellm stopped")
