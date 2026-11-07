"use client";

import { useMemo, useState } from "react";
import "./facilities.css";

export type HubType = "dropoff" | "repair" | "donate" | "recycle";

export type Hub = {
  id: string;
  name: string;
  area: string;
  address: string;
  type: HubType;
  hours: string;
  accepts: string[];
  phone?: string;
  distanceKm?: number;
};

export type FacilitiesViewProps = {
  hubs?: Hub[];
};

const TYPE_META: Record<HubType, { label: string }> = {
  dropoff: { label: "Drop-off" },
  repair: { label: "Repair" },
  donate: { label: "Donate" },
  recycle: { label: "Recycle" },
};

const FILTERS: { value: HubType | "all"; label: string }[] = [
  { value: "all", label: "All" },
  { value: "dropoff", label: "Drop-off" },
  { value: "repair", label: "Repair" },
  { value: "donate", label: "Donate" },
  { value: "recycle", label: "Recycle" },
];

// Sample data only. Replace with real hubs via the `hubs` prop.
const SAMPLE_HUBS: Hub[] = [
  {
    id: "h1",
    name: "Sample Textile Drop-off",
    area: "Kothrud",
    address: "Sample address, Kothrud, Pune",
    type: "dropoff",
    hours: "Mon–Sat, 10:00–18:00",
    accepts: ["Clothing", "Bed linen", "Shoes"],
    phone: "+91 00000 00000",
    distanceKm: 2.4,
  },
  {
    id: "h2",
    name: "Sample Repair Studio",
    area: "Deccan",
    address: "Sample address, Deccan, Pune",
    type: "repair",
    hours: "Tue–Sun, 11:00–19:00",
    accepts: ["Seam repair", "Buttons", "Zips", "Hemming"],
    distanceKm: 4.1,
  },
  {
    id: "h3",
    name: "Sample Community Donation Centre",
    area: "Aundh",
    address: "Sample address, Aundh, Pune",
    type: "donate",
    hours: "Daily, 09:00–17:00",
    accepts: ["Wearable clothing", "Blankets"],
    phone: "+91 00000 00001",
    distanceKm: 6.8,
  },
  {
    id: "h4",
    name: "Sample Fibre Recycling Point",
    area: "Hadapsar",
    address: "Sample address, Hadapsar, Pune",
    type: "recycle",
    hours: "Mon–Fri, 10:00–16:00",
    accepts: ["Worn-out fabric", "Mixed textiles"],
    distanceKm: 9.2,
  },
];

export function FacilitiesView({ hubs = SAMPLE_HUBS }: FacilitiesViewProps) {
  const [filter, setFilter] = useState<HubType | "all">("all");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return hubs.filter((h) => {
      if (filter !== "all" && h.type !== filter) return false;
      if (!q) return true;
      return (
        h.name.toLowerCase().includes(q) ||
        h.area.toLowerCase().includes(q) ||
        h.accepts.some((a) => a.toLowerCase().includes(q))
      );
    });
  }, [hubs, filter, query]);

  const selected = filtered.find((h) => h.id === selectedId) ?? filtered[0] ?? null;

  const countFor = (value: HubType | "all") =>
    value === "all" ? hubs.length : hubs.filter((h) => h.type === value).length;

  const resetFilters = () => {
    setFilter("all");
    setQuery("");
  };

  return (
    <section className="fh" aria-labelledby="fh-title">
      <header className="fh-header">
        <p className="fh-eyebrow">
          <span className="fh-eyebrowRule" aria-hidden="true" />
          Pune network
        </p>
        <h2 id="fh-title" className="fh-title">
          Drop-off <em>hubs</em>
        </h2>
        <p className="fh-lead">
          Find where to drop, repair, donate or recycle your garments. Every hub lists what it accepts, so you
          know before you go.
        </p>
      </header>

      <div className="fh-toolbar">
        <label className="fh-search">
          <span className="fh-sr">Search hubs</span>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
          <input
            type="search"
            placeholder="Search by name, area or item"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>

        <div className="fh-filters" role="group" aria-label="Filter by service">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              className="fh-filter"
              aria-pressed={filter === f.value}
              onClick={() => setFilter(f.value)}
            >
              {f.label}
              <span className="fh-count">{countFor(f.value)}</span>
            </button>
          ))}
        </div>
      </div>

      {filtered.length === 0 ? (
        <div className="fh-empty">
          <p className="fh-emptyTitle">No hubs match your search</p>
          <p className="fh-emptyText">Try a different area or item, or clear the filters.</p>
          <button type="button" className="fh-btnGhost" onClick={resetFilters}>
            Clear filters
          </button>
        </div>
      ) : (
        <div className="fh-layout">
          <ul className="fh-list" role="list" aria-label="Hubs">
            {filtered.map((h) => {
              const active = selected?.id === h.id;
              return (
                <li key={h.id}>
                  <button
                    type="button"
                    className={`fh-item${active ? " fh-item--active" : ""}`}
                    aria-current={active ? "true" : undefined}
                    onClick={() => setSelectedId(h.id)}
                  >
                    <div className="fh-itemTop">
                      <span className={`fh-type fh-type--${h.type}`}>{TYPE_META[h.type].label}</span>
                      {h.distanceKm !== undefined && <span className="fh-distance">{h.distanceKm} km</span>}
                    </div>
                    <p className="fh-itemName">{h.name}</p>
                    <p className="fh-itemMeta">
                      {h.area} · {h.hours}
                    </p>
                  </button>
                </li>
              );
            })}
          </ul>

          {selected && (
            <article className="fh-detail" aria-live="polite">
              <div className="fh-detailTop">
                <span className={`fh-type fh-type--${selected.type}`}>{TYPE_META[selected.type].label}</span>
                {selected.distanceKm !== undefined && (
                  <span className="fh-distance">{selected.distanceKm} km away</span>
                )}
              </div>

              <h3 className="fh-detailName">{selected.name}</h3>
              <p className="fh-address">{selected.address}</p>

              <dl className="fh-facts">
                <div>
                  <dt>Hours</dt>
                  <dd>{selected.hours}</dd>
                </div>
                <div>
                  <dt>Area</dt>
                  <dd>{selected.area}</dd>
                </div>
              </dl>

              <p className="fh-sectionLabel">Accepts</p>
              <ul className="fh-chips" role="list">
                {selected.accepts.map((a) => (
                  <li key={a} className="fh-chip">
                    {a}
                  </li>
                ))}
              </ul>

              <div className="fh-actions">
                <a
                  className="fh-btnPrimary"
                  href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(selected.address)}`}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Get directions
                  <span aria-hidden="true">→</span>
                </a>
                {selected.phone && (
                  <a className="fh-btnGhost" href={`tel:${selected.phone.replace(/\s/g, "")}`}>
                    Call hub
                  </a>
                )}
              </div>
            </article>
          )}
        </div>
      )}
    </section>
  );
}

export default FacilitiesView;