let lastListenToken = 0;
let lastTurnToken = 0;
let partialTimer = 0;
let ws = null;
let stream = null;
let audioContext = null;
let processor = null;
let sessionReady = false;
let listening = false;
let connecting = false;
let listeningDuringAnswer = false;

const SAMPLE_RATE = 16000;
const STATUS_DURING_ANSWER = "Listening to audio.";
const STATUS_LISTENING = "Listening… pause when you finish your question.";

function setStatus(root, text) {
  const el = root.querySelector("#status");
  if (el) el.textContent = text;
}

function emitPartial(setTriggerValue, text) {
  window.clearTimeout(partialTimer);
  partialTimer = window.setTimeout(() => {
    setTriggerValue("partial", text);
  }, 200);
}

function clearPartial(setTriggerValue) {
  window.clearTimeout(partialTimer);
  setTriggerValue("partial", "");
}

function findLatestChatAudio() {
  const audios = document.querySelectorAll("audio");
  if (!audios.length) return null;
  return audios[audios.length - 1];
}

function pauseAnswerAudio() {
  const pageAudio = findLatestChatAudio();
  if (pageAudio && !pageAudio.paused) {
    pageAudio.pause();
  }
}

function pcmBase64(float32Array) {
  const inputRate = audioContext.sampleRate;
  const ratio = inputRate / SAMPLE_RATE;
  const length = Math.round(float32Array.length / ratio);
  const buffer = new ArrayBuffer(length * 2);
  const view = new DataView(buffer);
  for (let i = 0; i < length; i += 1) {
    const sample = float32Array[Math.min(float32Array.length - 1, Math.floor(i * ratio))];
    const clipped = Math.max(-1, Math.min(1, sample));
    view.setInt16(i * 2, clipped < 0 ? clipped * 0x8000 : clipped * 0x7fff, true);
  }
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 512) {
    binary += String.fromCharCode.apply(null, bytes.subarray(i, i + 512));
  }
  return btoa(binary);
}

function sendChunk(float32Chunk) {
  if (!sessionReady || !ws || ws.readyState !== WebSocket.OPEN) return;
  ws.send(
    JSON.stringify({
      message_type: "input_audio_chunk",
      audio_base_64: pcmBase64(float32Chunk),
      commit: false,
      sample_rate: SAMPLE_RATE,
    }),
  );
}

function cleanup() {
  listening = false;
  sessionReady = false;
  connecting = false;
  listeningDuringAnswer = false;
  if (processor) {
    processor.disconnect();
    processor = null;
  }
  if (audioContext) {
    audioContext.close();
    audioContext = null;
  }
  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    stream = null;
  }
  if (ws) {
    ws.close();
    ws = null;
  }
}

function stopListening(root, setTriggerValue, keepStatus = false) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(
      JSON.stringify({
        message_type: "input_audio_chunk",
        audio_base_64: "",
        commit: true,
        sample_rate: SAMPLE_RATE,
      }),
    );
  }
  cleanup();
  clearPartial(setTriggerValue);
  if (!keepStatus) {
    setStatus(root, "");
  }
}

async function startMic(root) {
  stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  audioContext = new AudioContext({ sampleRate: SAMPLE_RATE });
  const source = audioContext.createMediaStreamSource(stream);
  processor = audioContext.createScriptProcessor(4096, 1, 1);
  processor.onaudioprocess = (event) => {
    if (listening) sendChunk(event.inputBuffer.getChannelData(0));
  };
  source.connect(processor);
  processor.connect(audioContext.destination);
  listening = true;
  connecting = false;
  setStatus(root, listeningDuringAnswer ? STATUS_DURING_ANSWER : STATUS_LISTENING);
}

export default function voiceAgentMic(component) {
  const { data, setTriggerValue, parentElement } = component;
  if (!parentElement) {
    return () => {};
  }

  const root = parentElement;
  const wsUrl = String(data?.ws_url || "");
  const active = Boolean(data?.active);
  const listenToken = Number(data?.listen_token || 0);
  const turnToken = Number(data?.turn_token || 0);

  function reportError(message) {
    setStatus(root, message);
    cleanup();
    clearPartial(setTriggerValue);
    setTriggerValue("error", message);
  }

  async function startListening(duringAnswer = false) {
    if (connecting || listening || !wsUrl) {
      if (!wsUrl) setStatus(root, "Missing login token. Sign in again from the home page.");
      return;
    }
    cleanup();
    clearPartial(setTriggerValue);
    listeningDuringAnswer = duringAnswer;
    connecting = true;
    setStatus(root, duringAnswer ? STATUS_DURING_ANSWER : "Connecting…");
    ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      let payload;
      try {
        payload = JSON.parse(event.data);
      } catch (_) {
        return;
      }
      const type = payload.message_type;
      if (type === "session_started") {
        sessionReady = true;
        startMic(root).catch((err) => reportError(`Microphone error: ${err.message}`));
        return;
      }
      if (type === "partial_transcript" && payload.text) {
        emitPartial(setTriggerValue, payload.text);
        return;
      }
      if (
        (type === "committed_transcript" || type === "committed_transcript_with_timestamps") &&
        payload.text
      ) {
        pauseAnswerAudio();
        clearPartial(setTriggerValue);
        listeningDuringAnswer = false;
        setStatus(root, "Sending to agent…");
        setTriggerValue("transcript", JSON.stringify({ text: payload.text, id: Date.now() }));
        stopListening(root, setTriggerValue, true);
        return;
      }
      if (type === "error" || type === "auth_error") {
        reportError(payload.error || "Speech recognition error.");
      }
    };

    ws.onerror = () => {
      reportError("WebSocket connection failed. Is the API running on port 8000?");
    };

    ws.onclose = () => {
      if (listening || connecting) setStatus(root, "Connection closed.");
      cleanup();
    };
  }

  function continueConversation() {
    const pageAudio = findLatestChatAudio();
    setStatus(root, STATUS_DURING_ANSWER);

    if (pageAudio && pageAudio.paused && !pageAudio.ended) {
      pageAudio.play().catch(() => {});
    }

    startListening(true);
  }

  if (!active) {
    if (listening || connecting) {
      stopListening(root, setTriggerValue);
    } else {
      clearPartial(setTriggerValue);
    }
    lastListenToken = listenToken;
  } else if (listenToken > lastListenToken && wsUrl) {
    startListening(false);
    lastListenToken = listenToken;
  }

  if (turnToken > lastTurnToken) {
    lastTurnToken = turnToken;
    continueConversation();
  }

  return () => {};
}
