import 'leaflet/dist/leaflet.css'
import L from 'leaflet'
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet'
import { useEffect } from 'react'
import type { MapMarker, MapRoute, HeatmapData } from '@/types'
import { cn } from '@/lib/utils'

// Fix Leaflet default icon issue in bundlers (webpack/vite don't resolve marker image URLs)
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
})

// Inner component that calls useMap() — must be rendered inside MapContainer
function MapInvalidator() {
  const map = useMap()
  useEffect(() => {
    // Delay slightly to allow layout to settle after tab switch or initial render
    const timer = setTimeout(() => {
      map.invalidateSize()
    }, 100)
    return () => clearTimeout(timer)
  }, [map])
  return null
}

export interface GeoViewProps {
  center?: [number, number]
  zoom?: number
  markers?: MapMarker[]
  routes?: MapRoute[]
  heatmap?: HeatmapData
  onMarkerClick?: (marker: MapMarker) => void
  className?: string
}

export function GeoView({
  center = [39.8283, -98.5795],
  zoom = 4,
  markers = [],
  routes = [],
  // heatmap is accepted in the prop signature for future use but not rendered (no heatmap layer library loaded)
  heatmap: _heatmap,
  onMarkerClick,
  className,
}: GeoViewProps) {
  return (
    <div className={cn('h-[400px] rounded-lg overflow-hidden border border-border', className)}>
      <MapContainer
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        // Suppress React strict-mode double-init warning
        key={`${center[0]}-${center[1]}-${zoom}`}
      >
        {/* Dark theme tile layer via CartoCDN */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        />

        {/* Markers */}
        {markers.map((marker, idx) => {
          // Build a custom colored icon if a color is specified
          const icon = marker.color
            ? new L.DivIcon({
                html: `<div style="
                  width: 14px;
                  height: 14px;
                  background: ${marker.color};
                  border: 2px solid rgba(255,255,255,0.8);
                  border-radius: 50%;
                  box-shadow: 0 0 6px ${marker.color};
                "></div>`,
                className: '',
                iconSize: [14, 14],
                iconAnchor: [7, 7],
                popupAnchor: [0, -10],
              })
            : undefined

          return (
            <Marker
              key={idx}
              position={[marker.lat, marker.lng]}
              icon={icon}
              eventHandlers={
                onMarkerClick
                  ? {
                      click: () => onMarkerClick(marker),
                    }
                  : undefined
              }
            >
              {(marker.label || marker.popup) && (
                <Popup>
                  <span className="text-sm font-medium">{marker.popup ?? marker.label}</span>
                </Popup>
              )}
            </Marker>
          )
        })}

        {/* Routes / polylines */}
        {routes.map((route, idx) => (
          <Polyline
            key={idx}
            positions={route.points}
            pathOptions={{
              color: route.color ?? '#10b981',
              weight: 2,
              opacity: 0.85,
              dashArray: route.animated ? '10 20' : undefined,
            }}
          />
        ))}

        {/* Invalidate map size on mount + tab-switch */}
        <MapInvalidator />
      </MapContainer>
    </div>
  )
}

export default GeoView
