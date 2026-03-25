/* global requireAuth, apiFetch */

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();

  const chart = document.getElementById("cal-chart");
  const avgEl = document.getElementById("avg-calories");
  const proteinEl = document.getElementById("protein-avg");
  const hitsEl = document.getElementById("protein-hits");
  const historyEl = document.getElementById("history-list");
  const errEl = document.getElementById("insights-error");

  let period = "7d";

  function bindPeriodButtons() {
    document.querySelectorAll("[data-period]").forEach((btn) => {
      btn.addEventListener("click", () => {
        period = btn.getAttribute("data-period") || "7d";
        document.querySelectorAll("[data-period]").forEach((b) => {
          b.classList.remove("bg-[#66d9cc]", "text-[#003732]", "font-bold");
          b.classList.add("text-[#bec8c9]");
        });
        btn.classList.add("bg-[#66d9cc]", "text-[#003732]", "font-bold");
        btn.classList.remove("text-[#bec8c9]");
        load();
      });
    });
  }

  function escapeHtml(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  function mealsInSelectedPeriod(items) {
    const days = period === "30d" ? 30 : 7;
    const start = new Date();
    start.setHours(0, 0, 0, 0);
    start.setDate(start.getDate() - (days - 1));
    return (items || []).filter((m) => new Date(m.logged_at) >= start);
  }

  function renderMacroMix(mealsList) {
    const items = mealsInSelectedPeriod(mealsList);
    let pG = 0;
    let cG = 0;
    let fG = 0;
    let kcalSum = 0;
    items.forEach((m) => {
      pG += Number(m.protein_g) || 0;
      cG += Number(m.carbs_g) || 0;
      fG += Number(m.fat_g) || 0;
      kcalSum += Number(m.calories) || 0;
    });
    const pCal = pG * 4;
    const cCal = cG * 4;
    const fCal = fG * 9;
    const macro = pCal + cCal + fCal;
    const elP = document.getElementById("mix-p");
    const elC = document.getElementById("mix-c");
    const elF = document.getElementById("mix-f");
    const pctP = document.getElementById("mix-p-pct");
    const pctC = document.getElementById("mix-c-pct");
    const pctF = document.getElementById("mix-f-pct");
    const totalEl = document.getElementById("mix-total-kcal");
    if (macro <= 0) {
      if (elP) elP.style.width = "0%";
      if (elC) elC.style.width = "0%";
      if (elF) elF.style.width = "0%";
      if (pctP) pctP.textContent = "—";
      if (pctC) pctC.textContent = "—";
      if (pctF) pctF.textContent = "—";
      if (totalEl) totalEl.textContent = "0";
      return;
    }
    const wp = Math.round((pCal / macro) * 100);
    const wc = Math.round((cCal / macro) * 100);
    const wf = Math.max(0, 100 - wp - wc);
    if (elP) elP.style.width = `${wp}%`;
    if (elC) elC.style.width = `${wc}%`;
    if (elF) elF.style.width = `${wf}%`;
    if (pctP) pctP.textContent = `${wp}%`;
    if (pctC) pctC.textContent = `${wc}%`;
    if (pctF) pctF.textContent = `${wf}%`;
    if (totalEl) totalEl.textContent = String(Math.round(kcalSum));
  }

  async function load() {
    try {
      const r = await apiFetch(`/analytics/summary?period=${encodeURIComponent(period)}`);
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      if (avgEl) avgEl.textContent = String(Math.round(data.average_daily_calories));
      if (proteinEl) proteinEl.textContent = `${Math.round(data.protein_daily_avg_g)}g`;
      if (hitsEl) hitsEl.textContent = `${data.protein_goal_hits} / ${data.protein_days_in_period} days`;

      if (chart) {
        chart.innerHTML = "";
        const maxCal = Math.max(...data.days.map((d) => d.calories), 1);
        data.days.forEach((d) => {
          const col = document.createElement("div");
          col.className = "flex flex-col items-center gap-2 flex-1";
          const h = Math.round((d.calories / maxCal) * 100);
          col.innerHTML = `
            <div class="w-full relative h-32 flex flex-col justify-end">
              <div class="rounded-t-lg w-full bg-gradient-to-t from-[#006159] to-[#66d9cc]" style="height:${h}%"></div>
            </div>
            <span class="text-[10px] text-[#bec8c9]">${d.date.slice(5)}</span>
          `;
          chart.appendChild(col);
        });
      }

      const mr = await apiFetch("/meals?limit=50");
      if (!mr.ok) throw new Error(await mr.text());
      const meals = await mr.json();
      renderMacroMix(meals.items || []);
      if (historyEl) {
        historyEl.innerHTML = "";
        (meals.items || []).forEach((m) => {
          const row = document.createElement("div");
          row.className =
            "px-4 py-3 flex justify-between items-center gap-3 border-b border-[#2e363e]/30 group";
          const when = new Date(m.logged_at).toLocaleString();
          row.innerHTML = `
            <div class="min-w-0 flex-1">
              <div class="font-medium text-[#dbe3ef]">${escapeHtml(m.title || "Meal")}</div>
              <div class="text-xs text-[#bec8c9]">${escapeHtml(when)} · ${escapeHtml(m.review_status || "")}</div>
            </div>
            <div class="flex items-center gap-3 shrink-0">
              <div class="text-right">
                <div class="font-bold">${Math.round(m.calories)} kcal</div>
                <div class="text-[10px] text-[#bec8c9]">P ${Math.round(m.protein_g)}g</div>
              </div>
              <button type="button" class="meal-delete-btn text-[#bec8c9] hover:text-red-400 p-2 rounded-lg hover:bg-[#2e363e]/80 opacity-70 group-hover:opacity-100 transition-all" title="Delete" aria-label="Delete meal" data-meal-id="${escapeHtml(m.id)}">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
              </button>
            </div>
          `;
          historyEl.appendChild(row);
        });
      }
    } catch (e) {
      console.error(e);
      if (errEl) errEl.textContent = "Could not load insights.";
    }
  }

  bindPeriodButtons();

  if (historyEl) {
    historyEl.addEventListener("click", async (ev) => {
      const btn = ev.target.closest(".meal-delete-btn");
      if (!btn || !historyEl.contains(btn)) return;
      const id = btn.getAttribute("data-meal-id");
      if (!id || !confirm("Delete this meal from your log?")) return;
      btn.setAttribute("disabled", "true");
      try {
        const dr = await apiFetch(`/meals/${encodeURIComponent(id)}`, { method: "DELETE" });
        if (!dr.ok) throw new Error(await dr.text());
        await load();
      } catch (e) {
        console.error(e);
        if (errEl) errEl.textContent = "Could not delete meal.";
        btn.removeAttribute("disabled");
      }
    });
  }

  load();
});
