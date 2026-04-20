const stateEls = {
  angle1Slider: document.getElementById("angle1Slider"),
  angle2Slider: document.getElementById("angle2Slider"),
  speedSlider: document.getElementById("speedSlider"),
  angle1Text: document.getElementById("angle1Text"),
  angle2Text: document.getElementById("angle2Text"),
  speedText: document.getElementById("speedText"),
  modeText: document.getElementById("modeText"),
  peerText: document.getElementById("peerText"),
  receiverText: document.getElementById("receiverText"),
  toggleReceiverBtn: document.getElementById("toggleReceiverBtn"),
  bindIp: document.getElementById("bindIp"),
  bindPort: document.getElementById("bindPort"),
  autoPeer: document.getElementById("autoPeer"),
  peerIp: document.getElementById("peerIp"),
  peerPort: document.getElementById("peerPort"),
  apiBase: document.getElementById("apiBase"),
  saveApiBaseBtn: document.getElementById("saveApiBaseBtn"),
  resetApiBaseBtn: document.getElementById("resetApiBaseBtn"),
  backendText: document.getElementById("backendText"),
  videoFeed: document.getElementById("videoFeed"),
  toast: document.getElementById("toast"),
};

const API_BASE_STORAGE_KEY = "snake_api_base";

function normalizeApiBase(raw) {
  const value = String(raw || "").trim();
  if (!value) return "";
  return value.replace(/\/+$/, "");
}

function getApiBase() {
  const fromQuery = new URLSearchParams(window.location.search).get("api");
  if (fromQuery) {
    const base = normalizeApiBase(fromQuery);
    if (base) {
      localStorage.setItem(API_BASE_STORAGE_KEY, base);
      return base;
    }
  }
  return normalizeApiBase(localStorage.getItem(API_BASE_STORAGE_KEY));
}

let apiBase = getApiBase();

function buildUrl(path) {
  return apiBase ? `${apiBase}${path}` : path;
}

function renderBackendInfo() {
  if (stateEls.apiBase) {
    stateEls.apiBase.value = apiBase;
  }
  if (stateEls.backendText) {
    stateEls.backendText.textContent = apiBase || "同源（当前域名）";
  }
  if (stateEls.videoFeed) {
    stateEls.videoFeed.src = buildUrl("/video_feed");
  }
}

function setToast(msg, isError = false) {
  stateEls.toast.textContent = msg || "";
  stateEls.toast.style.color = isError ? "#b91c1c" : "#0369a1";
}

