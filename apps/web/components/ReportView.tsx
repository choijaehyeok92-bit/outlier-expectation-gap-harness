'use client';

import { useState } from 'react';
import { show, type Assessment, type DeepDiveReport, type EvidenceItem } from '@/lib/api';

const ASSESSMENT_KO: Record<string, string> = {
  strong: '강함', favorable: '우호적', mixed: '혼재', weak: '약함', critical: '치명적',
};
const DIRECTION_KO: Record<string, string> = {
  strengthening: '강화', stable: '유지', weakening: '약화', unclear: '불명확',
};
const SECTIONS: [keyof DeepDiveReport, string][] = [
  ['business_model', 'Business Model'], ['industry', 'Industry & Competitors'],
  ['customer_product', 'Customer & Product'], ['moat', 'Moat'],
  ['moat_trajectory', 'Moat Trajectory'], ['growth_runway', 'Growth Runway'],
  ['unit_economics', 'Unit Economics'], ['per_share_economics', 'Per-Share Economics'],
  ['financial_quality', 'Financial Quality'], ['management', 'Management & Governance'],
  ['capital_allocation', 'Capital Allocation'], ['technology_disruption', 'Technology / Disruption'],
  ['risk_analysis', 'Regulatory & Geopolitical Risk'], ['valuation_interpretation', 'Market Expectations'],
];

