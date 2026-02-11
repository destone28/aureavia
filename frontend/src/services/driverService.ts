import api from '../config/api';

export interface DriverProfile {
  id: string;
  user_id: string;
  license_number: string | null;
  license_expiry: string | null;
  vehicle_make: string | null;
  vehicle_model: string | null;
  vehicle_plate: string | null;
  vehicle_year: number | null;
  vehicle_seats: number;
  vehicle_luggage_capacity: number;
  vehicle_fuel_type: string | null;
  insurance_number: string | null;
  insurance_expiry: string | null;
  vehicle_inspection_date: string | null;
  special_permits: any;
  rating_avg: number;
  total_km: number;
  total_rides: number;
  total_earnings: number;
  ncc_company_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface DriverStats {
  total_rides: number;
  total_earnings: number;
  total_km: number;
  rating_avg: number;
  completed_this_month: number;
  earnings_this_month: number;
}

export async function fetchMyDriver(): Promise<DriverProfile> {
  const { data } = await api.get('/drivers/me');
  return data;
}

export async function fetchDriverStats(driverId: string): Promise<DriverStats> {
  const { data } = await api.get(`/drivers/${driverId}/stats`);
  return data;
}
