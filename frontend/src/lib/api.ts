export const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

export async function fetchProjects() {
  const res = await fetch(`${API_BASE}/projects/?limit=50`);
  if (!res.ok) throw new Error('Failed to fetch projects');
  return res.json();
}

export async function fetchProjectDetails(id: string) {
  const res = await fetch(`${API_BASE}/projects/${id}`);
  if (!res.ok) throw new Error('Failed to fetch project details');
  return res.json();
}

export async function fetchProjectRisk(id: string) {
  const res = await fetch(`${API_BASE}/projects/${id}/risk`);
  if (!res.ok) throw new Error('Failed to fetch project risk');
  return res.json();
}

export async function fetchRealityGap(id: string) {
  const res = await fetch(`${API_BASE}/projects/${id}/reality-gap`);
  if (!res.ok) throw new Error('Failed to fetch reality gap');
  return res.json();
}

export async function fetchDigitalTwin(id: string) {
  const res = await fetch(`${API_BASE}/projects/${id}/digital-twin`);
  if (!res.ok) throw new Error('Failed to fetch digital twin');
  return res.json();
}
export async function fetchProjectTimeline(id: string) {
  const res = await fetch(`${API_BASE}/projects/${id}/timeline`);
  if (!res.ok) throw new Error('Failed to fetch timeline');
  return res.json();
}

export async function fetchProjectRecommendations(id: string) {
  const res = await fetch(`${API_BASE}/projects/${id}/recommendations`);
  if (!res.ok) throw new Error('Failed to fetch recommendations');
  return res.json();
}
