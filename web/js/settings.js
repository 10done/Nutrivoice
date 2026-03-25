/* global requireAuth, apiFetch, logout */

document.addEventListener("DOMContentLoaded", () => {
  requireAuth();

  const elEmail = document.getElementById("settings-email");
  const elCal = document.getElementById("goal-calories");
  const elP = document.getElementById("goal-protein");
  const elC = document.getElementById("goal-carbs");
  const elF = document.getElementById("goal-fat");
  const btnSave = document.getElementById("btn-save-settings");
  const btnLogout = document.getElementById("btn-logout");
  const err = document.getElementById("settings-error");
  const ok = document.getElementById("settings-saved");

  function showError(msg) {
    if (err) err.textContent = msg || "";
    if (ok) ok.textContent = "";
  }

  apiFetch("/me")
    .then(async (r) => {
      if (!r.ok) throw new Error(await r.text());
      return r.json();
    })
    .then((u) => {
      if (elEmail) elEmail.textContent = u.email;
      if (elCal) elCal.value = u.daily_calorie_goal;
      if (elP) elP.value = u.daily_protein_goal_g;
      if (elC) elC.value = u.daily_carbs_goal_g;
      if (elF) elF.value = u.daily_fat_goal_g;
    })
    .catch((e) => {
      console.error(e);
      showError("Could not load profile.");
    });

  if (btnSave) {
    btnSave.addEventListener("click", async () => {
      showError("");
      const body = {
        daily_calorie_goal: parseInt(elCal?.value || "2000", 10),
        daily_protein_goal_g: parseInt(elP?.value || "150", 10),
        daily_carbs_goal_g: parseInt(elC?.value || "220", 10),
        daily_fat_goal_g: parseInt(elF?.value || "65", 10),
      };
      try {
        const r = await apiFetch("/me/goals", { method: "PATCH", body: JSON.stringify(body) });
        if (!r.ok) throw new Error(await r.text());
        if (ok) ok.textContent = "Saved.";
      } catch (e) {
        console.error(e);
        showError("Save failed.");
      }
    });
  }

  if (btnLogout) {
    btnLogout.addEventListener("click", () => logout());
  }
});
