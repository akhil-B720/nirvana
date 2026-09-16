import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { fetchProjectDetails, fetchProjectRisk, fetchRealityGap, fetchDigitalTwin, fetchProjectTimeline, fetchProjectRecommendations } from '../lib/api';
import { formatCurrency } from '../lib/utils';
import { Card, Badge, Button } from '../components/ui/core';
import { ArrowLeft, BrainCircuit, Activity, FileText, AlertTriangle, Box } from 'lucide-react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Environment, Grid } from '@react-three/drei';

export default function ProjectDetails() {
  const { id } = useParams<{ id: string }>();
  const [data, setData] = useState<any>(null);
  const [risk, setRisk] = useState<any>(null);
  const [gap, setGap] = useState<any>(null);
  const [, setTwin] = useState<any>(null);
  const [timeline, setTimeline] = useState<any>(null);
  const [recs, setRecs] = useState<any>(null);
  const [sliderValue, setSliderValue] = useState<number | null>(null);

  useEffect(() => {
    if (!id) return;
    
    Promise.all([
      fetchProjectDetails(id).catch(() => null),
      fetchProjectRisk(id).catch(() => null),
      fetchRealityGap(id).catch(() => null),
      fetchDigitalTwin(id).catch(() => null),
      fetchProjectTimeline(id).catch(() => null),
      fetchProjectRecommendations(id).catch(() => null),
    ]).then(([d, r, g, t, tm, rc]) => {
      setData(d);
      setRisk(r);
      setGap(g);
      setTwin(t);
      setTimeline(tm);
      setRecs(rc);
    });
  }, [id]);

  if (!data) return <div className="p-10 text-center animate-pulse text-primary font-mono">NEURAL SYNCING...</div>;

  return (
    <div className="min-h-screen pb-20">
      {/* Header bar */}
      <div className="bg-gov-navy border-b border-white/5 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto p-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/dashboard">
              <Button variant="outline" className="px-3"><ArrowLeft size={18} /></Button>
            </Link>
            <div>
              <h1 className="font-bold text-xl">{data.name}</h1>
              <p className="text-xs text-white/50 tracking-widest">{data.id}</p>
            </div>
          </div>
          <div className="flex items-center gap-4">
            {data.data_availability_status === 'SYNTHETIC' && (
              <Badge variant="warning">SYNTHETIC DATA</Badge>
            )}
            <Badge variant={data.status === 'COMPLETED' ? 'success' : data.status === 'IN_PROGRESS' ? 'default' : 'danger'}>
              {data.status}
            </Badge>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto p-4 md:p-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: Overview & Risk */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-white/10 pb-2">
              <FileText size={18} className="text-primary"/> Overview
            </h2>
            <div className="space-y-3 text-sm">
              <div className="grid grid-cols-2"><span className="text-white/50">Location:</span> <span>{data.district}, {data.state}</span></div>
              <div className="grid grid-cols-2"><span className="text-white/50">Sector:</span> <span>{data.sector}</span></div>
              <div className="grid grid-cols-2"><span className="text-white/50">Agency:</span> <span>{data.agency || '-'}</span></div>
              <div className="grid grid-cols-2"><span className="text-white/50">Const:</span> <span>{data.constituency}</span></div>
              <div className="grid grid-cols-2"><span className="text-white/50">Sanctioned:</span> <span className="font-bold text-white">{formatCurrency(data.sanction_amount || 0)}</span></div>
              <div className="grid grid-cols-2"><span className="text-white/50">Reported %:</span> <span className="font-medium text-primary">{data.reported_progress}%</span></div>
            </div>
          </Card>

          {/* AI Risk Card */}
          <Card className="relative overflow-hidden border-t-2 border-t-primary">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <BrainCircuit size={100} />
            </div>
            <h2 className="text-lg font-bold mb-2 flex items-center gap-2 relative z-10">
              <BrainCircuit size={18} className="text-primary"/> AI Risk Analysis
            </h2>
            
            {risk ? (
              <div className="relative z-10 space-y-4">
                <div className="flex items-end justify-between">
                  <div>
                    <div className="text-4xl font-bold bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">
                      {risk.risk_score}
                    </div>
                    <div className="text-xs font-mono text-white/50">/ 100 RISK INDEX</div>
                  </div>
                  <Badge variant={risk.risk_level === 'CRITICAL' ? 'danger' : 'warning'}>{risk.risk_level}</Badge>
                </div>
                
                <div className="bg-black/30 p-3 rounded-lg text-sm border border-white/5 text-white/80">
                  {risk.explanation}
                </div>

                <div className="space-y-2">
                  <h3 className="text-xs font-bold text-white/50 uppercase tracking-widest">Confidence Metrics</h3>
                  <div className="w-full bg-white/5 h-2 rounded-full overflow-hidden">
                    <div className="bg-primary h-full" style={{ width: `${risk.confidence * 100}%` }}></div>
                  </div>
                  <div className="text-xs flex justify-between text-white/40 font-mono">
                    <span>{risk.available_signals}/{risk.total_signals} Signals Active</span>
                    <span>{(risk.confidence * 100).toFixed(0)}% Confidence</span>
                  </div>
                </div>
              </div>
            ) : (
              <div className="text-sm text-white/40 italic">Analysis unavailable. Engine warming up...</div>
            )}
          </Card>
          
          {/* Recommendations Card */}
          {recs && recs.recommendations && recs.recommendations.length > 0 && (
            <Card>
              <h2 className="text-sm font-bold text-white/50 tracking-widest uppercase mb-4 flex items-center gap-2 border-b border-white/10 pb-2">
                Verification Recommendations
              </h2>
              <div className="space-y-3 text-sm">
                {recs.recommendations.map((r: any, idx: number) => (
                  <div key={idx} className="bg-risk-medium/10 p-3 rounded-lg border border-risk-medium/20 text-white/80">
                    <span className="font-bold text-risk-medium block mb-1">{r.issue}</span>
                    <span>{r.action}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>

        {/* MIDDLE/RIGHT COLUMN: Digital Twin & Analytics */}
        <div className="lg:col-span-2 space-y-6">

          {/* Abstract Digital Twin View */}
          <Card className="!p-0 h-[400px] relative overflow-hidden bg-black flex flex-col">
            <div className="p-4 absolute top-0 left-0 right-0 z-10 flex justify-between items-start pointer-events-none">
              <div>
                <h2 className="text-lg font-bold flex items-center gap-2">
                  <Box size={18} className="text-primary"/> Digital Twin Sandbox
                </h2>
                <div className="text-xs font-mono text-white/60">Type: {data.project_type || 'GENERAL'} | Compare Expected vs Reported</div>
              </div>
              <Badge variant="default" className="backdrop-blur-md bg-black/50">LIVE ARCHITECTURE</Badge>
            </div>
            
            <div className="absolute bottom-4 left-4 right-4 z-10 bg-black/50 p-3 rounded-lg backdrop-blur-md border border-white/10 flex items-center gap-4">
              <span className="text-xs font-bold text-white/60 w-24">PROGRESS</span>
              <input 
                type="range" 
                min="0" max="100" 
                value={sliderValue !== null ? sliderValue : (data.reported_progress || 0)} 
                onChange={(e) => setSliderValue(Number(e.target.value))}
                className="flex-1 accent-primary" 
              />
              <span className="text-xs font-mono text-primary w-12 text-right">
                {sliderValue !== null ? sliderValue : (data.reported_progress || 0)}%
              </span>
              <Button variant="outline" onClick={() => setSliderValue(null)} className="text-xs py-1 h-auto">
                RESET
              </Button>
            </div>

            <div className="flex-1 w-full h-full cursor-move">
              <Canvas camera={{ position: [5, 5, 5], fov: 50 }}>
                <ambientLight intensity={0.5} />
                <directionalLight position={[10, 10, 5]} intensity={1} />
                <Environment preset="city" />
                
                <TwinRenderer 
                    type={data.project_type || 'BUILDING'} 
                    reportedProgress={sliderValue !== null ? sliderValue : (data.reported_progress || 0)}
                    expectedProgress={gap?.expected_progress || 100}
                />
                
                <Grid infiniteGrid fadeDistance={40} sectionColor="#1a233a" cellColor="#0b101e" position={[0, -1, 0]} />
                <OrbitControls enablePan={true} enableZoom={true} />
              </Canvas>
            </div>
          </Card>

          {/* Reality Gap Engine Output */}
          <Card>
             <h2 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-white/10 pb-2">
              <Activity size={18} className="text-primary"/> Reality Gap Engine
            </h2>
            {gap ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-2xl font-bold font-mono">
                    {gap.expected_progress ? `${gap.expected_progress.toFixed(1)}%` : 'N/A'}
                  </h3>
                  <div className="text-xs text-white/50 tracking-widest mt-1">EXPECTED PROGRESS</div>
                  <p className="text-xs text-white/40 mt-3 border-l-2 border-primary pl-2">
                    Calculated using temporal phase simulation based on '{data.sector}' curves.
                  </p>
                </div>

                <div className="space-y-4">
                  {gap.contributing_factors.map((factor: string, idx: number) => (
                    <div key={idx} className="flex gap-3 items-start bg-risk-medium/10 p-3 rounded-lg border border-risk-medium/20 text-sm">
                      <AlertTriangle size={16} className="text-risk-medium flex-shrink-0 mt-0.5" />
                      <span>{factor}</span>
                    </div>
                  ))}
                  {gap.contributing_factors.length === 0 && (
                    <div className="flex gap-3 items-start bg-risk-low/10 p-3 rounded-lg border border-risk-low/20 text-sm">
                       <span className="text-risk-low font-bold uppercase tracking-widest text-xs">No active reality flags</span>
                    </div>
                  )}
                </div>
              </div>
            ) : (
                <div className="text-sm text-white/40 italic">Engine offline or collecting data...</div>
            )}
          </Card>

            {/* Timeline UI */}
            <Card className="mt-6">
               <h2 className="text-lg font-bold mb-4 flex items-center gap-2 border-b border-white/10 pb-2">
                Timeline & Evidence Chain
              </h2>
              {timeline && timeline.timeline && timeline.timeline.length > 0 ? (
                <div className="space-y-4">
                  {timeline.timeline.map((event: any, idx: number) => (
                    <div key={idx} className="flex gap-4 border-l-2 border-primary/40 pl-4 py-1">
                      <div className="text-xs text-white/50 w-24 flex-shrink-0">
                        {new Date(event.date).toLocaleDateString()}
                      </div>
                      <div>
                        <div className="font-bold text-sm tracking-wide mb-1 text-white/90">
                           {event.type}
                        </div>
                        <div className="text-xs text-white/60 mb-1">{event.description}</div>
                        <div className="text-[10px] text-white/30 uppercase tracking-widest">{event.source}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-sm text-white/40 italic">No historical events tracked.</div>
              )}
            </Card>

        </div>
      </div>
    </div>
  );
}

function TwinRenderer({ type, reportedProgress, expectedProgress }: { type: string, reportedProgress: number, expectedProgress: number }) {
  // We overlay two models: The expected as a transparent wireframe, and the actual as solid
  return (
    <group position={[0, -0.5, 0]}>
      {/* Expected model - Ghost wireframe */}
      {renderModel(type, expectedProgress, true)}
      {/* Actual progress - Solid model */}
      {renderModel(type, reportedProgress, false)}
    </group>
  );
}

function renderModel(type: string, progress: number, isGhost: boolean) {
  const norm = progress / 100;
  
  if (type === 'ROAD') {
      const length = 10 * norm;
      return (
          <group position={[0, 0, 0]}>
              <mesh position={[0, 0.1, (10 - length)/2 - 5]} castShadow={!isGhost} receiveShadow={!isGhost}>
                  <boxGeometry args={[2, 0.2, length]} />
                  <meshStandardMaterial 
                      color={isGhost ? 0xffffff : 0x334155} 
                      wireframe={isGhost} 
                      transparent={isGhost} 
                      opacity={isGhost ? 0.2 : 1} 
                  />
              </mesh>
          </group>
      );
  }
  
  if (type === 'BRIDGE') {
      const length = 8 * norm;
      const pillars = Math.floor(length / 2);
      return (
          <group position={[0, 0, 0]}>
              <mesh position={[0, 2, (8 - length)/2 - 4]} castShadow={!isGhost}>
                  <boxGeometry args={[2, 0.4, length]} />
                  <meshStandardMaterial color={isGhost ? 0xffffff : 0x0ea5e9} wireframe={isGhost} transparent opacity={isGhost ? 0.2 : 0.9} />
              </mesh>
              {Array.from({length: pillars}).map((_, i) => (
                  <mesh key={`p-${i}`} position={[0, 1, -4 + (i * 2.5)]}>
                      <cylinderGeometry args={[0.3, 0.4, 2]} />
                      <meshStandardMaterial color={isGhost ? 0xffffff : 0x64748b} wireframe={isGhost} transparent opacity={isGhost ? 0.1 : 0.9} />
                  </mesh>
              ))}
          </group>
      );
  }
  
  if (type === 'WATER_TANK') {
      const height = 3 * norm;
      return (
          <group position={[0, 0, 0]}>
              {/* Pillars full height always if even 10% progress */}
              {progress > 10 && (
                <>
                  <mesh position={[-1, 2, -1]}><cylinderGeometry args={[0.1, 0.1, 4]}/><meshStandardMaterial color={isGhost ? 0xffffff : 0x64748b} wireframe={isGhost} transparent opacity={isGhost ? 0.2 : 1}/></mesh>
                  <mesh position={[1, 2, -1]}><cylinderGeometry args={[0.1, 0.1, 4]}/><meshStandardMaterial color={isGhost ? 0xffffff : 0x64748b} wireframe={isGhost} transparent opacity={isGhost ? 0.2 : 1}/></mesh>
                  <mesh position={[-1, 2, 1]}><cylinderGeometry args={[0.1, 0.1, 4]}/><meshStandardMaterial color={isGhost ? 0xffffff : 0x64748b} wireframe={isGhost} transparent opacity={isGhost ? 0.2 : 1}/></mesh>
                  <mesh position={[1, 2, 1]}><cylinderGeometry args={[0.1, 0.1, 4]}/><meshStandardMaterial color={isGhost ? 0xffffff : 0x64748b} wireframe={isGhost} transparent opacity={isGhost ? 0.2 : 1}/></mesh>
                </>
              )}
              {progress > 30 && (
                <mesh position={[0, 4 + height/2 - 1.5, 0]} castShadow={!isGhost}>
                    <cylinderGeometry args={[2, 2, height, 16]} />
                    <meshStandardMaterial color={isGhost ? 0xffffff : 0x3b82f6} wireframe={isGhost} transparent opacity={isGhost ? 0.2 : 0.9} />
                </mesh>
              )}
          </group>
      );
  }
  
  // Default: BUILDING
  const blocks = 5;
  const blocksVisible = Math.max(1, Math.ceil(norm * blocks));
  return (
      <group position={[0, 0, 0]}>
          {Array.from({ length: isGhost ? blocks : blocksVisible }).map((_, i) => (
             <mesh key={`b-${i}`} position={[0, i * 0.8, 0]} castShadow={!isGhost} receiveShadow={!isGhost}>
                 <boxGeometry args={[3 - i*0.2, 0.7, 3 - i*0.2]} />
                 <meshStandardMaterial 
                     color={isGhost ? 0xffffff : 0x0ea5e9} 
                     wireframe={isGhost} 
                     transparent={isGhost || !isGhost} 
                     opacity={isGhost ? 0.1 : 0.9} 
                 />
             </mesh>
          ))}
          {!isGhost && (
              <mesh position={[0, blocks*0.4, 0]}>
                 <cylinderGeometry args={[0.2, 0.2, blocks*0.8, 8]} />
                 <meshStandardMaterial color={0xffffff} transparent opacity={0.1} />
              </mesh>
          )}
      </group>
  );
}
