import { useEffect, useMemo, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip, useMap } from "react-leaflet";
import * as L from "leaflet";
import "leaflet/dist/leaflet.css";
import { apiGet } from "./api";

type GISStation = {
  station_id: string; station_name?: string; latitude: number; longitude: number;
  district?: string; state?: string; source?: string; source_url?: string;
  data_confidence?: string; verified_gujarat_gas_station?: boolean;
  has_cng?: string; source_status?: string; [key: string]: unknown;
};
type GISResponse = { items: GISStation[]; count: number; data_note?: string };

function FitStations({ stations }: { stations: GISStation[] }) {
  const map = useMap();
  useEffect(() => {
    if (stations.length === 1) map.setView([stations[0].latitude, stations[0].longitude], 12);
    else if (stations.length > 1) map.fitBounds(L.latLngBounds(stations.map(s => [s.latitude, s.longitude] as [number, number])), { padding: [24, 24] });
  }, [stations, map]);
  return null;
}

function stationIsCng(s: GISStation) {
  return String(s.has_cng ?? "").toLowerCase() === "true";
}

export default function GISNetwork() {
  const [items, setItems] = useState<GISStation[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [note, setNote] = useState("");
  const [riskOnly, setRiskOnly] = useState(false);
  const [verifiedOnly, setVerifiedOnly] = useState(false);

  async function load() {
    setStatus("loading");
    try {
      const data = await apiGet<GISResponse>("/api/gis/stations");
      setItems(data.items || []); setNote(data.data_note || ""); setStatus("ready");
    } catch (e) {
      setNote(e instanceof Error ? e.message : "GIS API unavailable"); setStatus("error");
    }
  }
  useEffect(() => { void load(); }, []);
  const shown = useMemo(() => items.filter(s =>
    (!riskOnly || Number(s.utilization ?? s.util ?? 0) >= 1) &&
    (!verifiedOnly || s.verified_gujarat_gas_station === true)
  ), [items, riskOnly, verifiedOnly]);
  const provisionalCount = items.filter(s => s.verified_gujarat_gas_station !== true).length;

  return <section className="gis-section">
    <div className="gis-head"><div><div className="eyebrow">GEOSPATIAL ANALYSIS</div><h2>Station network map</h2>
      <p>Coordinate-backed outlets · proximity diagnostics</p></div>
      <div className="gis-filters">
        <label className="gis-toggle"><input type="checkbox" checked={verifiedOnly} onChange={e => setVerifiedOnly(e.target.checked)} /> Verified operator stations only</label>
        <label className="gis-toggle"><input type="checkbox" checked={riskOnly} onChange={e => setRiskOnly(e.target.checked)} /> Risk flagged only</label>
      </div>
    </div>
    {provisionalCount > 0 && <div className="gis-data-warning"><b>Provisional public outlet data</b><span>{provisionalCount} record(s) are not verified as operating Gujarat Gas CNG stations. They are candidate locations only, not company-confirmed stations.</span></div>}
    <div className="gis-map-wrap">
      <MapContainer center={[22.5, 72.9]} zoom={7} scrollWheelZoom className="gis-map">
        <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <FitStations stations={shown} />
        {shown.map(s => <CircleMarker key={s.station_id} center={[s.latitude, s.longitude]} radius={s.verified_gujarat_gas_station ? 7 : 5}
          pathOptions={s.verified_gujarat_gas_station ? { color: "#0f766e", fillColor: "#14b8a6", fillOpacity: 0.9 } : { color: "#b7791f", fillColor: "#f6ad55", fillOpacity: 0.75, dashArray: "3 3" }}>
          <Tooltip>{s.station_name || s.station_id}{s.verified_gujarat_gas_station ? " · verified" : " · provisional candidate"}</Tooltip>
          <Popup><b>{s.station_name || s.station_id}</b><br />ID: {s.station_id}<br />{s.district || "District not supplied"}, {s.state || "state not supplied"}<br />Coordinates: {s.latitude}, {s.longitude}<br />CNG flag in source: {stationIsCng(s) ? "yes" : "not confirmed"}<br />Verification: {s.verified_gujarat_gas_station ? "operator verified" : "not verified as Gujarat Gas station"}<br />Source: {s.source || "not supplied"}{s.source_url ? <><br /><a href={s.source_url} target="_blank" rel="noreferrer">Open source</a></> : null}</Popup>
        </CircleMarker>)}
      </MapContainer>
      {status === "ready" && items.length === 0 && <div className="gis-empty"><b>No station/outlet coordinates loaded</b><span>Run the public outlet import script or set CNG_STATIONS_CSV to a compatible CSV. Imported public records remain provisional until verified.</span></div>}
      {status === "error" && <div className="gis-empty"><b>GIS API unavailable</b><span>{note} Start the backend and refresh.</span></div>}
    </div>
    <div className="gis-foot"><span>{status === "loading" ? "Loading map data…" : status === "error" ? "API unavailable" : shown.length + " record(s) shown · " + items.length + " total with coordinates"}</span><button className="secondary" onClick={() => void load()}>Refresh map</button></div>
    <p className="gis-disclaimer">{note} Map source: OpenStreetMap. Nearby distance is a straight-line proximity diagnostic—not road travel time, demand catchment, or proof of cannibalization. Public CNG flags do not prove current operation or supply by Gujarat Gas.</p>
  </section>;
}
