export type AssistantState = 
  | 'IDLE' 
  | 'LISTENING' 
  | 'THINKING' 
  | 'USING_TOOL' 
  | 'SPEAKING' 
  | 'ERROR';

export interface Note {
  id: number;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface Reminder {
  id: number;
  title: string;
  scheduled_datetime: string;
  status: 'pending' | 'completed' | 'cancelled';
  created_at: string;
}

export interface ActivityItem {
  id: string;
  timestamp: string;
  type: 'tool_start' | 'tool_result' | 'transcript' | 'assistant_speech' | 'interruption';
  toolName?: string;
  details: string;
  status?: 'pending' | 'success' | 'failed';
}

export interface LatencyMetrics {
  stt_latency?: number;
  llm_ttft?: number;
  tool_execution_time?: number;
  tts_first_audio?: number;
  total_latency?: number;
}

export interface WSMessage {
  type: string;
  value?: AssistantState;
  text?: string;
  tool?: string;
  params?: Record<string, any>;
  result?: Record<string, any>;
  data?: string;
  sample_rate?: number;
  message?: string;
  conversation_id?: string;
  metrics?: LatencyMetrics;
}
