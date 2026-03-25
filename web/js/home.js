/* global requireAuth, apiFetch */

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();

  const elDate = document.getElementById("daily-date");
  const elLeft = document.getElementById("kcal-left");
  const elConsumed = document.getElementById("kcal-consumed");
  const elRing = document.getElementById("ring-progress");
  const elP = document.getElementById("macro-protein");
  const elC = document.getElementById("macro-carbs");
  const elF = document.getElementById("macro-fat");
  const barP = document.getElementById("bar-protein");
  const barC = document.getElementById("bar-carbs");
  const barF = document.getElementById("bar-fat");
  const elKcalGoal = document.getElementById("kcal-goal-display");
  const sideMealsToday = document.getElementById("side-meals-today");
  const sidePctGoal = document.getElementById("side-pct-goal");
  const sideWater = document.getElementById("side-water-goal");
  const grid = document.getElementById("recent-meals-grid");
  const homeError = document.getElementById("home-error");
  const formHomeMeal = document.getElementById("form-home-text-meal");
  const homeMealText = document.getElementById("home-meal-text");
  const btnHomeSave = document.getElementById("btn-home-save-meal");
  const homeMealStatus = document.getElementById("home-meal-status");

  const today = new Date();
  if (elDate) elDate.textContent = today.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" });

  function pctBar(consumed, goal) {
    if (!goal || goal <= 0) return 0;
    return Math.min(100, Math.round((consumed / goal) * 100));
  }

  function renderDashboard(todayData, meals, todayMealCount) {
    if (homeError) homeError.textContent = "";

    if (elLeft) elLeft.textContent = Math.round(todayData.kcal_remaining).toLocaleString();
    if (elConsumed) elConsumed.textContent = Math.round(todayData.consumed_calories).toLocaleString();
    if (elKcalGoal) elKcalGoal.textContent = String(todayData.goal_calories ?? "—");

    const goal = todayData.goal_calories || 1;
    const pct = Math.min(todayData.consumed_calories / goal, 1);
    const circumference = 2 * Math.PI * 110;
    if (elRing) {
      elRing.style.strokeDasharray = String(circumference);
      elRing.style.strokeDashoffset = String(circumference * (1 - pct));
    }

    if (elP) elP.textContent = `${Math.round(todayData.protein_g)}g / ${todayData.protein_goal_g}g`;
    if (elC) elC.textContent = `${Math.round(todayData.carbs_g)}g / ${todayData.carbs_goal_g}g`;
    if (elF) elF.textContent = `${Math.round(todayData.fat_g)}g / ${todayData.fat_goal_g}g`;

    if (barP) barP.style.width = `${pctBar(todayData.protein_g, todayData.protein_goal_g)}%`;
    if (barC) barC.style.width = `${pctBar(todayData.carbs_g, todayData.carbs_goal_g)}%`;
    if (barF) barF.style.width = `${pctBar(todayData.fat_g, todayData.fat_goal_g)}%`;

    if (sideMealsToday != null) sideMealsToday.textContent = String(todayMealCount);
    if (sidePctGoal != null) sidePctGoal.textContent = `${Math.round(pct * 100)}%`;
    if (sideWater != null) sideWater.textContent = todayData.water_goal_ml != null ? String(todayData.water_goal_ml) : "—";

    if (grid) {
      grid.innerHTML = "";
      const list = meals.items || [];
      if (list.length === 0) {
        const empty = document.createElement("div");
        empty.className =
          "col-span-full rounded-xl border border-dashed border-[#2e363e] bg-[#141c24]/50 p-10 text-center text-[#bec8c9] text-sm";
        empty.innerHTML =
          '<p class="mb-2">No meals logged yet today in your recent list.</p><a href="/log.html" class="font-bold text-[#66d9cc] hover:underline">Add one with voice or text →</a>';
        grid.appendChild(empty);
      }
      list.forEach((item) => {
        const card = document.createElement("div");
        card.className =
          "bg-[#232b33] rounded-xl p-6 border border-[#2e363e]/50 hover:border-primary/30 transition-colors";
        card.innerHTML = `
            <div class="flex justify-between items-start gap-2 mb-2">
              <h4 class="font-bold text-[#dbe3ef] flex-1 min-w-0">${escapeHtml(item.title || "Meal")}</h4>
              <div class="flex items-start gap-2 shrink-0">
                <span class="text-[#66d9cc] font-bold">${Math.round(item.calories)} <span class="text-xs text-[#bec8c9]">kcal</span></span>
                <button type="button" class="meal-delete-btn text-[#bec8c9] hover:text-red-400 p-1 rounded-lg hover:bg-[#2e363e] transition-colors" title="Delete meal" aria-label="Delete meal" data-meal-id="${escapeHtml(item.id)}">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                </button>
              </div>
            </div>
            <p class="text-xs text-[#bec8c9]">P ${Math.round(item.protein_g)}g · C ${Math.round(item.carbs_g)}g · F ${Math.round(item.fat_g)}g</p>
          `;
        grid.appendChild(card);
      });

      grid.querySelectorAll(".meal-delete-btn").forEach((btn) => {
        btn.addEventListener("click", async (ev) => {
          ev.preventDefault();
          const id = btn.getAttribute("data-meal-id");
          if (!id || !confirm("Delete this meal from your log?")) return;
          btn.setAttribute("disabled", "true");
          try {
            const r = await apiFetch(`/meals/${encodeURIComponent(id)}`, { method: "DELETE" });
            if (!r.ok) throw new Error(await r.text());
            await refreshDashboard();
          } catch (err) {
            console.error(err);
            if (homeError) homeError.textContent = "Could not delete meal.";
            btn.removeAttribute("disabled");
          }
        });
      });
    }
  }

  async function refreshDashboard() {
    const [a, m] = await Promise.all([apiFetch("/analytics/today"), apiFetch("/meals?limit=40")]);
    if (!a.ok) throw new Error(await a.text());
    if (!m.ok) throw new Error(await m.text());
    const todayData = await a.json();
    const meals = await m.json();
    const dayPrefix = new Date().toISOString().slice(0, 10);
    const todayMealCount = (meals.items || []).filter((i) => String(i.logged_at).startsWith(dayPrefix)).length;
    const recentOnly = { items: (meals.items || []).slice(0, 6) };
    renderDashboard(todayData, recentOnly, todayMealCount);
  }

  refreshDashboard().catch((e) => {
    console.error(e);
    if (homeError) homeError.textContent = "Could not load dashboard.";
  });

  if (formHomeMeal && homeMealText) {
    formHomeMeal.addEventListener("submit", async (e) => {
      e.preventDefault();
      const text = (homeMealText.value || "").trim();
      if (!text) {
        if (homeMealStatus) homeMealStatus.textContent = "Describe what you ate.";
        return;
      }
      if (homeMealStatus) homeMealStatus.textContent = "Saving…";
      if (btnHomeSave) btnHomeSave.disabled = true;
      try {
        const r = await apiFetch("/meals/text", { method: "POST", body: JSON.stringify({ text }) });
        if (!r.ok) throw new Error(await r.text());
        const data = await r.json();
        homeMealText.value = "";
        if (homeMealStatus) {
          homeMealStatus.textContent = `Saved: ${data.title} — ${Math.round(data.totals.calories)} kcal`;
        }
        await refreshDashboard();
      } catch (err) {
        console.error(err);
        if (homeMealStatus) homeMealStatus.textContent = "Could not save meal.";
      } finally {
        if (btnHomeSave) btnHomeSave.disabled = false;
      }
    });
  }
});

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}
