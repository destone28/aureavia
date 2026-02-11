import api from '../config/api';

export interface DashboardKPIs {
  total_rides: number;
  total_revenue: number;
  active_drivers: number;
  avg_rating: number;
  rides_today: number;
  rides_change_pct: number;
  revenue_change_pct: number;
}

export interface EarningsDataPoint {
  date: string;
  amount: number;
}

export interface EarningsData {
  granularity: string;
  data: EarningsDataPoint[];
}

export interface DriverListItem {
  id: string;
  user_id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  company_name: string | null;
  rating_avg: number;
  total_rides: number;
  total_earnings: number;
  vehicle_plate: string | null;
  vehicle_make: string | null;
  vehicle_model: string | null;
}

export interface CompanyListItem {
  id: string;
  name: string;
  contact_email: string;
  contact_person: string | null;
  contact_phone: string | null;
  status: string;
  active_drivers?: number;
}

export async function fetchDashboardKPIs(): Promise<DashboardKPIs> {
  const { data } = await api.get('/reports/dashboard');
  return data;
}

export async function fetchEarnings(granularity: string = 'daily'): Promise<EarningsData> {
  const { data } = await api.get(`/reports/earnings?granularity=${granularity}`);
  return data;
}

export async function fetchDriversList(): Promise<DriverListItem[]> {
  const { data } = await api.get('/drivers/');
  return data;
}

export async function fetchCompaniesList(): Promise<CompanyListItem[]> {
  const { data } = await api.get('/companies/');
  return data;
}

export async function createCompany(payload: Partial<CompanyListItem>): Promise<CompanyListItem> {
  const { data } = await api.post('/companies/', payload);
  return data;
}

export async function updateCompany(id: string, payload: Partial<CompanyListItem>): Promise<CompanyListItem> {
  const { data } = await api.put(`/companies/${id}`, payload);
  return data;
}
