import { useEffect, useState } from "react";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import { apiGet } from "./api";

type GISStation = {
  station_id: string;
  station_name?: string;
  latitude: number;
  longitude: number;
  district?: string;
  source?: string;
  [key: string]: unknown;
};
type GISResponse = { items: GISStation[]; count: number; data_note?: string };

function FitStations({ stations }: { stations: GISStation[] }) {
  const map = useMap();
  useEffect(() => {
    if (stations.length === 1) map.setView([stations[0].latitude, stations[0].longitude], 12);
    else if (stations.length > 1) {
      const L = (window as unknown as { L?: typeof import("leaflet") }).L;
      if (L) map.fitBounds(stations.map(s => [s.latitude, s.longitude] as [number, number]), { padding: [24, 24] });
    }
  }, [stations, map]);
  return null;
}

export default function GISNetwork() {
  const [items, setItems] = useState<GISStation[]>([]);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [note, setNote] = useState("");
  const [riskOnly, setRiskOnly] = useState(false);

  async function load() {
    setStatus("loading");
    try {
      const data = await apiGet<GISResponse>("/api/gis/stations");
      setItems(data.items || []);
      setNote(data.data_note || "");
      setStatus("ready");
    } catch (e) {
      setNote(e instanceof Error ? e.message : "GIS API unavailable");
      setStatus("error");
    }
  }
  useEffect(() => { void load(); }, []);
  const shown = items.filter(s => !riskOnly || Number(s.utilization ?? s.util ?? 0) >= 1);
  return <section className="gis-section">
    <div className="gis-head">
      <div><div className="eyebrow">GEOSPATIAL ANALYSIS</div><h2>Station network map</h2>
      <p>Source-backed coordinates only · straight-line proximity diagnostics</p></div>
      <label className="gis-toggle"><input type="checkbox" checked={riskOnly} onChange={e => setRiskOnly(e.target.checked)} /> Risk flagged only</label>
    </div>
    <div className="gis-map-wrap">
      <MapContainer center={[22.5, 72.9]} zoom={7} scrollWheelZoom className="gis-map">
        <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <FitStations stations={shown} />
        {shown.map(s => <CircleMarker key={s.station_id} center={[s.latitude, s.longitude]} radius={7}
          pathOptions={{ color: "#0f766e", fillColor: "#14b8a6", fillOpacity: 0.8 }}>
          <Popup><b>{s.station_name || s.station_id}</b><br />ID: {s.station_id}<br />{s.district || "District not supplied"}<br />Coordinates: {s.latitude}, {s.longitude}</Popup>
        </CircleMarker>)}
      </MapContainer>
      {status === "ready" && items.length === 0 && <div className="gis-empty"><b>No verified station coordinates loaded</b><span>Set CNG_STATIONS_CSV to a CSV with station_id, station_name, latitude and longitude.</span></div>}
      {status === "error" && <div className="gis-empty"><b>GIS API unavailable</b><span>{note} Start the backend and refresh.</span></div>}
    </div>
    <div className="gis-foot"><span>{status === "loading" ? "Loading stations…" : status === "error" ? "API unavailable" : shown.length + " station(s) shown"}</span><button className="secondary" onClick={() => void load()}>Refresh map</button></div>
    <p className="gis-disclaimer">{note} Nearby distance is a proximity diagnostic—not road travel time, demand catchment, or proof of station cannibalization. Risk filter becomes meaningful when a utilization field is supplied.</p>
  </section>;
}
