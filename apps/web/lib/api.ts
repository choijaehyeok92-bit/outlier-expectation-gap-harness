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
  warehouse: () => request<WarehouseSummary>('/api/warehouse'),
  universe: () => request<Universe>('/api/universe'),
  runs: () => request<RunRow[]>('/api/runs'),
  run: (id: string) => request<RunRow>(`/api/runs/${encodeURIComponent(id)}`),
  company: (ticker: string) => request<Company>(`/api/companies/${encodeURIComponent(ticker)}`),
  fields: () => request<FieldRow[]>('/api/screen/fields'),
  parse: (body: ParseBody) => request<ScreeningSpec>('/api/screen/parse', { method: 'POST', body: JSON.stringify(body) }),
  screen: (body: ScreenBody) => request<ScreenRecord>('/api/screen/run', { method: 'POST', body: JSON.stringify(body) }),
  screenProviders: () => request<ProviderCatalogue>('/api/screen/providers'),
  screenRuns: () => request<ScreenRunSummary[]>('/api/screen/runs'),
  screenRun: (id: string) => request<ScreenRecord>(`/api/screen/runs/${encodeURIComponent(id)}`),
  deepDives: () => request<DeepDiveSummary[]>('/api/deep-dive'),
  deepDive: (id: string) => request<{ report: DeepDiveReport; plan: DeepDivePlan | null }>(`/api/deep-dive/${encodeURIComponent(id)}`),
  deepDivePlan: (runId: string, userRequested: boolean) =>
    request<DeepDivePlan>('/api/deep-dive/plan', { method: 'POST', body: JSON.stringify({ run_id: runId, user_requested: userRequested }) }),
  deepDiveRun: (runId: string, userRequested: boolean, provider = 'fixture', model?: string) =>
    request<{ deep_dive_id: string }>('/api/deep-dive/run', {
      method: 'POST',
      body: JSON.stringify({ run_id: runId, user_requested: userRequested, provider, model }),
    }),
  report: (id: string) => request<DeepDiveReport>(`/api/reports/${encodeURIComponent(id)}`),
  monitoring: (tickers?: string) =>
    request<MonitoringPortfolio>(`/api/monitoring${tickers ? `?tickers=${encodeURIComponent(tickers)}` : ''}`),
  monitoringCompany: (ticker: string) =>
    request<MonitoringSnapshot>(`/api/monitoring/${encodeURIComponent(ticker)}`),
  monitoringDrift: (ticker: string) =>
    request<DriftSeries>(`/api/monitoring/${encodeURIComponent(ticker)}/drift`),
  marketProviders: () => request<MarketCatalogue>('/api/market/providers'),
  marketCoverage: (asOf: string) =>
    request<MarketCoverage>(`/api/market/coverage?as_of_date=${encodeURIComponent(asOf)}`),
  marketFetch: (body: MarketFetchBody) =>
    request<MarketFetchResult>('/api/market/fetch', { method: 'POST', body: JSON.stringify(body) }),
  regulatorCredentials: () => request<{ credentials: RegulatorCredential[] }>('/api/universe/credentials'),
  universeSync: (body: UniverseSyncBody) =>
    request<UniverseSyncResult>('/api/universe/sync', { method: 'POST', body: JSON.stringify(body) }),
  candidates: (asOf: string, markets: string, limit: number, includeIngested: boolean) =>
    request<CandidateList>(`/api/universe/candidates?as_of_date=${encodeURIComponent(asOf)}`
      + `&markets=${encodeURIComponent(markets)}&limit=${limit}`
      + `&include_ingested=${includeIngested}`),
  ingestPacks: (body: PackIngestBody) =>
    request<PackIngestResult>('/api/ingest/packs', { method: 'POST', body: JSON.stringify(body) }),
  pipeline: (asOf: string) => request<PipelineStatus>(`/api/pipeline/status?as_of_date=${encodeURIComponent(asOf)}`),
  pipelineProviders: () => request<StageProviders>('/api/pipeline/providers'),
  warehouseBuild: (asOf: string) =>
    request<WarehouseBuildResult>('/api/warehouse/build', { method: 'POST', body: JSON.stringify({ as_of_date: asOf }) }),
  triage: (body: Record<string, unknown>) =>
    request<StageRunResult>('/api/harness/triage', { method: 'POST', body: JSON.stringify(body) }),
  fullHarness: (body: Record<string, unknown>) =>
    request<StageRunResult>('/api/harness/full', { method: 'POST', body: JSON.stringify(body) }),
};

