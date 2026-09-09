document.addEventListener("DOMContentLoaded", () => {
  const filterForm = document.querySelector("[data-live-filter]");
  const inspector = document.querySelector("#session-inspector");
  const inspectorTitle = document.querySelector("#inspector-title");
  const inspectorContent = document.querySelector("#inspector-content");
  const dialog = document.querySelector("#session-dialog");
  const dialogForm = document.querySelector("#session-form");
  let selectedSession = null;
  let actionMode = "details";

  const filters = () => Object.fromEntries(
    [...filterForm.querySelectorAll("input[name=padre], input[name=especialidad], select")]
      .map((input) => [input.name, input.value.trim()])
      .filter(([, value]) => value)
  );

  const openDialog = (mode) => {
    if (!selectedSession) return;
    actionMode = mode;
    document.querySelector("#dialog-title").textContent = mode === "reschedule" ? "Reprogramar sesión" : mode === "cancel" ? "Cancelar sesión" : "Detalle de sesión";
    document.querySelector("#dialog-content").textContent = `${selectedSession.paciente || "Sesión grupal"} con ${selectedSession.terapeuta || "Equipo WonderKids"}\n${selectedSession.especialidad} · ${selectedSession.tipo_sesion} · Pago ${selectedSession.estado_pago}`;
    dialogForm.elements.fecha.value = selectedSession.fecha;
    dialogForm.elements.hora_inicio.value = selectedSession.hora_inicio.slice(0, 5);
    dialogForm.elements.hora_fin.value = selectedSession.hora_fin.slice(0, 5);
    dialogForm.querySelector(".dialog-fields").hidden = mode === "details" || mode === "cancel";
    dialogForm.querySelector('[value="save"]').hidden = mode === "details";
    dialog.showModal();
  };

  const calendar = new FullCalendar.Calendar(document.querySelector("#calendar"), {
    locale: "es", initialView: "timeGridDay", initialDate: document.querySelector("#calendar").dataset.initialDate, firstDay: 1,
    height: "auto", nowIndicator: true, allDaySlot: false, slotEventOverlap: false, eventMaxStack: 8, slotMinTime: "07:00:00", slotMaxTime: "21:00:00",
    eventTimeFormat: { hour: "2-digit", minute: "2-digit", hour12: false },
    headerToolbar: { left: "prev,next today", center: "title", right: "" },
    events: async (info, success, failure) => {
      try {
        const params = new URLSearchParams({ start: info.startStr.slice(0, 10), end: info.endStr.slice(0, 10), ...filters() });
        const response = await fetch(`/api/agenda?${params}`);
        const result = await response.json();
        if (!response.ok) throw new Error(result.error);
        success((result.data || []).map((item) => ({ id: item.id, title: item.paciente || "Sesión grupal", start: `${item.fecha}T${item.hora_inicio}`, end: `${item.fecha}T${item.hora_fin}`, extendedProps: item })));
      } catch (error) { failure(error); }
    },
    eventContent: (info) => {
      const item = info.event.extendedProps;
      const patient = item.paciente || "Sesión grupal";
      const therapist = item.terapeuta || "Equipo WonderKids";
      const specialty = item.especialidad || "Terapia";
      return { html: `<div class="calendar-event-body"><strong>${info.timeText}</strong><span>${patient}</span><small>${therapist} · ${specialty}</small></div>` };
    },
    eventClick: (info) => {
      selectedSession = info.event.extendedProps;
      inspector.hidden = false;
      inspectorTitle.textContent = selectedSession.paciente || "Sesión grupal";
      inspectorContent.textContent = `${selectedSession.fecha} · ${selectedSession.hora_inicio.slice(0, 5)}-${selectedSession.hora_fin.slice(0, 5)}\n${selectedSession.terapeuta || "Equipo WonderKids"} · ${selectedSession.especialidad}\n${selectedSession.padre_nombre || "Familiar no registrado"} · Pago ${selectedSession.estado_pago}`;
    },
  });
  calendar.render();

  document.querySelectorAll("[data-calendar-view]").forEach((button) => button.addEventListener("click", () => {
    calendar.changeView(button.dataset.calendarView);
    document.querySelectorAll("[data-calendar-view]").forEach((item) => item.classList.toggle("active", item === button));
  }));
  document.querySelector("input[name=fecha]")?.addEventListener("change", (event) => calendar.gotoDate(event.target.value));
  filterForm.querySelectorAll("input[name=padre], input[name=especialidad], select").forEach((input) => input.addEventListener("input", () => calendar.refetchEvents()));
  document.querySelectorAll("[data-inspector-action]").forEach((button) => button.addEventListener("click", () => openDialog(button.dataset.inspectorAction)));
  document.querySelector("#inspector-close")?.addEventListener("click", () => {
    inspector.hidden = true;
    selectedSession = null;
    calendar.unselect();
  });

  dialogForm.addEventListener("submit", async (event) => {
    if (event.submitter?.value !== "save") return;
    event.preventDefault();
    const data = actionMode === "cancel" ? { estado: "cancelado" } : Object.fromEntries(new FormData(dialogForm));
    if (actionMode === "reschedule") data.estado = "reprogramada";
    const response = await fetch(`/api/sesiones/${selectedSession.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    if (response.ok) { dialog.close(); calendar.refetchEvents(); inspector.hidden = true; }
    else alert((await response.json()).error || "No se pudo actualizar la sesión.");
  });
  dialogForm.addEventListener("close", () => { actionMode = "details"; });
});