import api from '../config/api';

export interface Ride {
  id: string;
  external_id: string | null;
  source_platform: string;
  status: 'to_assign' | 'booked' | 'in_progress' | 'completed' | 'cancelled' | 'critical';
  pickup_address: string;
  pickup_lat: number | null;
  pickup_lng: number | null;
  dropoff_address: string;
  dropoff_lat: number | null;
  dropoff_lng: number | null;
  scheduled_at: string;
  started_at: string | null;
  completed_at: string | null;
  passenger_name: string | null;
  passenger_phone: string | null;
  passenger_count: number;
  route_type: string | null;
  distance_km: number | null;
  duration_min: number | null;
  price: number | null;
  driver_share: number | null;
  notes: string | null;
  driver_id: string | null;
  assigned_by: string | null;
  created_at: string;
  updated_at: string;
}

export interface RidesListResponse {
  rides: Ride[];
  total: number;
  page: number;
  page_size: number;
}

export interface RidesFilters {
  status?: string;
  date_from?: string;
  date_to?: string;
  source_platform?: string;
  page?: number;
  page_size?: number;
}

/**
 * Fetch rides list with optional filters
 */
export async function fetchRides(filters?: RidesFilters): Promise<RidesListResponse> {
  const { data } = await api.get<RidesListResponse>('/rides', { params: filters });
  return data;
}

/**
 * Fetch a single ride by ID
 */
export async function fetchRide(id: string): Promise<Ride> {
  const { data } = await api.get<Ride>(`/rides/${id}`);
  return data;
}

/**
 * Accept a ride assignment (driver action)
 */
export async function acceptRide(id: string): Promise<Ride> {
  const { data } = await api.put<Ride>(`/rides/${id}/accept`);
  return data;
}

/**
 * Start a ride (driver action)
 */
export async function startRide(id: string): Promise<Ride> {
  const { data } = await api.put<Ride>(`/rides/${id}/start`);
  return data;
}

/**
 * Complete a ride (driver action)
 */
export async function completeRide(id: string): Promise<Ride> {
  const { data } = await api.put<Ride>(`/rides/${id}/complete`);
  return data;
}

/**
 * Cancel a ride with optional notes
 */
export async function cancelRide(id: string, notes?: string): Promise<Ride> {
  const { data } = await api.put<Ride>(`/rides/${id}/cancel`, { notes });
  return data;
}
