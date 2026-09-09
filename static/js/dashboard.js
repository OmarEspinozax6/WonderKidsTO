document.addEventListener("DOMContentLoaded", () => {
  const filterForm = document.querySelector("[data-live-filter]");
  const inspector = document.querySelector("#session-inspector");
  const inspectorTitle = document.querySelector("#inspector-title");
  const inspectorContent = document.querySelector("#inspector-content");
  const dialog = document.querySelector("#session-dialog");
  const dialogForm = document.querySelector("#session-form");
  const resultsList = document.querySelector("#agenda-results-list");
  const resultsCount = document.querySelector("#agenda-results-count");
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

  const renderResults = (items) => {
    resultsCount.textContent = `${items.length} ${items.length === 1 ? "sesión" : "sesiones"}`;
    if (!items.length) {
      resultsList.innerHTML = '<div class="agenda-results-empty">No hay sesiones en este periodo.</div>';
      return;
    }
    resultsList.innerHTML = `<div class="agenda-table-wrap"><table class="agenda-table"><thead><tr><th>Fecha</th><th>Horario</th><th>Paciente</th><th>Terapeuta</th><th>Especialidad</th><th>Estado</th><th>Pago</th><th>Asistencia</th></tr></thead><tbody>${items.map((item) => `<tr data-result-id="${item.id}"><td>${item.fecha}</td><td>${item.hora_inicio.slice(0, 5)} - ${item.hora_fin.slice(0, 5)}</td><td><strong>${item.paciente || "Sesión grupal"}</strong></td><td>${item.terapeuta || "Equipo WonderKids"}</td><td>${item.especialidad || "Terapia"}</td><td><span class="status ${item.estado}">${item.estado}</span></td><td><span class="payment ${item.estado_pago}">${item.estado_pago}</span></td><td><button type="button" class="attendance-button ${item.asistencia === "asistio" ? "is-done" : ""}" data-attendance-id="${item.id}">${item.asistencia === "asistio" ? "Asistió" : "Marcar"}</button></td></tr>`).join("")}</tbody></table></div>`;
    resultsList.querySelectorAll("[data-result-id]").forEach((row) => row.addEventListener("click", () => {
      const event = calendar.getEventById(row.dataset.resultId);
      if (event) { selectedSession = event.extendedProps; inspector.hidden = false; inspectorTitle.textContent = selectedSession.paciente || "Sesión grupal"; inspectorContent.textContent = `${selectedSession.fecha} · ${selectedSession.hora_inicio.slice(0, 5)}-${selectedSession.hora_fin.slice(0, 5)}\n${selectedSession.terapeuta || "Equipo WonderKids"} · ${selectedSession.especialidad || "Terapia"}\n${selectedSession.padre_nombre || "Familiar no registrado"} · Pago ${selectedSession.estado_pago}`; }
    }));
    resultsList.querySelectorAll("[data-attendance-id]").forEach((button) => button.addEventListener("click", async (event) => {
      event.stopPropagation();
      const item = items.find((session) => String(session.id) === button.dataset.attendanceId);
      if (!item || !item.paciente_id) return;
      const response = await fetch(`/api/agenda/${item.id}/asistencia`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ paciente_id: item.paciente_id, asistencia: "asistio" }) });
      if (response.ok) { item.asistencia = "asistio"; renderResults(items); }
      else alert((await response.json()).error || "No se pudo guardar la asistencia.");
    }));
  };

  const calendar = new FullCalendar.Calendar(document.querySelector("#calendar"), {
    locale: "es", timeZone: "UTC", initialView: "timeGridDay", initialDate: document.querySelector("#calendar").dataset.initialDate, firstDay: 1,
    height: "auto", nowIndicator: false, allDaySlot: false, slotEventOverlap: false, eventMaxStack: 20, slotMinTime: "06:00:00", slotMaxTime: "22:00:00", slotDuration: "00:30:00", slotLabelInterval: "01:00:00", slotLabelFormat: { hour: "2-digit", minute: "2-digit", hour12: false },
    eventTimeFormat: { hour: "2-digit", minute: "2-digit", hour12: false },
    headerToolbar: { left: "prev,next today", center: "title", right: "" },
    events: async (info, success, failure) => {
      try {
        const params = new URLSearchParams({ start: info.startStr.slice(0, 10), end: info.endStr.slice(0, 10), ...filters() });
        const response = await fetch(`/api/agenda?${params}`);
        const result = await response.json();
        if (!response.ok) throw new Error(result.error);
        const items = result.data || [];
        renderResults(items);
        success(items.map((item) => ({ id: String(item.id), title: item.paciente || "Sesión grupal", start: `${item.fecha}T${item.hora_inicio}Z`, end: `${item.fecha}T${item.hora_fin}Z`, extendedProps: item })));
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
  document.querySelectorAll("[data-inspector-action]").forEach((button) => button.addEventListener("click", async () => {
    if (button.dataset.inspectorAction !== "attendance") { openDialog(button.dataset.inspectorAction); return; }
    if (!selectedSession?.paciente_id) return;
    const response = await fetch(`/api/agenda/${selectedSession.id}/asistencia`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ paciente_id: selectedSession.paciente_id, asistencia: "asistio" }) });
    if (response.ok) { selectedSession.asistencia = "asistio"; inspectorContent.textContent += "\nAsistencia: asistió"; calendar.refetchEvents(); }
    else alert((await response.json()).error || "No se pudo guardar la asistencia.");
  }));
  document.querySelector("#inspector-close")?.addEventListener("click", () => {
    inspector.hidden = true;
    selectedSession = null;
    calendar.unselect();
  });

  dialogForm.addEventListener("submit", async (event) => {
    if (event.submitter?.value !== "save") return;
    event.preventDefault();
    if (actionMode === "attendance") {
      const response = await fetch(`/api/agenda/${selectedSession.id}/asistencia`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ paciente_id: selectedSession.paciente_id, asistencia: "asistio" }) });
      if (response.ok) { selectedSession.asistencia = "asistio"; inspectorContent.textContent += "\nAsistencia: asistió"; dialog.close(); calendar.refetchEvents(); }
      else alert((await response.json()).error || "No se pudo guardar la asistencia.");
      return;
    }
    const data = actionMode === "cancel" ? { estado: "cancelado" } : Object.fromEntries(new FormData(dialogForm));
    if (actionMode === "reschedule") data.estado = "reprogramada";
    const response = await fetch(`/api/sesiones/${selectedSession.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
    if (response.ok) { dialog.close(); calendar.refetchEvents(); inspector.hidden = true; }
    else alert((await response.json()).error || "No se pudo actualizar la sesión.");
  });
  dialogForm.addEventListener("close", () => { actionMode = "details"; });
});