function EvidenceChips({ ids, evidence, tone }: { ids: string[]; evidence: Map<string, EvidenceItem>; tone: 'support' | 'against' }) {
  const [open, setOpen] = useState(false);
  if (ids.length === 0) return <span className="muted text-xs">없음</span>;
  return (
    <div>
      <button onClick={() => setOpen(!open)} className="chip" style={{ color: tone === 'support' ? 'var(--accent)' : '#fca5a5' }}>
        {tone === 'support' ? '지지' : '반박'} {ids.length}건 {open ? '접기' : '펼치기'}
      </button>
      {open && (
        <ul className="mt-2 space-y-2 text-xs">
          {ids.map((id) => {
            const item = evidence.get(id);
            return (
              <li key={id} className="card p-2">
                <div className="muted">{id} · tier {item?.source_tier ?? '?'} · {item?.fact_or_estimate ?? '?'} · {item?.publication_date ?? '?'}</div>
                <div className="mt-1">{item?.claim ?? '증거 목록에 없다'}</div>
                <div className="muted mt-1 break-all">{item?.source}</div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

function Section({ title, data, evidence }: { title: string; data: Assessment; evidence: Map<string, EvidenceItem> }) {
  return (
    <section className="card p-4">
      <div className="flex flex-wrap items-center gap-2">
        <h3 className="text-sm font-medium">{title}</h3>
        <span className="chip">{ASSESSMENT_KO[data.assessment] ?? data.assessment}</span>
        <span className="chip">{DIRECTION_KO[data.direction] ?? data.direction}</span>
        <span className="chip">확신도 {show(data.confidence)}</span>
      </div>
      <p className="mt-3 text-sm whitespace-pre-wrap">{data.thesis}</p>
      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <EvidenceChips ids={data.supporting_evidence} evidence={evidence} tone="support" />
        <EvidenceChips ids={data.contradicting_evidence} evidence={evidence} tone="against" />
      </div>
      {data.unknowns.length > 0 && (
        <div className="mt-3">
          <div className="muted text-xs">남은 미확인</div>
          <ul className="mt-1 list-disc pl-5 text-xs">{data.unknowns.map((u) => <li key={u}>{u}</li>)}</ul>
        </div>
      )}
      {data.falsifiers.length > 0 && (
        <div className="mt-2">
          <div className="muted text-xs">반증조건</div>
          <ul className="mt-1 list-disc pl-5 text-xs">{data.falsifiers.map((f) => <li key={f}>{f}</li>)}</ul>
        </div>
      )}
    </section>
  );
}

export function ReportView({ report }: { report: DeepDiveReport }) {
  const evidence = new Map(report.evidence.map((item) => [item.evidence_id, item]));
  const snapshot = report.harness_snapshot as Record<string, unknown>;
  const isFixture = report.metadata.provenance.stages.some((s) => s.provider === 'fixture');

  return (
    <div className="space-y-6">
      {isFixture && (
        <div className="card p-4 text-sm" style={{ borderColor: '#854d0e' }}>
          <strong>FIXTURE REPLAY — 실제 리서치가 아니다.</strong>
          <div className="muted mt-1 text-xs">
            이 보고서는 고정된 하네스 run의 기록을 딥다이브 계약 형태로 재생한 것이다. 외부 검증이나
            독립 조사로 읽어서는 안 된다.
          </div>
        </div>
      )}

      <div>
        <h1 className="text-2xl font-semibold">
          {report.metadata.ticker} <span className="muted text-base">{report.metadata.company_name ?? ''}</span>
        </h1>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span className="chip">기준일 {report.metadata.as_of_date}</span>
          <span className="chip">{report.metadata.jurisdiction}</span>
          <span className="chip">harness run {report.metadata.harness_run.run_id}</span>
          {report.metadata.provenance.stages.map((s) => (
            <span key={s.stage} className="chip">{s.stage}: {s.provider}{s.model ? `/${s.model}` : ''}</span>
          ))}
        </div>
      </div>

      <section className="card p-4">
        <h2 className="text-sm font-medium">Harness Snapshot (읽기 전용)</h2>
        <p className="muted mt-1 text-xs">딥다이브는 이 값을 수정하지 않는다.</p>
        <div className="mt-3 grid gap-3 sm:grid-cols-4">
          {(['core_score', 'ex_valuation_score', 'classification', 'archetype', 'hard_veto_status', 'ic_state', 'position_range', 'price_to_base_value'] as const).map((key) => (
            <div key={key}>
              <div className="muted text-xs">{key}</div>
              <div className="mt-1 text-sm">{show(snapshot[key])}</div>
            </div>
          ))}
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-medium">Executive Summary</h2>
        <p className="mt-2 text-sm whitespace-pre-wrap">{report.executive_summary}</p>
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">투자 10문답</h2>
        {report.investment_question.map((item) => (
          <div key={item.id} className="card p-4">
            <div className="text-sm font-medium">{item.id}. {item.question}</div>
            <p className="mt-2 text-sm whitespace-pre-wrap">{item.answer}</p>
            <div className="muted mt-2 text-xs">근거 {item.supporting_evidence.join(', ') || '없음'} · 확신도 {show(item.confidence)}</div>
          </div>
        ))}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">도메인 정성분석</h2>
        {SECTIONS.map(([key, title]) => (
          <Section key={String(key)} title={title} data={report[key] as Assessment} evidence={evidence} />
        ))}
      </section>

      <section className="grid gap-3 lg:grid-cols-3">
        {([['bull_case', 'Bull Case'], ['base_case', 'Base Case'], ['bear_case', 'Bear Case']] as const).map(([key, title]) => (
          <div key={key} className="card p-4">
            <h3 className="text-sm font-medium">{title}</h3>
            <p className="mt-2 text-sm whitespace-pre-wrap">{report[key].narrative}</p>
            <ul className="muted mt-2 list-disc pl-5 text-xs">
              {report[key].key_drivers.map((d) => <li key={d}>{d}</li>)}
            </ul>
          </div>
        ))}
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-medium">Red Team (독립 단계)</h2>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span className="chip">종합 {report.red_team.overall}</span>
          <span className="chip">공격 벡터 {report.red_team.attack_paths.length}개</span>
        </div>
        <p className="mt-3 text-sm whitespace-pre-wrap">{report.red_team.reason}</p>
        <div className="mt-3 space-y-3">
          {report.red_team.attack_paths.map((path) => (
            <div key={path.vector} className="card p-3">
              <div className="text-sm font-medium">{path.vector} <span className="muted text-xs">({path.assessed_likelihood})</span></div>
              <p className="mt-1 text-sm whitespace-pre-wrap">{path.thesis_break_mechanism}</p>
              <div className="muted mt-1 text-xs">근거 {path.evidence.join(', ') || '없음'}</div>
            </div>
          ))}
        </div>
        {report.red_team.domains_with_material_disagreement.length > 0 && (
          <div className="mt-3 text-sm">
            <div className="muted text-xs">하네스와 실질적으로 불일치하는 도메인</div>
            <ul className="mt-1 list-disc pl-5">{report.red_team.domains_with_material_disagreement.map((d) => <li key={d}>{d}</li>)}</ul>
          </div>
        )}
      </section>

      <section className="card overflow-x-auto p-4">
        <h2 className="text-sm font-medium">Harness 비교</h2>
        <table className="mt-3">
          <thead><tr><th>도메인</th><th>Harness</th><th>정성판정</th><th>일치</th><th>비고</th></tr></thead>
          <tbody>
            {report.harness_comparison.by_domain.map((row) => (
              <tr key={row.domain}>
                <td>{row.domain}</td>
                <td>{show(row.harness_score)}</td>
                <td>{ASSESSMENT_KO[row.qualitative_assessment] ?? row.qualitative_assessment}</td>
                <td>{row.agreement}</td>
                <td className="muted">{row.note ?? ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {([
            ['하네스를 지지하는 가장 강한 증거', report.harness_comparison.strongest_supporting_evidence],
            ['하네스를 반박하는 가장 강한 증거', report.harness_comparison.strongest_contradicting_evidence],
            ['과대평가했을 수 있는 지점', report.harness_comparison.possible_harness_overstatement],
            ['놓쳤을 수 있는 지점', report.harness_comparison.possible_harness_blind_spots],
            ['해소되지 않은 모순', report.harness_comparison.unresolved_contradictions],
          ] as const).map(([label, rows]) => (
            <div key={label}>
              <div className="muted text-xs">{label}</div>
              <ul className="mt-1 list-disc pl-5 text-xs">
                {rows.length ? rows.map((r) => <li key={r}>{r}</li>) : <li className="muted">없음</li>}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <section className="card overflow-x-auto p-4">
        <h2 className="text-sm font-medium">Monitoring KPIs</h2>
        <table className="mt-3">
          <thead>
            <tr><th>KPI</th><th>왜 중요한가</th><th>현재</th><th>방향</th><th>경고</th><th>thesis 폐기</th><th>주기</th></tr>
          </thead>
          <tbody>
            {report.monitoring_kpis.map((kpi, index) => (
              <tr key={`${kpi.name}-${index}`}>
                <td>{kpi.name}</td>
                <td className="muted">{kpi.why_it_matters}</td>
                <td>{show(kpi.current_value)}</td>
                <td>{kpi.direction_required}</td>
                <td>{show(kpi.warning_threshold)}</td>
                <td>{show(kpi.thesis_break_threshold)}</td>
                <td>{kpi.cadence}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="grid gap-3 sm:grid-cols-2">
        <div className="card p-4">
          <h2 className="text-sm font-medium">Falsifiers</h2>
          <ul className="mt-2 space-y-2 text-xs">
            {report.falsifiers.map((f, index) => (
              <li key={index}>
                <div>{f.statement}</div>
                <div className="muted">관측값: {f.observable} · 깨지는 것: {f.would_break}</div>
              </li>
            ))}
          </ul>
        </div>
        <div className="card p-4">
          <h2 className="text-sm font-medium">증거 품질</h2>
          <div className="muted mt-2 text-xs">
            tier 분포 {JSON.stringify(report.evidence_quality.tier_counts)} · 1차 비중{' '}
            {show(report.evidence_quality.primary_share)} · 독립 출처 {report.evidence_quality.independent_origins}
          </div>
          <ul className="mt-2 list-disc pl-5 text-xs">
            {report.evidence_quality.concerns.map((c) => <li key={c}>{c}</li>)}
          </ul>
          <div className="muted mt-3 text-xs">남은 미확인</div>
          <ul className="mt-1 list-disc pl-5 text-xs">
            {report.remaining_unknowns.map((u) => <li key={u}>{u}</li>)}
          </ul>
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-medium">최종 종합</h2>
        <p className="mt-2 text-sm whitespace-pre-wrap">{report.final_synthesis.thesis}</p>
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          <div>
            <div className="muted text-xs">반드시 성립해야 하는 것</div>
            <ul className="mt-1 list-disc pl-5 text-xs">{report.final_synthesis.what_must_be_true.map((x) => <li key={x}>{x}</li>)}</ul>
          </div>
          <div>
            <div className="muted text-xs">판단을 바꿀 관측값</div>
            <ul className="mt-1 list-disc pl-5 text-xs">{report.final_synthesis.what_would_change_our_mind.map((x) => <li key={x}>{x}</li>)}</ul>
          </div>
        </div>
        <p className="muted mt-3 text-xs">
          하네스와의 관계: {report.final_synthesis.agreement_with_harness} · {report.final_synthesis.decision_authority}
        </p>
      </section>
    </div>
  );
}