/** A status the monitoring layer computed. It is never a recommendation. */
export type MonitorStatus =
  | 'ok' | 'warning' | 'thesis_break' | 'stale' | 'unknown'
  | 'unchecked' | 'not_triggered' | 'triggered' | 'not_machine_checkable';

export interface MonitorSummary {
  items: number;
  by_status: Record<string, number>;
  review_required: number;
  observed: number;
  never_observed: number;
  not_machine_checkable: number;
}

export interface MonitorItem {
  watch_id: string;
  kind: 'kpi' | 'falsifier';
  name: string;
  source_kind: string;
  source_ref: string | null;
  cadence: string | null;
  status: MonitorStatus;
  reason: string | null;
  review_required: boolean;
  observations: number;
  observed_value?: number | null;
  days_overdue?: number | null;
  checked_levels: string[];
  breached_levels: string[];
  latest_observation: Record<string, unknown> | null;
}

export interface MonitoringSnapshot {
  ticker: string;
  run_id: string;
  analysis_as_of_date: string | null;
  evaluated_as_of: string;
  deep_dive_id: string | null;
  summary: MonitorSummary;
  review_required: { watch_id: string; kind: string; name: string; status: string; reason: string | null }[];
  authority: { may: string[]; may_not: string[]; statement: string };
  items: MonitorItem[];
  integrity: { lines: number; unreadable: unknown[]; superseded: unknown[] };
}

export interface MonitoringPortfolio {
  evaluated_as_of?: string;
  companies: number;
  needing_review?: number;
  rows: { ticker: string; run_id: string; analysis_as_of_date: string | null; summary: MonitorSummary;
          review_required: { name: string; status: string }[] }[];
  unreadable: { ticker: string; reason: string }[];
  note?: string;
  authority?: { may: string[]; may_not: string[]; statement: string };
}

export interface DriftStep {
  from_run: string;
  to_run: string;
  from_as_of: string | null;
  to_as_of: string | null;
  comparable: boolean;
  not_comparable_reason: string | null;
  policy_changes: Record<string, { before: unknown; after: unknown }>;
  changes: { field: string; before: unknown; after: unknown; delta: number | null; attributable_to_company: boolean }[];
}

export interface DriftSeries {
  ticker: string;
  runs: number;
  comparable_steps: number;
  matched_by: string[];
  points: Record<string, unknown>[];
  steps: DriftStep[];
  reading_note: string;
}

export interface Health { status: string; backends: string[]; runs: number; llm_provider_default: string }

export interface WarehouseSummary {
  as_of_date: string;
  built_at_utc: string;
  companies: number;
  tickers: string[];
  coverage: Record<string, { computed: number; missing: number }>;
  failures: { ticker: string | null; error: string }[];
}

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
  has_harness_run?: boolean;
  has_warehouse_metrics?: boolean;
  field_sources?: Record<string, string>;
  consolidation_basis?: string | null;
  anchor_fiscal_year?: number | null;
  warehouse_unavailable?: string[];
  warehouse_requires_review?: string[];
  market_cap?: number | null;
  revenue_ttm?: number | null;
  revenue_growth_yoy?: number | null;
  revenue_cagr_3y?: number | null;
  gross_margin?: number | null;
  operating_margin?: number | null;
  owner_fcf_ttm?: number | null;
  owner_fcf_margin?: number | null;
  owner_fcf_per_share?: number | null;
  net_cash?: number | null;
  debt_to_ocf?: number | null;
  sbc_to_revenue?: number | null;
  rnd_to_revenue?: number | null;
  capex_to_ocf?: number | null;
  price_to_owner_fcf?: number | null;
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

