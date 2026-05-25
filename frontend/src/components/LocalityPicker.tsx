'use client'

import { useState, useEffect } from 'react'
import { ChevronDown, Check, X, Zap, MapPin } from 'lucide-react'

interface Locality { name: string; query: string }
interface Region { region: string; localities: Locality[] }
interface CityData { city: string; regions: Region[]; total_localities: number }

interface Props {
  city: string
  onCityChange: (city: string) => void
  selectedLocalities: string[]
  onLocalitiesChange: (locs: string[]) => void
  disabled?: boolean
}

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
const CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai', 'Pune']

export default function LocalityPicker({ city, onCityChange, selectedLocalities, onLocalitiesChange, disabled }: Props) {
  const [cityData, setCityData] = useState<CityData | null>(null)
  const [open, setOpen] = useState(false)
  const [activeRegion, setActiveRegion] = useState<string | null>(null)

  useEffect(() => {
    if (!city) return
    fetch(`${API}/api/cities/${city}/localities`)
      .then(r => r.json())
      .then(data => {
        setCityData(data)
        setActiveRegion(data.regions?.[0]?.region || null)
        onLocalitiesChange([])   // Reset when city changes
      })
      .catch(() => setCityData(null))
  }, [city])

  const toggleLocality = (name: string) => {
    if (selectedLocalities.includes(name))
      onLocalitiesChange(selectedLocalities.filter(l => l !== name))
    else
      onLocalitiesChange([...selectedLocalities, name])
  }

  const selectAllInRegion = (region: Region) => {
    const names = region.localities.map(l => l.name)
    const allSelected = names.every(n => selectedLocalities.includes(n))
    if (allSelected) {
      onLocalitiesChange(selectedLocalities.filter(l => !names.includes(l)))
    } else {
      const merged = [...new Set([...selectedLocalities, ...names])]
      onLocalitiesChange(merged)
    }
  }

  const selectAll = () => {
    if (!cityData) return
    const all = cityData.regions.flatMap(r => r.localities.map(l => l.name))
    onLocalitiesChange(all)
  }

  const clearAll = () => onLocalitiesChange([])

  const removeChip = (name: string) => onLocalitiesChange(selectedLocalities.filter(l => l !== name))

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* City selector */}
      <div>
        <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
          City
        </label>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {CITIES.map(c => (
            <button
              key={c}
              type="button"
              onClick={() => { onCityChange(c); setOpen(true); }}
              disabled={disabled}
              style={{
                padding: '6px 14px', borderRadius: 8, fontSize: '0.82rem', fontWeight: 600,
                cursor: 'pointer', border: '1px solid',
                background: city === c ? 'rgba(99,102,241,0.2)' : 'transparent',
                borderColor: city === c ? 'var(--accent)' : 'var(--border)',
                color: city === c ? 'var(--accent)' : 'var(--text-secondary)',
                transition: 'all 0.15s',
              }}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      {/* Locality picker — only shows when a supported city is selected */}
      {city && cityData && (
        <div>
          <label style={{ display: 'block', fontSize: '0.78rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Localities <span style={{ color: 'var(--accent)' }}>{selectedLocalities.length > 0 && `(${selectedLocalities.length} selected)`}</span>
          </label>

          {/* Action buttons */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <button type="button" onClick={selectAll} disabled={disabled}
              style={{
                padding: '5px 12px', borderRadius: 7, fontSize: '0.78rem', fontWeight: 600,
                cursor: 'pointer', border: '1px solid var(--accent)',
                background: 'rgba(99,102,241,0.15)', color: 'var(--accent)',
                display: 'flex', alignItems: 'center', gap: 5,
              }}>
              <Zap size={12} /> Select All ({cityData.total_localities})
            </button>
            {selectedLocalities.length > 0 && (
              <button type="button" onClick={clearAll} disabled={disabled}
                style={{
                  padding: '5px 12px', borderRadius: 7, fontSize: '0.78rem', fontWeight: 600,
                  cursor: 'pointer', border: '1px solid var(--border)',
                  background: 'transparent', color: 'var(--text-muted)',
                }}>
                Clear
              </button>
            )}
          </div>

          {/* Selected chips */}
          {selectedLocalities.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5, marginBottom: 8, maxHeight: 80, overflowY: 'auto' }}>
              {selectedLocalities.map(name => (
                <span key={name} style={{
                  display: 'inline-flex', alignItems: 'center', gap: 3,
                  background: 'rgba(99,102,241,0.12)', color: 'var(--accent)',
                  border: '1px solid rgba(99,102,241,0.25)',
                  borderRadius: 20, padding: '2px 8px', fontSize: '0.72rem', fontWeight: 600,
                }}>
                  <MapPin size={10} /> {name}
                  <button onClick={() => removeChip(name)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--accent)', padding: 0, display: 'flex' }}>
                    <X size={10} />
                  </button>
                </span>
              ))}
            </div>
          )}

          {/* Region tabs + locality grid */}
          <div className="card" style={{ borderRadius: 10, overflow: 'hidden' }}>
            {/* Region tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid var(--border)', overflowX: 'auto' }}>
              {cityData.regions.map(r => {
                const regionSelected = r.localities.filter(l => selectedLocalities.includes(l.name)).length
                return (
                  <button
                    key={r.region}
                    type="button"
                    onClick={() => setActiveRegion(r.region)}
                    style={{
                      padding: '8px 14px', fontSize: '0.78rem', fontWeight: 600,
                      whiteSpace: 'nowrap', cursor: 'pointer', border: 'none',
                      background: activeRegion === r.region ? 'rgba(99,102,241,0.1)' : 'transparent',
                      color: activeRegion === r.region ? 'var(--accent)' : 'var(--text-muted)',
                      borderBottom: activeRegion === r.region ? '2px solid var(--accent)' : '2px solid transparent',
                      transition: 'all 0.15s',
                    }}
                  >
                    {r.region}
                    {regionSelected > 0 && (
                      <span style={{ marginLeft: 5, background: 'var(--accent)', borderRadius: 10, padding: '1px 5px', fontSize: '0.65rem', color: 'white' }}>
                        {regionSelected}
                      </span>
                    )}
                  </button>
                )
              })}
            </div>

            {/* Localities grid */}
            {cityData.regions.filter(r => r.region === activeRegion).map(r => (
              <div key={r.region} style={{ padding: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 8 }}>
                  <button type="button" onClick={() => selectAllInRegion(r)}
                    style={{ background: 'none', border: 'none', color: 'var(--accent)', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 600 }}>
                    {r.localities.every(l => selectedLocalities.includes(l.name)) ? 'Deselect all' : 'Select all in region'}
                  </button>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 6 }}>
                  {r.localities.map(loc => {
                    const sel = selectedLocalities.includes(loc.name)
                    return (
                      <button
                        key={loc.name}
                        type="button"
                        onClick={() => toggleLocality(loc.name)}
                        disabled={disabled}
                        style={{
                          padding: '6px 10px', borderRadius: 7, fontSize: '0.78rem', fontWeight: 600,
                          cursor: 'pointer', border: '1px solid',
                          background: sel ? 'rgba(99,102,241,0.18)' : 'rgba(255,255,255,0.02)',
                          borderColor: sel ? 'var(--accent)' : 'var(--border)',
                          color: sel ? 'var(--accent)' : 'var(--text-secondary)',
                          textAlign: 'left', transition: 'all 0.12s',
                          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                        }}
                      >
                        {loc.name}
                        {sel && <Check size={11} />}
                      </button>
                    )
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
