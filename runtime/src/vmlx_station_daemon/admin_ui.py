from __future__ import annotations


def render_admin_ui() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>vMLX Station</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #0a1016;
      --panel: #101821;
      --panel-2: #121e29;
      --line: rgba(180, 204, 229, 0.16);
      --ink: #eaf2fb;
      --muted: #8ea2b7;
      --accent: #63d2c7;
      --accent-2: #f2b468;
      --good: #4ade80;
      --bad: #fb7185;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "SF Pro Text", "JetBrains Mono", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(99, 210, 199, 0.14), transparent 22%),
        radial-gradient(circle at top right, rgba(242, 180, 104, 0.15), transparent 20%),
        linear-gradient(180deg, #0f1722 0%, var(--bg) 100%);
    }
    .shell {
      width: min(1340px, calc(100vw - 28px));
      margin: 18px auto 64px;
      display: grid;
      gap: 16px;
    }
    .hero, .card {
      background: rgba(16, 24, 33, 0.94);
      border: 1px solid var(--line);
      border-radius: 18px;
      box-shadow: 0 20px 42px rgba(0, 0, 0, 0.26);
    }
    .hero { padding: 22px; }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 16px;
    }
    .card { padding: 18px; }
    h1, h2, h3, p { margin: 0; }
    h1 { font-size: clamp(28px, 4vw, 38px); }
    h2 { font-size: 18px; margin-bottom: 12px; }
    h3 { font-size: 14px; margin-bottom: 6px; }
    p { color: var(--muted); line-height: 1.5; }
    .summary {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 10px;
      margin-top: 14px;
    }
    .pill {
      padding: 12px 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(7, 12, 18, 0.7);
    }
    .pill .label {
      display: block;
      font-size: 11px;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
      margin-bottom: 7px;
    }
    .pill .value {
      font-size: 15px;
      font-weight: 700;
    }
    .toolbar, .button-row {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    button, input, select, textarea {
      border-radius: 12px;
      border: 1px solid var(--line);
      background: rgba(8, 12, 18, 0.82);
      color: var(--ink);
      font: inherit;
    }
    button {
      padding: 10px 14px;
      cursor: pointer;
      background: var(--accent);
      color: #061015;
      font-weight: 700;
    }
    button.secondary {
      background: rgba(8, 12, 18, 0.82);
      color: var(--ink);
    }
    button.warn {
      background: var(--accent-2);
      color: #1b1205;
    }
    button.danger {
      background: #f87171;
      color: #180808;
    }
    input, select, textarea {
      width: 100%;
      padding: 11px 12px;
    }
    textarea { min-height: 104px; resize: vertical; }
    label {
      display: grid;
      gap: 7px;
      font-size: 13px;
      color: var(--muted);
    }
    .form-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px;
    }
    .form-grid .span-2 {
      grid-column: span 2;
    }
    .models {
      display: grid;
      gap: 10px;
    }
    .model {
      padding: 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(8, 12, 18, 0.7);
    }
    .model-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
    }
    .meta {
      font-size: 12px;
      color: var(--muted);
      word-break: break-word;
    }
    .status-good { color: var(--good); }
    .status-bad { color: var(--bad); }
    .checkbox {
      display: flex;
      align-items: center;
      gap: 10px;
      color: var(--ink);
    }
    .checkbox input {
      width: auto;
      margin: 0;
    }
    pre {
      margin: 0;
      padding: 14px;
      border-radius: 14px;
      border: 1px solid var(--line);
      background: rgba(8, 12, 18, 0.74);
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.55;
      font-family: "SF Mono", "JetBrains Mono", monospace;
      font-size: 12px;
    }
    .hint {
      margin-top: 10px;
      font-size: 12px;
      color: var(--muted);
    }
    .notice {
      margin-top: 10px;
      font-size: 13px;
      color: var(--accent);
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <p>vMLX Station</p>
      <h1>Local vMLX control, testing, and scheduling</h1>
      <p class="hint">This page is built into the daemon. You do not need Open WebUI just to test a loaded model.</p>
      <div class="summary" id="summary"></div>
      <div class="toolbar" style="margin-top: 14px;">
        <button id="refresh-btn">Refresh</button>
        <button class="secondary" id="rescan-btn">Rescan Models</button>
        <button class="secondary" id="open-webui-btn">Open WebUI</button>
        <button class="warn" id="reload-btn">Reload Current</button>
        <button class="danger" id="unload-btn">Unload</button>
      </div>
      <div class="notice" id="top-notice"></div>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Models</h2>
        <div class="models" id="models"></div>
      </article>

      <article class="card">
        <h2>Chat Test</h2>
        <div class="form-grid">
          <label class="span-2">System Prompt
            <textarea id="system-prompt" placeholder="Optional system prompt"></textarea>
          </label>
          <label class="span-2">Prompt
            <textarea id="user-prompt" placeholder="Say something to the loaded model"></textarea>
          </label>
          <label>Response Max Tokens
            <input id="chat-max-tokens" type="number" min="1" max="32768" value="256">
          </label>
          <label>Temperature
            <input id="chat-temperature" type="number" min="0" max="2" step="0.1" placeholder="optional">
          </label>
        </div>
        <div class="button-row" style="margin-top: 12px;">
          <button id="send-chat-btn">Send Test Prompt</button>
        </div>
        <div class="hint" id="chat-hint">This uses the currently loaded runtime on <code>/v1/chat/completions</code>.</div>
        <pre id="chat-output" style="margin-top: 12px;">No response yet.</pre>
      </article>
    </section>

    <section class="grid">
      <article class="card">
        <h2>Runtime Settings</h2>
        <div class="form-grid">
          <label class="span-2">Model Roots (one per line)
            <textarea id="model-roots"></textarea>
          </label>
          <label class="span-2">vmlx Binary
            <input id="vmlx-bin" type="text">
          </label>
          <label>Max Tokens
            <input id="cfg-max-tokens" type="number" min="1" max="262144">
          </label>
          <label>Max Concurrent Seqs
            <input id="cfg-max-num-seqs" type="number" min="1" max="4096">
          </label>
          <label>Cache Memory Percent
            <input id="cfg-cache-memory-percent" type="number" min="0.01" max="0.95" step="0.01">
          </label>
          <label>KV Cache Quantization
            <select id="cfg-kv-cache-quantization">
              <option value="none">none</option>
              <option value="q4">q4</option>
              <option value="q8">q8</option>
            </select>
          </label>
          <label>KV Group Size
            <input id="cfg-kv-cache-group-size" type="number" min="1" max="4096">
          </label>
          <label>Paged Cache Block Size
            <input id="cfg-paged-cache-block-size" type="number" min="1" max="4096">
          </label>
          <label>Max Cache Blocks
            <input id="cfg-max-cache-blocks" type="number" min="1" max="1000000">
          </label>
          <label>Stream Memory Percent
            <input id="cfg-stream-memory-percent" type="number" min="1" max="99">
          </label>
          <label class="checkbox"><input id="cfg-thinking" type="checkbox"> Default enable thinking</label>
          <label class="checkbox"><input id="cfg-continuous-batching" type="checkbox"> Continuous batching</label>
          <label class="checkbox"><input id="cfg-prefix-cache" type="checkbox"> Enable prefix cache</label>
          <label class="checkbox"><input id="cfg-paged-cache" type="checkbox"> Use paged cache</label>
          <label class="checkbox"><input id="cfg-stream-from-disk" type="checkbox"> Stream from disk</label>
          <label class="span-2">Extra Args (space-separated)
            <input id="cfg-extra-args" type="text" placeholder="Example: --enable-jit --log-level INFO">
          </label>
        </div>
        <div class="hint" id="runtime-context-hint">Current vMLX build does not expose a separate explicit “max context length” load flag in <code>vmlx serve --help</code>. The closest tunable knobs today are response max tokens, cache memory, batching, and streaming-related settings.</div>
        <pre id="runtime-rules" style="margin-top: 12px;">Loading runtime guidance...</pre>
        <div class="button-row" style="margin-top: 12px;">
          <button id="save-config-btn">Save Runtime Settings</button>
        </div>
      </article>

      <article class="card">
        <h2>Schedule</h2>
        <div class="form-grid">
          <label class="checkbox span-2"><input id="schedule-enabled" type="checkbox"> Enable day/night schedule</label>
          <label>Day Start
            <input id="day-start" type="time">
          </label>
          <label>Day End
            <input id="day-end" type="time">
          </label>
          <label class="span-2">Day Model
            <select id="day-model"></select>
          </label>
          <label>Night Start
            <input id="night-start" type="time">
          </label>
          <label>Night End
            <input id="night-end" type="time">
          </label>
          <label class="span-2">Night Model
            <select id="night-model"></select>
          </label>
        </div>
        <div class="button-row" style="margin-top: 12px;">
          <button id="save-schedule-btn">Save Schedule</button>
        </div>
      </article>
    </section>
  </div>

  <script>
    const state = { status: null, models: [], config: null, runtimeMetadata: null };

    function formatNumber(value) {
      if (value === null || value === undefined || value === "") return "Unknown";
      return Number(value).toLocaleString("en-US");
    }

    async function fetchJson(url, options = {}) {
      const response = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        cache: "no-store",
        ...options,
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `${response.status} ${response.statusText}`);
      }
      return response.json();
    }

    function notice(message, isError = false) {
      const el = document.getElementById("top-notice");
      el.textContent = message;
      el.style.color = isError ? "var(--bad)" : "var(--accent)";
    }

    function renderSummary() {
      const status = state.status;
      const contextText = status?.loaded_model_text_context_tokens
        ? `${formatNumber(status.loaded_model_text_context_tokens)} text`
        : "Unknown";
      const items = [
        ["Runtime", status?.running ? "Running" : "Idle"],
        ["Loaded", status?.loaded_model_id || "None"],
        ["Served As", status?.served_model_name || "None"],
        ["Model Context", contextText],
        ["Chat UI", status?.open_webui_running ? "Open WebUI running" : (status?.open_webui_url ? "Configured" : "Disabled")],
        ["OpenAI API", status?.openai_base_url || "Unavailable"],
        ["Control API", status?.control_base_url || "Unavailable"],
        ["Schedule", status?.schedule_enabled ? (status?.active_schedule_rule?.name || "Enabled") : "Disabled"],
      ];
      document.getElementById("summary").innerHTML = items.map(([label, value]) => `
        <div class="pill">
          <span class="label">${label}</span>
          <span class="value">${value}</span>
        </div>
      `).join("");
    }

    function renderModels() {
      const loaded = state.status?.loaded_model_id;
      const html = state.models.map((model) => {
        const isLoaded = loaded === model.id;
        const contexts = [
          model.text_context_tokens ? `text ${formatNumber(model.text_context_tokens)}` : null,
          model.vision_context_tokens ? `vision ${formatNumber(model.vision_context_tokens)}` : null,
        ].filter(Boolean).join(" · ");
        return `
          <div class="model">
            <div class="model-top">
              <div>
                <h3>${model.id}</h3>
                <div class="meta">${model.engine} · ${model.source}${model.has_vision ? " · vision" : ""}${model.has_jang ? " · JANG" : ""}${model.architecture ? ` · ${model.architecture}` : ""}</div>
              </div>
              <button data-load-model="${model.id}">${isLoaded ? "Reload" : "Load"}</button>
            </div>
            <div class="meta">${contexts || "Context window unknown"}</div>
            <div class="meta">${model.path}</div>
          </div>
        `;
      }).join("");
      document.getElementById("models").innerHTML = html || `<p>No models found.</p>`;
      document.querySelectorAll("[data-load-model]").forEach((button) => {
        button.addEventListener("click", async () => {
          notice(`Loading ${button.dataset.loadModel}...`);
          try {
            await fetchJson("/api/load", {
              method: "POST",
              body: JSON.stringify({ model_id: button.dataset.loadModel }),
            });
            await refreshAll();
            notice(`Loaded ${button.dataset.loadModel}`);
          } catch (error) {
            notice(error.message, true);
          }
        });
      });
    }

    function setSelectOptions(selectId, selectedValue) {
      const select = document.getElementById(selectId);
      select.innerHTML = state.models.map((model) => (
        `<option value="${model.id}" ${model.id === selectedValue ? "selected" : ""}>${model.id}</option>`
      )).join("");
    }

    function renderRuntimeHints() {
      const metadata = state.runtimeMetadata;
      const status = state.status;
      const loadedContext = status?.loaded_model_text_context_tokens || null;
      const maxTokensInput = document.getElementById("cfg-max-tokens");
      const chatMaxTokensInput = document.getElementById("chat-max-tokens");
      const maxTokensMeta = metadata?.fields?.max_tokens || { min: 1, max: 262144, default: 32768 };
      maxTokensInput.min = maxTokensMeta.min ?? 1;
      maxTokensInput.max = maxTokensMeta.max ?? 262144;
      chatMaxTokensInput.min = 1;
      chatMaxTokensInput.max = loadedContext || maxTokensMeta.max || 262144;

      const rules = [
        maxTokensMeta.note || "max_tokens is a generation cap, not the model context window.",
      ];
      if (loadedContext) {
        rules.push(`Loaded model context window: ${formatNumber(loadedContext)} text tokens.`);
      }
      if (status?.warnings?.length) {
        rules.push(...status.warnings);
      }
      if (metadata?.rules?.length) {
        rules.push(...metadata.rules);
      }
      document.getElementById("runtime-rules").textContent = rules.join("\\n");

      const chatHint = loadedContext
        ? `Loaded model text context: ${formatNumber(loadedContext)}. The chat-test max tokens field is a response cap, not the full context budget.`
        : "This uses the currently loaded runtime on /v1/chat/completions.";
      document.getElementById("chat-hint").textContent = chatHint;

      const contextHint = loadedContext
        ? `Current loaded model supports up to ${formatNumber(loadedContext)} text tokens. vMLX does not expose a separate --context-length flag in this build, so we surface safe load/runtime knobs instead.`
        : "Current vMLX build does not expose a separate explicit max context length load flag in vmlx serve --help.";
      document.getElementById("runtime-context-hint").textContent = contextHint;
      const openWebUIButton = document.getElementById("open-webui-btn");
      const openWebUIURL = status?.open_webui_url;
      openWebUIButton.disabled = !openWebUIURL;
      openWebUIButton.textContent = status?.open_webui_running ? "Open WebUI" : "Open WebUI (start if needed)";
    }

    function normalizeRuntimeForm() {
      const continuousBatching = document.getElementById("cfg-continuous-batching");
      const prefixCache = document.getElementById("cfg-prefix-cache");
      const pagedCache = document.getElementById("cfg-paged-cache");
      const kvQuant = document.getElementById("cfg-kv-cache-quantization");
      const maxNumSeqs = document.getElementById("cfg-max-num-seqs");
      const streamFromDisk = document.getElementById("cfg-stream-from-disk");

      let adjusted = [];

      if (streamFromDisk.checked) {
        if (maxNumSeqs.value !== "1") {
          maxNumSeqs.value = "1";
          adjusted.push("Set max concurrent seqs to 1 for stream-from-disk mode.");
        }
        if (continuousBatching.checked) {
          continuousBatching.checked = false;
          adjusted.push("Disabled continuous batching because stream-from-disk mode cannot use it.");
        }
        if (prefixCache.checked) {
          prefixCache.checked = false;
          adjusted.push("Disabled prefix cache because stream-from-disk mode cannot use it.");
        }
        if (pagedCache.checked) {
          pagedCache.checked = false;
          adjusted.push("Disabled paged cache because stream-from-disk mode cannot use it.");
        }
        if (kvQuant.value !== "none") {
          kvQuant.value = "none";
          adjusted.push("Disabled KV cache quantization because stream-from-disk mode cannot use it.");
        }
      }

      if (kvQuant.value !== "none" && !continuousBatching.checked) {
        continuousBatching.checked = true;
        adjusted.push("Enabled continuous batching because KV cache quantization requires it.");
      }

      if (pagedCache.checked && !continuousBatching.checked) {
        continuousBatching.checked = true;
        adjusted.push("Enabled continuous batching because paged cache requires it.");
      }

      if (!continuousBatching.checked) {
        if (kvQuant.value !== "none") {
          kvQuant.value = "none";
          adjusted.push("Reset KV cache quantization to none because continuous batching is off.");
        }
        if (pagedCache.checked) {
          pagedCache.checked = false;
          adjusted.push("Disabled paged cache because continuous batching is off.");
        }
      }

      return adjusted;
    }

    function renderConfigForm() {
      const config = state.config;
      if (!config) return;
      document.getElementById("model-roots").value = (config.model_roots || []).join("\\n");
      document.getElementById("vmlx-bin").value = config.runtime.vmlx_bin || "";
      document.getElementById("cfg-thinking").checked = !!config.runtime.default_enable_thinking;
      document.getElementById("cfg-max-tokens").value = config.runtime.max_tokens ?? 32768;
      document.getElementById("cfg-max-num-seqs").value = config.runtime.max_num_seqs ?? 256;
      document.getElementById("cfg-continuous-batching").checked = !!config.runtime.continuous_batching;
      document.getElementById("cfg-prefix-cache").checked = !!config.runtime.enable_prefix_cache;
      document.getElementById("cfg-cache-memory-percent").value = config.runtime.cache_memory_percent ?? 0.30;
      document.getElementById("cfg-paged-cache").checked = !!config.runtime.use_paged_cache;
      document.getElementById("cfg-paged-cache-block-size").value = config.runtime.paged_cache_block_size ?? 64;
      document.getElementById("cfg-max-cache-blocks").value = config.runtime.max_cache_blocks ?? 1000;
      document.getElementById("cfg-kv-cache-quantization").value = config.runtime.kv_cache_quantization ?? "none";
      document.getElementById("cfg-kv-cache-group-size").value = config.runtime.kv_cache_group_size ?? 64;
      document.getElementById("cfg-stream-from-disk").checked = !!config.runtime.stream_from_disk;
      document.getElementById("cfg-stream-memory-percent").value = config.runtime.stream_memory_percent ?? 90;
      document.getElementById("cfg-extra-args").value = (config.runtime.extra_args || []).join(" ");

      const schedule = config.schedule || { enabled: false, rules: [] };
      const day = (schedule.rules || []).find((item) => item.name === "day") || { start: "06:00", end: "23:00", model_id: "" };
      const night = (schedule.rules || []).find((item) => item.name === "night") || { start: "23:00", end: "06:00", model_id: "" };
      document.getElementById("schedule-enabled").checked = !!schedule.enabled;
      document.getElementById("day-start").value = day.start;
      document.getElementById("day-end").value = day.end;
      document.getElementById("night-start").value = night.start;
      document.getElementById("night-end").value = night.end;
      setSelectOptions("day-model", day.model_id);
      setSelectOptions("night-model", night.model_id);
      renderRuntimeHints();
    }

    async function refreshAll() {
      const [status, models, config, runtimeMetadata] = await Promise.all([
        fetchJson("/api/status"),
        fetchJson("/api/models"),
        fetchJson("/api/config"),
        fetchJson("/api/runtime-metadata"),
      ]);
      state.status = status;
      state.models = models.items || [];
      state.config = config;
      state.runtimeMetadata = runtimeMetadata;
      renderSummary();
      renderModels();
      renderConfigForm();
    }

    async function saveConfig() {
      const adjusted = normalizeRuntimeForm();
      const config = structuredClone(state.config);
      config.model_roots = document.getElementById("model-roots").value.split("\\n").map((v) => v.trim()).filter(Boolean);
      config.runtime.vmlx_bin = document.getElementById("vmlx-bin").value.trim();
      config.runtime.default_enable_thinking = document.getElementById("cfg-thinking").checked;
      config.runtime.max_tokens = Number(document.getElementById("cfg-max-tokens").value);
      config.runtime.max_num_seqs = Number(document.getElementById("cfg-max-num-seqs").value);
      config.runtime.continuous_batching = document.getElementById("cfg-continuous-batching").checked;
      config.runtime.enable_prefix_cache = document.getElementById("cfg-prefix-cache").checked;
      config.runtime.cache_memory_percent = Number(document.getElementById("cfg-cache-memory-percent").value);
      config.runtime.use_paged_cache = document.getElementById("cfg-paged-cache").checked;
      config.runtime.paged_cache_block_size = Number(document.getElementById("cfg-paged-cache-block-size").value);
      config.runtime.max_cache_blocks = Number(document.getElementById("cfg-max-cache-blocks").value);
      config.runtime.kv_cache_quantization = document.getElementById("cfg-kv-cache-quantization").value;
      config.runtime.kv_cache_group_size = Number(document.getElementById("cfg-kv-cache-group-size").value);
      config.runtime.stream_from_disk = document.getElementById("cfg-stream-from-disk").checked;
      config.runtime.stream_memory_percent = Number(document.getElementById("cfg-stream-memory-percent").value);
      config.runtime.extra_args = document.getElementById("cfg-extra-args").value.trim()
        ? document.getElementById("cfg-extra-args").value.trim().split(/\\s+/)
        : [];
      await fetchJson("/api/config", {
        method: "PUT",
        body: JSON.stringify(config),
      });
      if (adjusted.length) {
        notice(adjusted.join(" "), false);
      }
    }

    async function saveSchedule() {
      const payload = {
        enabled: document.getElementById("schedule-enabled").checked,
        rules: [
          {
            name: "day",
            start: document.getElementById("day-start").value,
            end: document.getElementById("day-end").value,
            model_id: document.getElementById("day-model").value,
          },
          {
            name: "night",
            start: document.getElementById("night-start").value,
            end: document.getElementById("night-end").value,
            model_id: document.getElementById("night-model").value,
          }
        ],
      };
      await fetchJson("/api/schedule", {
        method: "PUT",
        body: JSON.stringify(payload),
      });
    }

    async function sendChatTest() {
      const payload = {
        prompt: document.getElementById("user-prompt").value,
        system_prompt: document.getElementById("system-prompt").value,
        max_tokens: Number(document.getElementById("chat-max-tokens").value),
      };
      const tempValue = document.getElementById("chat-temperature").value.trim();
      if (tempValue) payload.temperature = Number(tempValue);
      const response = await fetchJson("/api/chat-test", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      document.getElementById("chat-output").textContent = response.content || JSON.stringify(response, null, 2);
    }

    document.getElementById("refresh-btn").addEventListener("click", async () => {
      try { await refreshAll(); notice("Refreshed"); } catch (error) { notice(error.message, true); }
    });
    document.getElementById("rescan-btn").addEventListener("click", async () => {
      try {
        const response = await fetchJson("/api/rescan", { method: "POST", body: "{}" });
        await refreshAll();
        notice(`Rescanned ${response.count} models`);
      } catch (error) { notice(error.message, true); }
    });
    document.getElementById("reload-btn").addEventListener("click", async () => {
      try {
        await fetchJson("/api/reload", { method: "POST", body: "{}" });
        await refreshAll();
        notice("Reloaded current model");
      } catch (error) { notice(error.message, true); }
    });
    document.getElementById("unload-btn").addEventListener("click", async () => {
      try {
        await fetchJson("/api/unload", { method: "POST", body: "{}" });
        await refreshAll();
        notice("Runtime unloaded");
      } catch (error) { notice(error.message, true); }
    });
    document.getElementById("save-config-btn").addEventListener("click", async () => {
      try {
        await saveConfig();
        await refreshAll();
        notice("Runtime settings saved. They apply on next load or on Reload Current.");
      } catch (error) { notice(error.message, true); }
    });
    document.getElementById("cfg-kv-cache-quantization").addEventListener("change", () => {
      const adjusted = normalizeRuntimeForm();
      if (adjusted.length) notice(adjusted.join(" "), false);
    });
    document.getElementById("cfg-paged-cache").addEventListener("change", () => {
      const adjusted = normalizeRuntimeForm();
      if (adjusted.length) notice(adjusted.join(" "), false);
    });
    document.getElementById("cfg-stream-from-disk").addEventListener("change", () => {
      const adjusted = normalizeRuntimeForm();
      if (adjusted.length) notice(adjusted.join(" "), false);
    });
    document.getElementById("cfg-continuous-batching").addEventListener("change", () => {
      const adjusted = normalizeRuntimeForm();
      if (adjusted.length) notice(adjusted.join(" "), false);
    });
    document.getElementById("save-schedule-btn").addEventListener("click", async () => {
      try {
        await saveSchedule();
        await refreshAll();
        notice("Schedule saved");
      } catch (error) { notice(error.message, true); }
    });
    document.getElementById("send-chat-btn").addEventListener("click", async () => {
      try {
        document.getElementById("chat-output").textContent = "Waiting for response...";
        await sendChatTest();
      } catch (error) {
        document.getElementById("chat-output").textContent = error.message;
        notice(error.message, true);
      }
    });
    document.getElementById("open-webui-btn").addEventListener("click", () => {
      if (state.status?.open_webui_url) {
        window.open(state.status.open_webui_url, "_blank", "noopener,noreferrer");
      }
    });

    refreshAll().catch((error) => notice(error.message, true));
    setInterval(() => refreshAll().catch(() => {}), 10000);
  </script>
</body>
</html>"""
