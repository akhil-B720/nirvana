import { useEffect, useState } from 'react';
import { Card, Badge, Button } from '../components/ui/core';
import { Link } from 'react-router-dom';
import { fetchProjects } from '../lib/api';
import { formatCompactCurrency } from '../lib/utils';
import { ShieldAlert, Map, Database, ArrowRight } from 'lucide-react';

export default function Dashboard() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjects()
      .then(setProjects)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen p-8 max-w-7xl mx-auto space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-primary to-blue-400 bg-clip-text text-transparent">NIRVANA</h1>
          <p className="text-white/60 mt-2">National Infrastructure Reality & Verification Network using AI</p>
        </div>
        <div className="flex gap-4">
          <Link to="/map">
            <Button variant="outline"><Map size={18} /> Command Center</Button>
          </Link>
        </div>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="items-center justify-center text-center py-10">
          <Database size={40} className="text-primary mb-4" />
          <h3 className="text-3xl font-bold">{projects.length > 0 ? projects.length : '-'}</h3>
          <p className="text-sm text-white/50 mt-1">Total Monitored Projects</p>
        </Card>
        
        <Card className="items-center justify-center text-center py-10 relative overflow-hidden">
          <div className="absolute inset-0 bg-risk-critical/10 blur-xl"></div>
          <ShieldAlert size={40} className="text-risk-critical mb-4 relative z-10" />
          <h3 className="text-3xl font-bold text-risk-critical relative z-10">
            {projects.filter(p => ['STALLED', 'DELAYED'].includes(p.status)).length}
          </h3>
          <p className="text-sm text-white/50 mt-1 relative z-10">Flagged For Review (Mock)</p>
        </Card>
        
        <Card className="items-center justify-center text-center py-10">
          <h3 className="text-3xl font-bold text-primary">₹ {formatCompactCurrency(projects.reduce((sum, p) => sum + (p.sanction_amount || 0), 0))}</h3>
          <p className="text-sm text-white/50 mt-1">Total Public Funds Sanctioned</p>
        </Card>
      </div>

      <div className="mt-10">
        <h2 className="text-2xl font-bold mb-6">Recent Project Intelligence</h2>
        {loading ? (
          <div className="text-center text-white/50 py-20 animate-pulse">Loading intelligence feed...</div>
        ) : (
          <div className="grid grid-cols-1 gap-4">
            {projects.slice(0, 50).map(project => (
              <ProjectListItem key={project.id} project={project} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ProjectListItem({ project }: { project: any }) {
  return (
    <Card className="flex-row items-center justify-between p-4 hover:border-primary/50 transition-colors group">
      <div className="flex-1">
        <div className="flex items-center gap-3 mb-1">
          <h3 className="font-semibold text-lg">{project.name}</h3>
          {(project.status === 'STALLED' || project.status === 'DELAYED') && (
            <Badge variant="danger">High Risk</Badge>
          )}
          {project.data_availability_status === 'SYNTHETIC' && (
            <Badge variant="warning">Synthetic</Badge>
          )}
        </div>
        <div className="flex gap-4 text-sm text-white/50">
          <span>{project.district}, {project.state}</span>
          <span>•</span>
          <span>{project.sector}</span>
          <span>•</span>
          <span>₹ {formatCompactCurrency(project.sanction_amount || 0)}</span>
        </div>
      </div>
      <div>
        <Link to={`/project/${project.id}`}>
          <Button variant="secondary" className="group-hover:bg-primary group-hover:text-white transition-colors">
            Analyze <ArrowRight size={16} />
          </Button>
        </Link>
      </div>
    </Card>
  );
}
