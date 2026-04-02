export type ThemePreference = "light" | "dark" | "system";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: "user" | "admin";
  is_active: boolean;
  job_title?: string | null;
  organization?: string | null;
  commute_line?: string | null;
  theme_preference: ThemePreference;
  created_at: string;
  updated_at: string;
};

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type Station = {
  id: string;
  code: string;
  name: string;
  line: string;
  zone: string;
  latitude: number;
  longitude: number;
  baseline_capacity: number;
  is_interchange: boolean;
};

export type PassengerFlow = {
  id: string;
  station_id: string;
  station_name: string;
  line: string;
  timestamp: string;
  passenger_count: number;
  avg_dwell_minutes: number;
  weather_code: string;
  event_flag: boolean;
  event_name?: string | null;
  source: string;
};

export type Prediction = {
  id: string;
  station_id: string;
  station_name: string;
  line: string;
  target_timestamp: string;
  predicted_count: number;
  baseline_count: number;
  confidence_score: number;
  anomaly_score: number;
  recommended_action: string;
  model_version: string;
  generated_at: string;
};

export type DashboardKpi = {
  label: string;
  value: string;
  change: string;
  tone: "neutral" | "good" | "warning" | "critical";
};

export type DashboardTrendPoint = {
  label: string;
  actual: number | null;
  forecast: number | null;
};

export type DashboardBreakdownPoint = {
  label: string;
  value: number;
};

export type DashboardHeatmapRow = {
  day_label: string;
  values: number[];
};

export type DashboardAlert = {
  title: string;
  detail: string;
  severity: "normal" | "warning" | "critical";
  timestamp: string;
};

export type DashboardOverview = {
  generated_at: string;
  selected_station_id: string;
  selected_station_name: string;
  model_version: string;
  insight: string;
  kpis: DashboardKpi[];
  trend: DashboardTrendPoint[];
  hourly_distribution: DashboardBreakdownPoint[];
  heatmap: DashboardHeatmapRow[];
  recent_flows: PassengerFlow[];
  recent_predictions: Prediction[];
  alerts: DashboardAlert[];
};

export type HistoricalSeriesPoint = {
  label: string;
  total_passengers: number;
};

export type HistoricalAnalytics = {
  generated_at: string;
  station_id: string;
  station_name: string;
  days: number;
  daily_totals: HistoricalSeriesPoint[];
  hourly_average: DashboardBreakdownPoint[];
  heatmap: DashboardHeatmapRow[];
  latest_records: PassengerFlow[];
};

export type ProfileResponse = {
  user: User;
};

export type TrainResult = {
  status: string;
  model_version: string;
  rmse: number;
  mae: number;
  message: string;
};
