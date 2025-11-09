export interface AIStrategy {
  reasoning: string;
  attack_plan: string;
  expected_findings: string[];
}

export interface AgentThought {
  step: number;
  state: 'planning' | 'executing' | 'analyzing' | 'refining' | 'complete';
  thought: string;
  action?: string | null;
  observation?: string | null;
  timestamp: string;
}

export interface Scan {
  id: string;
  target: string;
  user_prompt?: string | null;
  ai_strategy?: AIStrategy | null;
  agent_thoughts?: AgentThought[] | null;
  tools: string[];
  profile: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  current_tool: string | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ScanResult {
  id: string;
  scan_id: string;
  tool_name: string;
  raw_output: string;
  parsed_output: any;
  exit_code: number;
  execution_time: number;
  error_message: string | null;
  created_at: string;
}

export interface AIAnalysis {
  id: string;
  scan_id: string;
  model_used: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
  prompt_text?: string;  // Full prompt sent to AI
  analysis_text: string;
  created_at: string;
}

export interface ScanCreateRequest {
  target: string;
  user_prompt?: string;
  tools?: string[];
  profile: string;
  enable_ai: boolean;
}

export interface ScanDetailsResponse {
  scan: Scan;
  results: ScanResult[];
  analysis: AIAnalysis | null;
}
