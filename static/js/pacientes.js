document.addEventListener("DOMContentLoaded", () => {
  const form = document.querySelector("#paciente-form");
  const list = document.querySelector("#pacientes-body");

  if (form) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const data = Object.fromEntries(new FormData(form));
      data.asistencia = form.elements.asistencia.checked;
      const id = form.dataset.id;
      const response = await fetch(id ? `/api/pacientes/${id}` : "/api/pacientes", {
        method: id ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });
      if (response.ok) window.location.href = "/pacientes";
      else alert((await response.json()).error || "No se pudo guardar el paciente.");
    });
  }

  list?.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-delete-id]");
    if (!button || !window.confirm("Eliminar este paciente?")) return;
    const response = await fetch(`/api/pacientes/${button.dataset.deleteId}`, { method: "DELETE" });
    if (response.ok) window.location.reload();
    else alert((await response.json()).error || "No se pudo eliminar el paciente.");
  });
});