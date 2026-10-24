import { useMemo, useState } from "react";
import { MapPin } from "lucide-react";
import { Circle, CircleMarker, MapContainer, TileLayer, Tooltip, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";

type Station = { station_id: string; station_name: string; latitude?: number|string; longitude?: number|string; lat?: number|string; lon?: number|string; lng?: number|string; [key:string]: unknown };
type Props = { stations: Station[] };

function coords(s: Station): [number,number] | null {
 const lat=Number(s.latitude ?? s.lat), lon=Number(s.longitude ?? s.lon ?? s.lng);
 return Number.isFinite(lat)&&Number.isFinite(lon)&&Math.abs(lat)<=90&&Math.abs(lon)<=180 ? [lat,lon] : null;
}
function distanceKm(a:[number,number],b:[number,number]) {
 const rad=(v:number)=>v*Math.PI/180, dLat=rad(b[0]-a[0]),dLon=rad(b[1]-a[1]);
 const h=Math.sin(dLat/2)**2+Math.cos(rad(a[0]))*Math.cos(rad(b[0]))*Math.sin(dLon/2)**2;
 return 6371*2*Math.asin(Math.sqrt(h));
}
function CandidatePicker({onPick}:{onPick:(p:[number,number])=>void}) {
 useMapEvents({click(e){onPick([e.latlng.lat,e.latlng.lng]);}});
 return null;
}
export default function NetworkPlanning({stations}:Props) {
 const mapped=useMemo(()=>stations.map(s=>({station:s,point:coords(s)})).filter((x):x is {station:Station;point:[number,number]}=>x.point!==null),[stations]);
 const [candidate,setCandidate]=useState<[number,number]>([21.17,72.83]);
 const [baseline,setBaseline]=useState("1200");
 const [capacity,setCapacity]=useState("1500");
 const [expansion,setExpansion]=useState("500");
 const [newCapacity,setNewCapacity]=useState("1000");
 const [cannibal,setCannibal]=useState("25");
 const [radius,setRadius]=useState("5");
 const nearest=useMemo(()=>mapped.map(x=>({...x,distance:distanceKm(candidate,x.point)})).sort((a,b)=>a.distance-b.distance),[mapped,candidate]);
 const nearby=nearest.filter(x=>x.distance<=Number(radius));
 const demand=Math.max(0,Number(baseline)||0), cap=Math.max(0,Number(capacity)||0), addCap=Math.max(0,Number(expansion)||0), newCap=Math.max(0,Number(newCapacity)||0), diverted=Math.min(demand,newCap*Math.max(0,Math.min(100,Number(cannibal)||0))/100);
 const options=[
  {name:"A · No change",capacity:cap,incremental:0,description:"Keep current station capacity unchanged."},
  {name:"B · Expand existing",capacity:cap+addCap,incremental:Math.min(demand,cap+addCap)-Math.min(demand,cap),description:"Increase existing station capacity by the assumed amount."},
  {name:"C · Build new station",capacity:cap+newCap,incremental:Math.max(0,Math.min(demand,cap+newCap)-Math.min(demand,cap)-diverted),description:"New station potential less assumed demand diverted from nearby stations."}
 ];
 return <section className="planning-wrap">
  <div className="section-heading"><div><div className="eyebrow">GEOSPATIAL + INVESTMENT OPTIONS</div><h2>Network planning lab</h2></div><span className="tag purple">ASSUMPTION-BASED</span></div>
  <p className="planning-intro">Explore mapped station coordinates and compare three choices against one shared demand baseline. Results are planning illustrations, not verified site recommendations.</p>
  <div className="planning-grid">
   <article className="panel map-panel"><div className="panel-heading"><div><h3>Station coverage map</h3><p>Click the map to move the candidate site marker.</p></div><span className="tag">{mapped.length} MAPPED</span></div>
    {mapped.length ? <MapContainer center={candidate} zoom={10} scrollWheelZoom className="network-map"><TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"/><CandidatePicker onPick={setCandidate}/><Circle center={candidate} radius={Number(radius)*1000} pathOptions={{color:"#b28aff",fillOpacity:.08}}/><CircleMarker center={candidate} radius={8} pathOptions={{color:"#b28aff",fillColor:"#b28aff",fillOpacity:1}}><Tooltip>Candidate site</Tooltip></CircleMarker>{mapped.map(({station,point})=><CircleMarker key={station.station_id} center={point} radius={5} pathOptions={{color:"#50d6a7",fillColor:"#50d6a7",fillOpacity:.9}}><Tooltip>{station.station_name} · {station.station_id}</Tooltip></CircleMarker>)}</MapContainer> : <div className="map-empty"><MapPin size={26}/><b>No usable station coordinates found</b><p>Station CSV needs latitude/longitude (or lat/lon) columns for map markers. Other fields are not guessed.</p></div>}
    <div className="coords-row"><span>Candidate coordinates</span><b>{candidate[0].toFixed(4)}, {candidate[1].toFixed(4)}</b></div>
    <div className="input-grid"><label>Coverage radius (km)<input type="number" min="1" max="100" value={radius} onChange={e=>setRadius(e.target.value)}/></label><label>Nearby stations<input value={mapped.length?String(nearby.length):"No coordinates"} readOnly/></label></div>
    <div className="nearby-list">{nearby.slice(0,5).map(x=><div key={x.station.station_id}><span>{x.station.station_name}</span><b>{x.distance.toFixed(1)} km</b></div>)}{mapped.length>0&&!nearby.length&&<p>No mapped station within the selected radius.</p>}</div>
   </article>
   <article className="panel"><div className="panel-heading"><div><h3>Compare A / B / C</h3><p>Same assumed demand baseline for each option.</p></div><span className="tag">SIMULATOR</span></div>
    <label>Demand baseline (kg/day)<input type="number" min="0" value={baseline} onChange={e=>setBaseline(e.target.value)}/></label>
    <label>Current station capacity (kg/day)<input type="number" min="0" value={capacity} onChange={e=>setCapacity(e.target.value)}/></label>
    <label>Additional capacity if expanded (kg/day)<input type="number" min="0" value={expansion} onChange={e=>setExpansion(e.target.value)}/></label>
    <label>New station capacity (kg/day)<input type="number" min="0" value={newCapacity} onChange={e=>setNewCapacity(e.target.value)}/></label>
    <label>Assumed cannibalization from new station (%)<input type="number" min="0" max="100" value={cannibal} onChange={e=>setCannibal(e.target.value)}/></label>
    <div className="scenario-cards">{options.map(o=><div className="scenario-card" key={o.name}><div><b>{o.name}</b><span>{o.description}</span></div><div className="scenario-stats"><span>Available capacity<strong>{o.capacity.toLocaleString()} kg/day</strong></span><span>Potential incremental served demand<strong>{o.incremental.toLocaleString(undefined,{maximumFractionDigits:1})} kg/day</strong></span></div></div>)}</div>
    <p className="assumption">Simplified capacity arithmetic only. No station-level actual sales, costs, travel-time routing, demand allocation or validated cannibalization model is available in this prototype.</p>
   </article>
  </div>
 </section>;
}
