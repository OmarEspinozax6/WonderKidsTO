document.addEventListener("DOMContentLoaded", () => {
  const dialog = document.querySelector("#session-dialog");
  const form = document.querySelector("#session-form");
  const title = document.querySelector("#dialog-title");
  const content = document.querySelector("#dialog-content");
  let session = null;
  let mode = "details";

  const filterForm = document.querySelector("[data-live-filter]");
  const cards = [...document.querySelectorAll(".session-card")];
  const emptyFiltered = document.querySelector("#filtered-empty");
  const applyLiveFilter = () => {
    const values = [...filterForm.querySelectorAll("input[name=padre], input[name=especialidad], select")].map((input) => input.value.trim().toLowerCase()).filter(Boolean);
    let visible = 0;
    cards.forEach((card) => {
      const matches = values.every((value) => card.dataset.search.toLowerCase().includes(value) || card.dataset.session.toLowerCase().includes(value));
      card.hidden = !matches;
      if (matches) visible += 1;
    });
    if (emptyFiltered) emptyFiltered.hidden = visible > 0;
  };
  filterForm?.querySelectorAll("input[name=padre], input[name=especialidad], select").forEach((input) => input.addEventListener("input", applyLiveFilter));
  filterForm?.querySelector("input[name=fecha]")?.addEventListener("change", () => filterForm.submit());
  filterForm?.querySelectorAll("input[type=radio]").forEach((input) => input.addEventListener("change", () => filterForm.submit()));

  document.querySelectorAll(".session-card").forEach((card) => card.addEventListener("click", (event) => {
    const action = event.target.closest("[data-action]")?.dataset.action || "details";
    session = JSON.parse(card.dataset.session);
    mode = action;
    title.textContent = action === "reschedule" ? "Reprogramar sesion" : action === "cancel" ? "Cancelar sesion" : "Detalle de sesion";
    content.textContent = `${session.paciente} con ${session.terapeuta}\n${session.especialidad} · ${session.tipo_sesion} · Pago ${session.estado_pago}\n${session.notas || "Sin notas registradas."}`;
    form.elements.fecha.value = session.fecha;
    form.elements.hora_inicio.value = session.hora_inicio.slice(0, 5);
    form.elements.hora_fin.value = session.hora_fin.slice(0, 5);
    form.querySelector(".dialog-fields").hidden = action === "details" || action === "cancel";
    form.querySelector('[value="save"]').hidden = action === "details";
    dialog.showModal();
  }));

  form.addEventListener("submit", async (event) => {
    if (event.submitter?.value !== "save") return;
    event.preventDefault();
    const data = mode === "cancel" ? { estado: "cancelado" } : Object.fromEntries(new FormData(form));
    if (mode === "reschedule") data.estado = "reprogramada";
    const response = await fetch(`/api/sesiones/${session.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    if (response.ok) window.location.reload();
    else alert((await response.json()).error || "No se pudo actualizar la sesion.");
  });
});