import api from '../config/api';

export interface BookingConfig {
  client_id: string;
  api_base_url: string;
  webhook_secret: string;
  is_enabled: boolean;
  environment: string;
  last_sync_at: string | null;
  has_client_secret: boolean;
}

export interface BookingConfigUpdate {
  client_id?: string;
  client_secret?: string;
  api_base_url?: string;
  webhook_secret?: string;
  is_enabled?: boolean;
  environment?: string;
}

export interface BookingTestResult {
  success: boolean;
  message: string;
}

export interface BookingSyncResult {
  success: boolean;
  new_rides: number;
  updated_rides: number;
  message: string;
}

export async function fetchBookingConfig(): Promise<BookingConfig> {
  const { data } = await api.get<BookingConfig>('/booking/config');
  return data;
}

export async function updateBookingConfig(config: BookingConfigUpdate): Promise<BookingConfig> {
  const { data } = await api.put<BookingConfig>('/booking/config', config);
  return data;
}

export async function testBookingConnection(): Promise<BookingTestResult> {
  const { data } = await api.post<BookingTestResult>('/booking/test');
  return data;
}

export async function syncBookings(): Promise<BookingSyncResult> {
  const { data } = await api.post<BookingSyncResult>('/booking/sync');
  return data;
}
