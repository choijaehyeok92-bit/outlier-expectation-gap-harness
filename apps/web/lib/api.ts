/**
 * The only place the browser talks to the backend.
 *
 * Nothing here computes anything. Every number this app shows was written by
 * the harness and read back through the API; the UI's job is to lay it out and
 * to be honest about what is missing. A null is rendered as unknown, never as
 * zero and never as a dash that could be mistaken for one.
 */
export const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? 'http://localhost:8000';

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    cache: 'no-store',
  });
  if (!response.ok) {
    const body = await response.text();
    let detail = body;
    try {
      detail = JSON.parse(body).detail ?? body;
    } catch {
      /* the body was not JSON; show it as it came */
    }
    throw new ApiError(detail || response.statusText, response.status);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Health>('/api/health'),
  universe: () => request<Universe>('/api/universe'),
  runs: () => request<RunRow[]>('/api/runs'),
  run: (id: string) => request<RunRow>(`/api/runs/${encodeURIComponent(id)}`),
  company: (ticker: string) => request<Company>(`/api/companies/${encodeURIComponent(ticker)}`),
  fields: () => request<FieldRow[]>('/api/screen/fields'),
  parse: (body: ParseBody) => request<ScreeningSpec>('/api/screen/parse', { method: 'POST', body: JSON.stringify(body) }),
  screen: (body: ScreenBody) => request<ScreenRecord>('/api/screen/run', { method: 'POST', body: JSON.stringify(body) }),
  screenRuns: () => request<ScreenRunSummary[]>('/api/screen/runs'),
  screenRun: (id: string) => request<ScreenRecord>(`/api/screen/runs/${encodeURIComponent(id)}`),
  deepDives: () => request<DeepDiveSummary[]>('/api/deep-dive'),
  deepDive: (id: string) => request<{ report: DeepDiveReport; plan: DeepDivePlan | null }>(`/api/deep-dive/${encodeURIComponent(id)}`),
  deepDivePlan: (runId: string, userRequested: boolean) =>
    request<DeepDivePlan>('/api/deep-dive/plan', { method: 'POST', body: JSON.stringify({ run_id: runId, user_requested: userRequested }) }),
  deepDiveRun: (runId: string, userRequested: boolean) =>
    request<{ deep_dive_id: string }>('/api/deep-dive/run', { method: 'POST', body: JSON.stringify({ run_id: runId, user_requested: userRequested, provider: 'fixture' }) }),
  report: (id: string) => request<DeepDiveReport>(`/api/reports/${encodeURIComponent(id)}`),
};

export interface Health { status: string; backend: string; runs: number; llm_provider_default: string }

export interface Universe {
  backend: string;
  runs: number;
  by_jurisdiction: Record<string, number>;
  as_of_dates: string[];
  latest_as_of_date: string | null;
  note: string;
  companies: [string, string | null, string][];
}

export interface RunRow {
  run_id: string;
  ticker: string;
  company_name: string | null;
  jurisdiction: string;
  exchange: string | null;
  currency: string | null;
  as_of_date: string | null;
  market_cap_usd: number | null;
  core_score: number | null;
  ex_valuation_score: number | null;
  classification: string | null;
  archetype: string | null;
  hard_veto_status: string | null;
  ic_state: string | null;
  position_range: string | null;
  price_to_base_value: number | null;
  early_exit: boolean;
  full_harness_complete: boolean;
  domain_scores?: Record<string, number | null>;
  axis_scores?: Record<string, number | null>;
  dilution_watch_status?: string | null;
  current_price?: number | null;
  triage_complete?: boolean;
  mechanical_pre_ic_state?: string | null;
  revenue_cagr_next_3y?: number | null;
  result_source?: string | null;
  result_sha256?: string | null;
  decision_policy_version?: string | null;
  valuation_status?: string | null;
  coverage_weight?: number | null;
  net_cash_per_share?: number | null;
  strategy_version?: string | null;
  input_snapshot_sha256?: string | null;
  frozen?: boolean;
  match_explain?: ClauseExplain[];
}

export interface ClauseExplain {
  field: string;
  operator: string;
  threshold: unknown;
  value: unknown;
  missing: boolean;
  result: boolean | null;
}

export interface Company {
  ticker: string;
  company_name: string | null;
  jurisdiction: string;
  currency: string | null;
  latest: RunRow;
  harness_history: RunRow[];
  deep_dives: DeepDiveSummary[];
}

export interface FieldRow {
  id: string; group: string; dtype: string; unit: string;
  backends: string[]; requires_harness_run: boolean; available: boolean; note: string | null;
}

export interface UnresolvedCondition { text: string; reason: string; suggested_field: string | null; detail: string | null }

export interface Filter { field: string; operator: string; value: unknown; unit?: string | null; currency?: string | null; rationale?: string | null; origin_text?: string | null }

export interface FilterGroup { op: 'and' | 'or'; clauses: (Filter | FilterGroup)[] }

export interface ScreeningSpec {
  schema_version: string;
  spec_id?: string;
  as_of_date: string;
  source?: { kind: string; text?: string; parser?: { provider: string; model: string | null } };
  universe: { jurisdictions?: string[]; exchanges?: string[]; tickers?: string[] };
  filters: FilterGroup;
  sort: { field: string; direction: string }[];
  limit: number;
  missing_policy: string;
  requires_harness_run: boolean;
  unresolved_conditions: UnresolvedCondition[];
  fx_rates?: Record<string, { per_usd: number; source: string }>;
}

