export type Rating = 'Below expectations' | 'Meet expectations' | 'Exceeds expectations' | 'insufficient_data';

export interface Employee {
  employee_id: string;
  full_name: string;
  position?: string;
  level?: string;
  status: string;
  manager_id?: string;
}

export interface EmployeeStats extends Employee {
  total_feedback: number;
  mapped_feedback: number;
  unmapped_feedback: number;
  rating_recommendation?: Rating;
  top_strengths: string[];
  top_growth_areas: string[];
}

export interface Criterion {
  criterion_id: string;
  criterion_name: string;
  below_description: string;
  meet_description: string;
  exceeds_description: string;
  role?: string;
  weight: number;
  is_key_criterion: boolean;
  is_active: boolean;
  sort_order: number;
}

export interface FeedbackMapping {
  mapping_id: string;
  feedback_id: string;
  criterion_id: string;
  criterion_name?: string;
  original_fragment?: string;
  suggested_rating?: Rating;
  confirmed_rating?: Rating;
  llm_explanation?: string;
  manager_confirmed: boolean;
  confirmed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface Feedback {
  feedback_id: string;
  employee_id: string;
  manager_id: string;
  period_id?: string;
  feedback_date: string;
  original_text: string;
  source: string;
  status: 'confirmed' | 'draft' | 'no_criterion' | 'needs_review';
  mappings: FeedbackMapping[];
  employee_name?: string;
  manager_name?: string;
  created_at: string;
  updated_at: string;
}

export interface Period {
  period_id: string;
  period_name: string;
  start_date: string;
  end_date: string;
  is_active: boolean;
}

export interface CriterionBreakdown {
  criterion_name: string;
  below_count: number;
  meet_count: number;
  exceeds_count: number;
  evidence_quotes: string[];
}

export interface StrengthArea {
  criterion_name: string;
  pattern_description: string;
  evidence_quotes: string[];
  is_key_criterion?: boolean;
  is_systemic?: boolean;
}

export interface Summary {
  summary_id: string;
  employee_id: string;
  period_id: string;
  generated_at: string;
  total_feedback_count: number;
  mapped_feedback_count: number;
  unmapped_feedback_count: number;
  strengths?: StrengthArea[];
  growth_areas?: StrengthArea[];
  criterion_breakdown?: CriterionBreakdown[];
  top_criteria?: { criterion_name: string; mention_count: number }[];
  repeating_patterns?: { description: string; frequency: number; evidence_quotes: string[] }[];
  rating_recommendation?: Rating;
  arguments_for?: string[];
  arguments_against?: string[];
  risks?: string[];
  disputed_areas?: { criterion_name: string; description: string }[];
  needs_attention?: { feedback_id: string; original_text: string; reason: string }[];
  evidence_comments?: CriterionBreakdown[];
  llm_model_version?: string;
}

export interface User {
  user_id: string;
  full_name: string;
  email: string;
  role: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  user_id: string;
  role: string;
  full_name: string;
}
