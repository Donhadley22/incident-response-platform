const form = document.querySelector("#incident-form");
const list = document.querySelector("#incidents");
const message = document.querySelector("#message");
const source = document.querySelector("#source");
const refresh = document.querySelector("#refresh");

async function loadIncidents() {
  const response = await fetch("/api/incidents");
  const data = await response.json();
  source.textContent = `source: ${data.source}`;

  if (!data.items.length) {
    list.innerHTML = "<p>No incidents yet.</p>";
    return;
  }

  list.innerHTML = data.items.map(renderIncident).join("");
}

function renderIncident(incident) {
  const canAcknowledge = incident.status === "open";
  const canResolve = incident.status !== "resolved";

  return `
    <article class="incident" data-severity="${incident.severity}">
      <div class="incident-title">
        <h3>${escapeHtml(incident.title)}</h3>
        <span class="badge">${incident.severity}</span>
      </div>
      <p class="meta">${escapeHtml(incident.service_name)} - ${escapeHtml(incident.status)} - ${escapeHtml(incident.owner)}</p>
      <p>${escapeHtml(incident.summary)}</p>
      <div class="actions">
        ${canAcknowledge ? `<button class="secondary" data-id="${incident.id}" data-status="acknowledged">Acknowledge</button>` : ""}
        ${canResolve ? `<button data-id="${incident.id}" data-status="resolved">Resolve</button>` : ""}
      </div>
    </article>
  `;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  message.textContent = "Creating incident...";

  const payload = Object.fromEntries(new FormData(form).entries());
  const response = await fetch("/api/incidents", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  message.textContent = response.ok ? "Incident opened and worker notification queued." : "Unable to create incident.";
  await loadIncidents();
});

list.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-id]");
  if (!button) return;

  await fetch(`/api/incidents/${button.dataset.id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: button.dataset.status }),
  });
  await loadIncidents();
});

refresh.addEventListener("click", loadIncidents);

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

loadIncidents();
