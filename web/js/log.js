/* global requireAuth, apiFetch, getToken */

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();

  const statusEl = document.getElementById("log-status");
  const transcriptEl = document.getElementById("transcript-display");
  const formTextMeal = document.getElementById("form-text-meal");
  const btnText = document.getElementById("btn-save-text");
  const textarea = document.getElementById("meal-text");
  const btnMic = document.getElementById("btn-mic");
  const btnStop = document.getElementById("btn-stop");

  let mediaRecorder = null;
  let chunks = [];

  const elK = document.getElementById("log-today-kcal");
  const elP = document.getElementById("log-today-p");
  const elC = document.getElementById("log-today-c");
  const elF = document.getElementById("log-today-f");
  const elHint = document.getElementById("log-today-goal-hint");

  async function refreshTodayTotals() {
    try {
      const r = await apiFetch("/analytics/today");
      if (!r.ok) return;
      const d = await r.json();
      if (elK) elK.textContent = Math.round(d.consumed_calories).toLocaleString();
      if (elP) elP.textContent = `${Math.round(d.protein_g)}`;
      if (elC) elC.textContent = `${Math.round(d.carbs_g)}`;
      if (elF) elF.textContent = `${Math.round(d.fat_g)}`;
      if (elHint) {
        const left = Math.max(0, Math.round(d.kcal_remaining));
        elHint.textContent = `Goal ${d.goal_calories} kcal · ${left} kcal remaining today`;
      }
    } catch (e) {
      console.debug(e);
    }
  }

  refreshTodayTotals();

  function setStatus(msg) {
    if (statusEl) statusEl.textContent = msg;
  }

  function showResult(data) {
    if (transcriptEl) {
      transcriptEl.innerHTML = "";
      const t = document.createElement("p");
      t.className = "text-xl text-[#dbe3ef] leading-relaxed";
      t.textContent = data.transcript || "(no transcript)";
      transcriptEl.appendChild(t);
    }
    setStatus(
      `Saved: ${data.title} — ${Math.round(data.totals.calories)} kcal · P ${Math.round(data.totals.protein_g)}g`,
    );
  }

  async function saveTextMeal() {
    const text = (textarea?.value || "").trim();
    if (!text) {
      setStatus("Enter a meal description.");
      return;
    }
    setStatus("Saving…");
    if (btnText) btnText.disabled = true;
    try {
      const r = await apiFetch("/meals/text", { method: "POST", body: JSON.stringify({ text }) });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      showResult(data);
      if (textarea) textarea.value = "";
      await refreshTodayTotals();
    } catch (e) {
      console.error(e);
      setStatus("Failed to save.");
    } finally {
      if (btnText) btnText.disabled = false;
    }
  }

  if (formTextMeal && textarea) {
    formTextMeal.addEventListener("submit", (e) => {
      e.preventDefault();
      saveTextMeal();
    });
  } else if (btnText && textarea) {
    btnText.addEventListener("click", () => saveTextMeal());
  }

  if (btnMic) {
    btnMic.addEventListener("click", async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        chunks = [];
        const mime = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/mp4";
        mediaRecorder = new MediaRecorder(stream, { mimeType: mime });
        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size) chunks.push(e.data);
        };
        mediaRecorder.onstop = async () => {
          stream.getTracks().forEach((t) => t.stop());
          const blob = new Blob(chunks, { type: mime });
          setStatus("Uploading…");
          const fd = new FormData();
          fd.append("file", blob, "recording.webm");
          try {
            const r = await fetch(`${typeof NUTRIVOICE_API !== "undefined" ? NUTRIVOICE_API : "/api"}/meals/voice`, {
              method: "POST",
              headers: { Authorization: `Bearer ${getToken()}` },
              body: fd,
            });
            if (r.status === 401) {
              window.location.href = "/login.html";
              return;
            }
            if (!r.ok) throw new Error(await r.text());
            const data = await r.json();
            showResult(data);
            await refreshTodayTotals();
          } catch (e) {
            console.error(e);
            setStatus("Voice upload failed.");
          }
        };
        mediaRecorder.start();
        setStatus("Recording… click Stop when done.");
        if (btnStop) btnStop.classList.remove("hidden");
      } catch (e) {
        console.error(e);
        setStatus("Microphone permission denied or unavailable.");
      }
    });
  }

  if (btnStop) {
    btnStop.addEventListener("click", () => {
      if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        btnStop.classList.add("hidden");
      }
    });
  }
});
