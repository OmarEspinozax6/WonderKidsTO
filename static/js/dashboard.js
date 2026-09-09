document.addEventListener("DOMContentLoaded", () => {
  const dialog = document.querySelector("#session-dialog");
  const form = document.querySelector("#session-form");
  const title = document.querySelector("#dialog-title");
  const content = document.querySelector("#dialog-content");
  let session = null;
  let mode = "details";

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
    const data = mode === "cancel" ? { estado: "cancelada" } : Object.fromEntries(new FormData(form));
    if (mode === "reschedule") data.estado = "reprogramada";
    const response = await fetch(`/api/sesiones/${session.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    if (response.ok) window.location.reload();
    else alert((await response.json()).error || "No se pudo actualizar la sesion.");
  });
});