async function api(path, body) {
  const res = await fetch(buildUrl(path), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  const data = await res.json();
  if (!res.ok || !data.ok) {
    throw new Error(data.error || "请求失败");
  }
  return data;
}

function renderState(state) {
  stateEls.angle1Slider.value = state.angle1;
  stateEls.angle2Slider.value = state.angle2;
  stateEls.speedSlider.value = state.speed;
  stateEls.angle1Text.textContent = state.angle1_display;
  stateEls.angle2Text.textContent = state.angle2_display;
  stateEls.speedText.textContent = String(state.speed);
  stateEls.modeText.textContent = state.mode;
  stateEls.bindIp.value = state.bind_ip || "";
  stateEls.bindPort.value = state.bind_port || "";
  stateEls.receiverText.textContent = state.receiver_running ? "运行中" : "未运行";
  stateEls.toggleReceiverBtn.textContent = state.receiver_running ? "停止接收" : "开启接收";

  if (state.peer && state.peer.length === 2) {
    stateEls.peerText.textContent = `${state.peer[0]}:${state.peer[1]}`;
  } else {
    stateEls.peerText.textContent = "-";
  }

  const carMode = state.mode === "小车模式";
  stateEls.angle1Slider.disabled = carMode;
  stateEls.angle2Slider.disabled = carMode;
}

async function refreshState() {
  const res = await fetch(buildUrl("/api/state"));
  const state = await res.json();
  renderState(state);
}

function bindActionButtons() {
  document.querySelectorAll("[data-action]").forEach((btn) => {
    const action = btn.getAttribute("data-action");
    const needStop = btn.getAttribute("data-stop-on-release") === "true";
    const start = async () => {
      try {
        const data = await api("/api/action", { action });
        renderState(data.state);
      } catch (err) {
        setToast(err.message, true);
      }
    };
    const stop = async () => {
      if (!needStop) return;
      try {
        const data = await api("/api/action", { action: "stop" });
        renderState(data.state);
      } catch (err) {
        setToast(err.message, true);
      }
    };
    btn.addEventListener("mousedown", start);
    btn.addEventListener("touchstart", start, { passive: true });
    btn.addEventListener("mouseup", stop);
    btn.addEventListener("mouseleave", stop);
    btn.addEventListener("touchend", stop);
  });
}

function bindControls() {
  if (stateEls.saveApiBaseBtn) {
    stateEls.saveApiBaseBtn.addEventListener("click", async () => {
      const nextBase = normalizeApiBase(stateEls.apiBase.value);
      apiBase = nextBase;
      if (nextBase) {
        localStorage.setItem(API_BASE_STORAGE_KEY, nextBase);
      } else {
        localStorage.removeItem(API_BASE_STORAGE_KEY);
      }
      renderBackendInfo();
      try {
        await refreshState();
        setToast("后端地址已更新");
      } catch (err) {
        setToast(`后端连接失败：${err.message}`, true);
      }
    });
  }

  if (stateEls.resetApiBaseBtn) {
    stateEls.resetApiBaseBtn.addEventListener("click", async () => {
      apiBase = "";
      localStorage.removeItem(API_BASE_STORAGE_KEY);
      renderBackendInfo();
      try {
        await refreshState();
        setToast("已恢复同源后端");
      } catch (err) {
        setToast(`连接失败：${err.message}`, true);
      }
    });
  }

  document.getElementById("toggleModeBtn").addEventListener("click", async () => {
    try {
      const data = await api("/api/mode");
      renderState(data.state);
    } catch (err) {
      setToast(err.message, true);
    }
  });

  stateEls.speedSlider.addEventListener("input", () => {
    stateEls.speedText.textContent = stateEls.speedSlider.value;
  });
  stateEls.speedSlider.addEventListener("change", async () => {
    try {
      const data = await api("/api/speed", { value: Number(stateEls.speedSlider.value) });
      renderState(data.state);
    } catch (err) {
      setToast(err.message, true);
    }
  });

  stateEls.angle1Slider.addEventListener("change", async () => {
    try {
      const data = await api("/api/angle", { name: "angle1", value: Number(stateEls.angle1Slider.value) });
      renderState(data.state);
    } catch (err) {
      setToast(err.message, true);
    }
  });
  stateEls.angle2Slider.addEventListener("change", async () => {
    try {
      const data = await api("/api/angle", { name: "angle2", value: Number(stateEls.angle2Slider.value) });
      renderState(data.state);
    } catch (err) {
      setToast(err.message, true);
    }
  });

  document.getElementById("applyPeerBtn").addEventListener("click", async () => {
    try {
      const data = await api("/api/peer", {
        ip: stateEls.peerIp.value.trim(),
        port: Number(stateEls.peerPort.value),
      });
      renderState(data.state);
      setToast("对端地址已应用");
    } catch (err) {
      setToast(err.message, true);
    }
  });

  stateEls.toggleReceiverBtn.addEventListener("click", async () => {
    const start = stateEls.toggleReceiverBtn.textContent.includes("开启");
    try {
      const data = await api("/api/receiver", {
        action: start ? "start" : "stop",
        bind_ip: stateEls.bindIp.value.trim(),
        bind_port: Number(stateEls.bindPort.value),
        auto_peer: stateEls.autoPeer.checked,
      });
      renderState(data.state);
      setToast(start ? "接收已开启" : "接收已停止");
    } catch (err) {
      setToast(err.message, true);
    }
  });
}

async function bootstrap() {
  renderBackendInfo();
  bindActionButtons();
  bindControls();
  await refreshState();
}

bootstrap().catch((err) => setToast(err.message, true));