export interface ScreenRecord {
  screen_run_id: string;
  as_of_date: string;
  backend: string;
  spec: ScreeningSpec;
  summary: {
    considered: number;
    matched_count: number;
    missing_policy: string;
    excluded_missing_data: { ticker: string; run_id: string; missing_fields: string[] }[];
    excluded_post_cutoff: { ticker: string; run_id: string; as_of_date: string }[];
    unresolved_conditions: UnresolvedCondition[];
    requires_harness_run: boolean;
  };
  results: RunRow[];
  needs_review: RunRow[];
  provenance: { code_commit_sha: string; created_at_utc: string };
}

export interface ScreenRunSummary { screen_run_id: string; as_of_date: string; matched_count: number; query: string | null; created_at_utc: string }

export interface DeepDiveSummary {
  deep_dive_id: string; ticker: string; company_name: string | null; jurisdiction: string;
  as_of_date: string; created_at_utc: string; harness_run: string;
  red_team_overall: string | null; agreement_with_harness: string | null;
}

export interface Assessment {
  assessment: string; direction: string; confidence: number; thesis: string;
  supporting_evidence: string[]; contradicting_evidence: string[];
  unknowns: string[]; falsifiers: string[];
}

export interface EvidenceItem {
  evidence_id: string; claim: string; value?: unknown; unit?: string | null;
  source: string; source_origin: string; source_type?: string | null; source_tier: number;
  publication_date: string; period: string; as_of_date: string;
  fact_or_estimate: string; economic_driver: string; confidence: number;
  verified_fact_refs: string[]; supports?: string;
}

export interface DeepDiveReport {
  schema_version: string;
  metadata: {
    deep_dive_id: string; ticker: string; company_name: string | null; jurisdiction: string;
    as_of_date: string; created_at_utc: string;
    harness_run: { run_id: string; aggregate_sha256: string; strategy_version: string | null };
    provenance: { code_commit_sha: string; stages: { stage: string; provider: string; model: string | null }[] };
  };
  harness_snapshot: Record<string, unknown>;
  executive_summary: string;
  investment_question: { id: string; question: string; answer: string; supporting_evidence: string[]; unknowns?: string[]; confidence: number }[];
  evidence: EvidenceItem[];
  business_model: Assessment; industry: Assessment; customer_product: Assessment;
  moat: Assessment; moat_trajectory: Assessment; growth_runway: Assessment;
  unit_economics: Assessment; per_share_economics: Assessment; financial_quality: Assessment;
  management: Assessment; capital_allocation: Assessment; technology_disruption: Assessment;
  risk_analysis: Assessment; valuation_interpretation: Assessment;
  bull_case: NarrativeCase; base_case: NarrativeCase; bear_case: NarrativeCase;
  red_team: {
    overall: string; reason: string; supporting_harness: string[]; contradicting_harness: string[];
    domains_with_material_disagreement: string[];
    attack_paths: { vector: string; thesis_break_mechanism: string; evidence: string[]; assessed_likelihood: string; strongest_counterargument: string | null }[];
  };
  harness_comparison: {
    strongest_supporting_evidence: string[]; strongest_contradicting_evidence: string[];
    possible_harness_overstatement: string[]; possible_harness_blind_spots: string[];
    unresolved_contradictions: string[];
    by_domain: { domain: string; harness_score: number | null; qualitative_assessment: string; agreement: string; note: string | null }[];
  };
  falsifiers: { statement: string; observable: string; would_break: string }[];
  monitoring_kpis: {
    name: string; why_it_matters: string; current_value: string | number | null;
    direction_required: string; warning_threshold: string | number;
    thesis_break_threshold: string | number; cadence: string; source: string;
  }[];
  remaining_unknowns: string[];
  evidence_quality: { tier_counts: Record<string, number>; primary_share: number; independent_origins: number; concerns: string[] };
  final_synthesis: { thesis: string; what_must_be_true: string[]; what_would_change_our_mind: string[]; agreement_with_harness: string; decision_authority: string };
}

export interface NarrativeCase { narrative: string; key_drivers: string[]; evidence: string[]; what_must_be_true: string[] }

export interface DeepDivePlan {
  ticker: string; company_name: string | null; jurisdiction: string; as_of_date: string;
  harness_run: { run_id: string; aggregate_sha256: string };
  selection: { eligible: boolean; route: string; reasons: string[] };
  harness_snapshot: Record<string, unknown>;
  domains: { id: string; title: string; prompt_focus: string; harness_reference: { domain: string | null; score: number | null } }[];
  local_evidence: { path: string; exists: boolean; sha256: string | null }[];
  questions: { question_id: string; question: string; domain: string | null; origin: string }[];
  red_team_mandate: string[];
}

export interface ParseBody { text: string; as_of_date: string; provider?: string; fx_rates?: Record<string, number> }
export interface ScreenBody { text?: string; spec?: ScreeningSpec; as_of_date?: string; fx_rates?: Record<string, number>; persist?: boolean }

/** A missing value is unknown, not zero. The UI says so everywhere. */
export function show(value: unknown, digits = 2): string {
  if (value === null || value === undefined) return '미상';
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(digits);
  if (typeof value === 'boolean') return value ? 'yes' : 'no';
  return String(value);
}

export function money(value: number | null | undefined): string {
  if (value === null || value === undefined) return '미상';
  const units: [number, string][] = [[1e12, 'T'], [1e9, 'B'], [1e6, 'M']];
  for (const [size, suffix] of units) {
    if (Math.abs(value) >= size) return `$${(value / size).toFixed(1)}${suffix}`;
  }
  return `$${value.toFixed(0)}`;
}
