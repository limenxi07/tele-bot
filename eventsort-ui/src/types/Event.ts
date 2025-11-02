export interface Event {
  id: number;
  user_id: number;
  username: string;
  title: string;
  event_type: string;
  date: string;
  location: string | null;
  synopsis: string;
  organisation: string | null;
  fee: number | null;
  signup_link: string | null;
  deadline: string | null;
  target_audience: string | null;
  refreshments: string | null;
  key_speakers: string | null;
  raw_message?: string | null;
  user_interested: boolean | null;
  date_created: string;
}

export interface AuthResponse {
  user_id: number;
  username: string;
  message: string;
}

export interface SwipeResponse {
  success: boolean;
  event_id: number;
  interested: boolean;
  message: string;
}

export interface Stats {
  total_events: number;
  interested: number;
  not_interested: number;
  pending_swipes: number;
  urgent_events: number;
}