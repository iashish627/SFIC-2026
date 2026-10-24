/* Live API panel for the existing CNG dashboard. Values are explicitly labelled as estimates. */
(() => {
  const API = (window.CNG_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
  const main = document.querySelector('.main');
  if (!main) return;

  const panel = document.createElement('section');
  panel.className = 'card';
  panel.style.cssText = 'margin:1rem 1.5rem;padding:1rem;border:1px solid #cbd5e1;';
  panel.innerHTML = `
    <div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;align-items:center">
      <div><h2 style="font-size:1.05rem;margin:0 0 .25rem">Live Forecast API</h2>
      <p id="liveApiStatus" class="desc" style="margin:0">Connecting to local FastAPI…</p></div>
      <span class="badge">ESTIMATED DEMO · not observed sales</span>
    </div>
    <div style="display:flex;gap:.75rem;flex-wrap:wrap;margin-top:1rem;align-items:end">
      <label style="display:grid;gap:.35rem;font-size:.8rem">Station<select id="liveStation" style="min-width:220px"><option>Loading stations…</option></select></label>
      <label style="display:grid;gap:.35rem;font-size:.8rem">Baseline demand (kg/day)<input id="liveBase" type="number" min="1" value="1200" style="max-width:190px"></label>
      <label style="display:grid;gap:.35rem;font-size:.8rem">Days<input id="liveDays" type="number" min="1" max="30" value="14" style="max-width:100px"></label>
      <button id="liveGenerate" class="btn btn-primary" type="button">Generate forecast</button>
      <button id="liveShock" class="btn btn-ghost" type="button">Simulate +20% surge</button>
    </div>
    <p id="liveResultNote" class="desc" style="margin:.9rem 0 0">No forecast generated yet.</p>
    <div style="overflow:auto;margin-top:.75rem"><table style="width:100%;border-collapse:collapse;font-size:.82rem"><thead><tr><th style="text-align:left;padding:.5rem">Date</th><th style="text-align:left;padding:.5rem">Demand (kg/day)</th><th style="text-align:left;padding:.5rem">Type</th></tr></thead><tbody id="liveRows"><tr><td colspan="3" style="padding:.5rem">Load stations to begin.</td></tr></tbody></table></div>
  `;
  const topbar = main.querySelector('.topbar');
  if (topbar) topbar.insertAdjacentElement('afterend', panel);
  else main.prepend(panel);

  const status = panel.querySelector('#liveApiStatus');
  const stationSelect = panel.querySelector('#liveStation');
  const resultNote = panel.querySelector('#liveResultNote');
  const rows = panel.querySelector('#liveRows');
  const btnGenerate = panel.querySelector('#liveGenerate');
  const btnShock = panel.querySelector('#liveShock');
  let stations = [];

  async function loadStations() {
    try {
      const [health, response] = await Promise.all([
        fetch(API + '/health'),
        fetch(API + '/api/v1/forecast/stations')
      ]);
      if (!health.ok || !response.ok) throw new Error('API returned ' + response.status);
      const data = await response.json();
      stations = data.stations || [];
      stationSelect.innerHTML = '';
      stations.forEach(s => {
        const option = document.createElement('option');
        option.value = s.station_id;
        option.textContent = s.station_name + ' (' + s.station_id + ')';
        stationSelect.appendChild(option);
      });
      status.textContent = 'API connected · ' + stations.length + ' station record(s) loaded.';
      if (!stations.length) status.textContent += ' Add station rows to the CSV.';
    } catch (err) {
      status.textContent = 'API unavailable: ' + err.message + '. Keep FastAPI running on port 8000 and check CORS.';
      stationSelect.innerHTML = '<option value="">Stations unavailable</option>';
    }
  }

  function showRows(items, kind) {
    rows.innerHTML = '';
    items.slice(0, 30).forEach(item => {
      const tr = document.createElement('tr');
      [item.date, Number(item.predicted_demand_kg ?? item.scenario_demand_kg).toLocaleString(), kind].forEach(value => {
        const td = document.createElement('td');
        td.style.cssText = 'padding:.5rem;border-top:1px solid #e2e8f0';
        td.textContent = value;
        tr.appendChild(td);
      });
      rows.appendChild(tr);
    });
    resultNote.textContent = items.length + ' day(s) returned. ' + (kind === 'Estimated demand' ? 'Assumption-based estimate; not calibrated to actual sales.' : 'Hypothetical scenario, not an observed demand change.');
  }

  async function generate() {
    const stationId = stationSelect.value;
    const base = Number(panel.querySelector('#liveBase').value);
    const days = Number(panel.querySelector('#liveDays').value);
    if (!stationId || !(base > 0) || !Number.isInteger(days) || days < 1 || days > 30) {
      resultNote.textContent = 'Choose a station, enter a positive baseline, and set days from 1 to 30.';
      return;
    }
    btnGenerate.disabled = btnShock.disabled = true;
    try {
      const response = await fetch(API + '/api/v1/forecast/generate', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({station_ids:[stationId], start_date:new Date().toLocaleDateString('en-CA'), days, mode:'estimated', base_demand_kg:base})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail?.message || data.detail || 'Forecast request failed');
      showRows(data.forecast_data || [], 'Estimated demand');
    } catch (err) {
      resultNote.textContent = 'Forecast failed: ' + err.message;
    } finally {
      btnGenerate.disabled = btnShock.disabled = false;
    }
  }

  async function shock() {
    const stationId = stationSelect.value;
    const base = Number(panel.querySelector('#liveBase').value);
    if (!stationId || !(base > 0)) { resultNote.textContent = 'Choose a station and enter a positive baseline.'; return; }
    btnGenerate.disabled = btnShock.disabled = true;
    try {
      const start = new Date();
      const end = new Date(start);
      end.setDate(end.getDate() + 6);
      const iso = d => d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
      const response = await fetch(API + '/api/v1/forecast/scenario/demand-shock', {
        method: 'POST', headers: {'Content-Type':'application/json'},
        body: JSON.stringify({station_ids:[stationId], start_date:iso(start), end_date:iso(end), uplift_percentage:20, base_demand_kg:base})
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail?.message || data.detail || 'Scenario request failed');
      showRows((data.scenario_data || []).map(x => ({...x, predicted_demand_kg:x.scenario_demand_kg, date:x.date})), 'Hypothetical +20% surge');
    } catch (err) {
      resultNote.textContent = 'Scenario failed: ' + err.message;
    } finally {
      btnGenerate.disabled = btnShock.disabled = false;
    }
  }
  btnGenerate.addEventListener('click', generate);
  btnShock.addEventListener('click', shock);
  loadStations();
})();