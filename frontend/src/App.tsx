import { useEffect, useMemo, useState } from "react";
import { Activity, Fuel, MapPin, RefreshCw, Zap, AlertTriangle, ArrowUpRight, Play, Server } from "lucide-react";
import { apiGet, apiPost } from "./api";
import NetworkPlanning from "./NetworkPlanning";
type Station = { station_id: string; station_name: string; [key: string]: unknown };
type StationsResponse = { success?: boolean; total_count?: number; stations?: Station[] };
type ForecastRow = { station_id: string; date: string; predicted_demand_kg?: number; baseline_demand_kg?: number; scenario_demand_kg?: number; data_type?: string; model?: string; unit?: string };
type ForecastResponse = { success?: boolean; mode?: string; forecast_data?: ForecastRow[]; scenario_data?: ForecastRow[]; metadata?: Record<string, unknown> };
const today = () => new Date().toISOString().slice(0, 10);
const endAfter = (start: string, n: number) => { const d = new Date(`${start}T12:00:00`); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };
export default function App() {
 const [health,setHealth] = useState<"checking"|"online"|"offline">("checking");
 const [stations,setStations] = useState<Station[]>([]);
 const [stationError,setStationError] = useState("");
 const [stationId,setStationId] = useState("");
 const [startDate,setStartDate] = useState(today());
 const [baseDemand,setBaseDemand] = useState("1200");
 const [uplift,setUplift] = useState("20");
 const [days,setDays] = useState("30");
 const [forecast,setForecast] = useState<ForecastResponse|null>(null);
 const [busy,setBusy] = useState(false);
 const [error,setError] = useState("");
 const [shock,setShock] = useState<ForecastResponse|null>(null);
 const selectedIds = useMemo(()=>stationId ? [stationId] : [],[stationId]);
 async function load(){setHealth("checking");setStationError("");try{await apiGet("/health");setHealth("online");}catch{setHealth("offline");}try{const result=await apiGet<StationsResponse>("/api/v1/forecast/stations");setStations(result.stations||[]);if(result.stations?.length)setStationId(old=>old||result.stations![0].station_id);}catch(e){setStationError(e instanceof Error?e.message:"Could not load station list");}}
 useEffect(()=>{void load();},[]);
 async function generate(){setBusy(true);setError("");setForecast(null);try{if(!selectedIds.length)throw new Error("Load station data and select a station first.");setForecast(await apiPost<ForecastResponse>("/api/v1/forecast/generate",{station_ids:selectedIds,start_date:startDate,days:Number(days),mode:"estimated",base_demand_kg:Number(baseDemand)}));}catch(e){setError(e instanceof Error?e.message:"Forecast request failed");}finally{setBusy(false);}}
 async function runShock(){setBusy(true);setError("");setShock(null);try{if(!selectedIds.length)throw new Error("Load station data and select a station first.");setShock(await apiPost<ForecastResponse>("/api/v1/forecast/scenario/demand-shock",{station_ids:selectedIds,start_date:startDate,end_date:endAfter(startDate,Number(days)-1),uplift_percentage:Number(uplift),base_demand_kg:Number(baseDemand)}));}catch(e){setError(e instanceof Error?e.message:"Scenario request failed");}finally{setBusy(false);}}
 const count=stations.length;
 return <main className="shell">
  <aside className="sidebar"><div className="brand"><div className="brand-icon"><Fuel size={22}/></div><div><b>CNG INTELLIGENCE</b><small>NETWORK CONTROL</small></div></div><div className="nav-label">WORKSPACE</div><div className="nav-item active"><Activity size={17}/> Overview</div><div className="nav-item"><MapPin size={17}/> Station network</div><div className="nav-item"><Zap size={17}/> Demand forecast</div><div className="sidebar-bottom"><span className={health==="online"?"dot":"dot dim"}/><span>Forecast API</span><b className="api-state">{health}</b></div></aside>
  <section className="content"><header><div><div className="eyebrow">GUJARAT GAS · SFIC 2026</div><h1>Network intelligence</h1><p className="sub">Station-level demand signals and decision support.</p></div><div className="status-pill"><span className={health==="online"?"dot":"dot dim"}/>{health==="online"?"API connected":health==="checking"?"Connecting…":"API offline"}</div></header>
  {health==="offline"&&<div className="notice"><AlertTriangle size={18}/><div><b>Backend not reachable</b><p>Start the FastAPI service on port 8000. Set VITE_API_BASE_URL in frontend/.env if needed.</p></div></div>}
  <div className="metrics"><article className="metric"><div className="metric-top"><span>Station records</span><MapPin size={17}/></div><strong>{count||"—"}</strong><small>{stationError?"Station endpoint unavailable":"Configured station CSV"}</small></article><article className="metric"><div className="metric-top"><span>Forecast horizon</span><strong>{days} <em>days</em></strong></div><small>Choose 1–30 days below</small></article><article className="metric"><div className="metric-top"><span>Data mode</span><Fuel size={17}/></div><strong className="mode">Estimated</strong><small>Not calibrated to actual sales</small></article><article className="metric"><div className="metric-top"><span>API status</span><Server size={17}/></div><strong className="mode">{health==="online"?"Online":health==="checking"?"Checking":"Offline"}</strong><small>FastAPI health check</small></article></div>
  <div className="section-heading"><div><div className="eyebrow">FORECAST WORKBENCH</div><h2>Demand forecast</h2></div><button className="secondary" onClick={()=>void load()}><RefreshCw size={15}/> Refresh data</button></div>
  <div className="work-grid"><article className="panel"><div className="panel-heading"><div><h3>Generate baseline</h3><p>Forecast demand for one configured station.</p></div><span className="tag">BASELINE</span></div>
  <label>Station<select value={stationId} onChange={e=>setStationId(e.target.value)}><option value="">Select a station</option>{stations.map(s=><option key={s.station_id} value={s.station_id}>{s.station_name} ({s.station_id})</option>)}</select></label>
  <div className="input-grid"><label>Start date<input type="date" value={startDate} onChange={e=>setStartDate(e.target.value)}/></label><label>Forecast days<input type="number" min="1" max="30" value={days} onChange={e=>setDays(e.target.value)}/></label></div>
  <label>Assumed baseline demand (kg/day)<input type="number" min="1" value={baseDemand} onChange={e=>setBaseDemand(e.target.value)}/></label><div className="assumption">Assumption only; this is not observed Gujarat Gas sales data.</div>
  <button className="primary" disabled={busy||health!=="online"||!stationId||Number(baseDemand)<=0||Number(days)<1||Number(days)>30||!startDate} onClick={generate}><Play size={16} fill="currentColor"/>{busy?"Working…":"Generate forecast"}<ArrowUpRight size={16}/></button>{forecast&&<Result title="Forecast response" rows={forecast.forecast_data||[]} metadata={forecast.metadata}/>}</article>
  <article className="panel"><div className="panel-heading"><div><h3>Demand shock simulator</h3><p>Compare baseline with a hypothetical uplift.</p></div><span className="tag purple">WHAT-IF</span></div><label>Demand uplift (%)<input type="number" min="0" max="1000" value={uplift} onChange={e=>setUplift(e.target.value)}/></label><div className="assumption">Try a hypothetical festival or holiday uplift. The percentage is an assumption.</div><button className="primary purple-btn" disabled={busy||health!=="online"||!stationId||Number(baseDemand)<=0||Number(uplift)<0||Number(uplift)>1000} onClick={runShock}><Zap size={16}/>{busy?"Working…":"Run demand shock"}<ArrowUpRight size={16}/></button>{shock&&<Result title="Scenario response" rows={shock.scenario_data||[]} metadata={shock.metadata}/>}</article></div>
  {stationError&&<div className="error"><AlertTriangle size={17}/><span>{stationError}</span></div>}{error&&<div className="error"><AlertTriangle size={17}/><span>{error}</span></div>}
  <div className="section-heading"><div><div className="eyebrow">DATA TRANSPARENCY</div><h2>Station data status</h2></div></div><article className="panel data-panel"><div className="data-icon"><MapPin size={19}/></div><div><h3>Station master</h3><p>{stationError?stationError:count?count+" station record(s) loaded from the API.":"Waiting for station endpoint."} Historical forecasting requires a genuine sales CSV. Estimated outputs are assumption-based, not actual demand.</p></div><span className={stationError?"tag warn":"tag"}>{stationError?"NOT LOADED":count?"LOADED":"NO DATA"}</span></article>
  <NetworkPlanning stations={stations}/>
  <footer>Prototype for SFIC 2026 · Forecasts are estimates, not official operational guidance.</footer>
 </section></main>;
}
function Result({title,rows,metadata}:{title:string;rows:ForecastRow[];metadata?:Record<string,unknown>}){return <div className="result"><b>{title} · {rows.length} rows</b><pre>{JSON.stringify({sample:rows.slice(0,5),metadata},null,2)}</pre></div>}