export interface BackendSummary {
  rows: number;
  with_harness_run: number;
  with_warehouse_metrics: number;
  warehouse_only: number;
  backends: string[];
}

export interface ScreenRecord {
  screen_run_id: string;
  backends?: BackendSummary;
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

export interface ParseBody {
  text: string;
  as_of_date: string;
  provider?: string;
  model?: string;
  fx_rates?: Record<string, number>;
}
export interface ScreenBody {
  text?: string;
  spec?: ScreeningSpec;
  as_of_date?: string;
  provider?: string;
  model?: string;
  fx_rates?: Record<string, number>;
  persist?: boolean;
}

/**
 * A parser the screener can use.
 *
 * `configured` says whether the server holds the credential. It never says
 * what the credential is — the key stays on the backend and no field here
 * carries it, or a prefix of it, or its length.
 *
 * `default_model` is a starting point, not a catalogue. The backend holds no
 * list of what a vendor offers, so any model string is passed through and the
 * vendor decides whether it exists.
 */
export interface ProviderOption {
  name: string;
  kind: 'deterministic' | 'offline' | 'api';
  spends_money: boolean;
  env_var: string | null;
  default_model: string | null;
  configured: boolean;
  note: string;
}

export interface ProviderCatalogue { default: string; providers: ProviderOption[] }

/**
 * US quote vendors. `configured` says a key exists; it never says what it is,
 * and no field here ever carries one.
 */
export interface MarketProviderOption {
  name: string;
  label: string;
  env_var: string | null;
  configured: boolean;
  bulk: boolean;
  signup: string | null;
  note: string | null;
  auth_note: string | null;
  is_default: boolean;
}

export interface MarketCatalogue {
  default: string;
  jurisdiction: string;
  providers: MarketProviderOption[];
  rejected: Record<string, string>;
  shares_note: string | null;
}

export interface MarketPricedRow {
  ticker: string;
  observed_date: string;
  close: number | null;
  shares_outstanding: number | null;
}

export interface MarketCoverage {
  as_of_date: string;
  market_root: string;
  packs: number;
  priced: number;
  unpriced: string[];
  without_shares: string[];
  older_than_cutoff: MarketPricedRow[];
  rows: MarketPricedRow[];
}

export interface MarketFetchBody {
  as_of_date: string;
  provider?: string;
  scope?: 'packs' | 'universe' | 'all';
  tickers?: string[];
  dry_run?: boolean;
}

export interface MarketFetchResult {
  as_of_date: string;
  session_date: string | null;
  sessions_tried: string[];
  provider: string;
  selection_reason: string;
  vendor_rows: number;
  requested: number;
  written_count: number;
  written: { ticker: string; date: string; close: number; shares_outstanding: number | null; shares_as_of: string | null }[];
  missing_price: string[];
  missing_shares_outstanding: string[];
  wrote_files: boolean;
  note: string;
}

/**
 * Regulator credentials. SEC wants a contact in its User-Agent rather than a
 * key; either way `configured` is a boolean and the value never leaves the
 * server.
 */
export interface RegulatorCredential {
  market: 'US' | 'KR';
  regulator: 'SEC' | 'DART';
  env_var: string;
  configured: boolean;
  note: string;
  signup: string;
}

export interface UniverseSyncBody {
  markets: ('US' | 'KR')[];
  as_of_date?: string;
  enrich_limit?: number;
  refresh_corp_codes?: boolean;
}

export interface UniverseSummary {
  total: number;
  included: number;
  excluded: number;
  requires_review: number;
  by_exchange: Record<string, number>;
  by_security_type: Record<string, number>;
  excluded_by_reason: Record<string, number>;
}

export interface UniverseSyncResult {
  as_of_date: string | null;
  synced_at_utc: string;
  summary: UniverseSummary;
  markets: Record<string, UniverseSummary>;
  errors: Record<string, string>;
  enrich_limit: number;
  enrich_limit_note?: string;
  path: string;
}

/**
 * One listing considered for ingest. `dollar_volume` decides where the next
 * regulator call goes and nothing else — it is not a score, and a listing
 * without one is unranked rather than ranked last.
 */
export interface Candidate {
  ticker: string;
  company_name: string | null;
  exchange: string | null;
  currency: string | null;
  jurisdiction: 'US' | 'KR';
  requires_review: boolean;
  already_ingested: boolean;
  quoted_as?: string;
  close?: number;
  volume?: number;
  dollar_volume?: number;
  rank?: number;
  reason_unranked?: string;
}

export interface CandidateList {
  as_of_date: string;
  session_date: string | null;
  sessions_tried: string[];
  markets: string[];
  ranked_by: string | null;
  quote_source: 'vendor' | 'local_csv' | null;
  ranked_by_note: string | null;
  is_not_evidence: string | null;
  quote_error: string | null;
  universe_size: number;
  already_ingested: number;
  ranked_count: number;
  unranked_count: number;
  limit: number;
  candidates: Candidate[];
  unranked: Candidate[];
}

export interface PackIngestBody {
  tickers: string[];
  market: 'US' | 'KR';
  as_of_date: string;
  force?: boolean;
}

export interface PackResult {
  ticker: string;
  company_name?: string | null;
  status: 'ok' | 'exists' | 'validation_errors' | 'failed';
  facts?: number;
  documents?: number;
  requires_review?: number;
  validation_errors?: string[];
  error?: string;
  path?: string;
  note?: string;
}

export interface PackIngestResult {
  as_of_date: string;
  market: string;
  requested: number;
  written: number;
  skipped_existing: number;
  failed: number;
  pack_dir: string;
  results: PackResult[];
}

/**
 * One step of the funnel. `spends_money` is the whole reason this type exists:
 * the free steps may be chained behind one click and the paid ones may not.
 */
export interface PipelineStep {
  id: string;
  title: string;
  what: string;
  action: string;
  page: string;
  spends_money: boolean;
  calls_per_company?: number;
  state: 'done' | 'partial' | 'todo' | 'blocked';
  count: number;
  detail: string;
  blocked: string | null;
  latest_id?: string | null;
  eligible?: string[];
  synced_at_utc?: string | null;
}

export interface PipelineCredential {
  market: string;
  regulator: string;
  env_var: string | null;
  configured: boolean;
  note: string | null;
  signup: string | null;
}

export interface PipelineStatus {
  as_of_date: string;
  next_step: string | null;
  free_steps: string[];
  credentials: PipelineCredential[];
  money_note: string;
  steps: PipelineStep[];
}

export interface WarehouseBuildResult {
  as_of_date: string;
  companies: number;
  tickers: string[];
  failures: unknown[];
  market_snapshots_attached: number;
  path: string;
}

/**
 * A triage or full-harness batch. A dry run reports the selection and stops —
 * which is the default, because both stages call a model per agent per
 * company and starting one is an explicit act.
 */
export interface StageCandidate {
  run_id?: string;
  ticker?: string;
  rank?: number;
  eligible?: boolean;
  reason?: string;
  core_score?: number | null;
  hard_veto_status?: string | null;
  status?: string;
}

export interface StageRunResult {
  as_of_date?: string;
  stage?: string;
  dry_run?: boolean;
  eligible?: StageCandidate[];
  not_eligible?: StageCandidate[];
  results?: StageCandidate[];
  summary?: Record<string, unknown>;
  [key: string]: unknown;
}

/**
 * What a paid stage may be run with. Each stage has its own offline stand-in —
 * `placeholder` analyses nothing, `fixture` replays a recording — and it is
 * listed first and chosen by default, so opening the page is not one click
 * away from spending money.
 */
export interface StageProviderOption {
  name: string;
  kind: 'offline' | 'api';
  spends_money: boolean;
  env_var: string | null;
  default_model: string | null;
  note: string;
  configured: boolean;
}

export interface StageProviderSet {
  title: string;
  calls_per_company: number;
  default: string;
  options: StageProviderOption[];
}

export interface StageProviders {
  stages: Record<string, StageProviderSet>;
  note: string;
  model_note: string;
}

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
