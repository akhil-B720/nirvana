import { useEffect, useRef, useState } from 'react';
import maplibregl from 'maplibre-gl';
import { fetchProjects } from '../lib/api';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { Button } from '../components/ui/core';

export default function CommandCenter() {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const [projects, setProjects] = useState<any[]>([]);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(console.error);
  }, []);

  useEffect(() => {
    if (map.current || !mapContainer.current) return;

    // Use a beautiful, dark MapLibre Voyager theme from MapTiler or a generic basemap
    // For free & local we use OpenStreetMap formatted dark via a free raster tile or custom style
    const darkStyle: maplibregl.StyleSpecification = {
      version: 8,
      sources: {
        'osm': {
          type: 'raster',
          tiles: ['https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png'],
          tileSize: 256,
          attribution: '&copy; OpenStreetMap &copy; CARTO',
        }
      },
      layers: [
        {
          id: 'osm',
          type: 'raster',
          source: 'osm',
          minzoom: 0,
          maxzoom: 22,
        }
      ]
    };

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: darkStyle,
      center: [78.9629, 20.5937], // India center
      zoom: 4,
      pitch: 45, // 3D tilt
    });

    map.current.addControl(new maplibregl.NavigationControl(), 'top-right');
    
    // Once data is loaded, add markers
    map.current.on('load', () => {
      // Data bound effect handles this below
    });

    return () => {
      map.current?.remove();
      map.current = null;
    };
  }, []);

  // Add markers when projects arrived
  useEffect(() => {
    if (!map.current || projects.length === 0) return;

    // Remove existing markers if any (simplified: we just add for prototype)
    projects.forEach(p => {
      if (p.latitude && p.longitude) {
        
        // Define marker color based on status
        let color = '#0ea5e9'; // primary
        if (p.status === 'STALLED' || p.status === 'DELAYED') color = '#ef4444'; // critical
        if (p.data_availability_status === 'SYNTHETIC') color = '#eab308'; // warning for synthetic

        // Create popup
        const maxAmt = `${~~(p.sanction_amount / 100000)}L`; // simple format

        const popupHTML = `
          <div class="px-2 pb-1">
            <h4 class="font-bold text-sm mb-1">${p.name}</h4>
            <div class="text-xs text-white/70">
              ${p.district}, ${p.state}<br/>
              <b>Amt:</b> ₹ ${maxAmt} | <b>Status:</b> ${p.status}
              <br/><br/>
              <a href="/project/${p.id}" class="text-primary hover:underline font-bold">Analyze Project →</a>
            </div>
          </div>
        `;

        new maplibregl.Marker({ color })
          .setLngLat([p.longitude, p.latitude])
          .setPopup(new maplibregl.Popup({ offset: 25 }).setHTML(popupHTML))
          .addTo(map.current!);
      }
    });

  }, [projects]);

  return (
    <div className="relative h-screen w-screen overflow-hidden bg-black">
      {/* Top HUD */}
      <div className="absolute top-0 left-0 right-0 z-10 p-4 pointer-events-none">
        <div className="flex justify-between items-start pointer-events-auto">
          
          <div className="flex gap-4 items-center glass-panel px-6 py-4 rounded-xl">
            <Link to="/dashboard">
               <Button variant="outline" className="px-3 border-none hover:bg-white/10"><ArrowLeft size={18} /></Button>
            </Link>
            <div>
              <h1 className="font-bold text-xl tracking-widest">COMMAND CENTER <span className="text-primary font-bold ml-2">GIS</span></h1>
              <p className="text-xs text-white/50 tracking-widest font-mono mt-1">Geospatial Intelligence Engine</p>
            </div>
          </div>

          <div className="glass-panel px-6 py-4 rounded-xl text-right">
            <div className="text-2xl font-bold text-primary font-mono">{projects.length}</div>
            <div className="text-xs text-white/50 tracking-widest">NODES ACTIVE</div>
          </div>

        </div>
      </div>
      
      {/* Map Container */}
      <div ref={mapContainer} className="absolute inset-0 w-full h-full" />
      
      {/* Crosshair / Overlay overlay */}
      <div className="absolute inset-0 pointer-events-none border-[1px] border-primary/20 bg-[radial-gradient(ellipse_at_center,_rgba(0,0,0,0)_50%,_rgba(0,0,0,0.8)_100%)]"></div>
    </div>
  );
}
