'use client';

import Link from 'next/link';
import { use, useEffect, useState } from 'react';
import { api, money, show, type DeepDivePlan, type RunRow } from '@/lib/api';

const DOMAIN_LABEL: Record<string, string> = {
  structural_leadership: 'SL 산업 구조·리더십',
  customer_product: 'CP 고객·제품',
  moat_trajectory: 'MT 해자 궤적',
  reinvestment_fcf: 'RF 재투자·FCF',
  management_allocation: 'MA 경영진·자본배분',
  financial_survival: 'FS 재무 생존력',
  expectation_valuation: 'EV 기대·밸류에이션',
  asymmetry: 'AS 비대칭성',
};

export default function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [row, setRow] = useState<RunRow | null>(null);
  const [plan, setPlan] = useState<DeepDivePlan | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [deepDiveId, setDeepDiveId] = useState<string | null>(null);

  useEffect(() => {
    api.run(id).then(setRow).catch((e) => setError(String(e.message)));
  }, [id]);

  async function buildPlan(force: boolean) {
    setBusy(true);
    setError(null);
    try {
      setPlan(await api.deepDivePlan(id, force));
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }

  async function runDeepDive() {
    setBusy(true);
    setError(null);
    try {
      const result = await api.deepDiveRun(id, true);
      setDeepDiveId(result.deep_dive_id);
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }

  if (error && !row) return <div className="card p-4 text-sm">{error}</div>;
  if (!row) return <p className="muted">불러오는 중…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">
          {row.ticker} <span className="muted text-base">{row.company_name ?? ''}</span>
        </h1>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span className="chip">run {row.run_id}</span>
          <span className="chip">기준일 {row.as_of_date}</span>
          <span className="chip">{row.jurisdiction}</span>
          <span className="chip">{row.frozen ? 'frozen' : 'not frozen'}</span>
          {row.strategy_version && <span className="chip">policy v{row.strategy_version}</span>}
        </div>
      </div>

      <section className="grid gap-4 sm:grid-cols-4">
        {[
          ['Core score', show(row.core_score)],
          ['Ex-valuation', show(row.ex_valuation_score)],
          ['Archetype', row.archetype ?? '미상'],
          ['Hard Veto', row.hard_veto_status ?? '미상'],
          ['IC state', row.ic_state ?? '미상'],
          ['Position', row.position_range ?? '미상'],
          ['Price / Base', show(row.price_to_base_value)],
          ['시가총액', money(row.market_cap_usd)],
        ].map(([label, value]) => (
          <div key={label} className="card p-4">
            <div className="muted text-xs">{label}</div>
            <div className="mt-1 text-lg">{value}</div>
          </div>
        ))}
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-medium">도메인 점수</h2>
        <table className="mt-3">
          <thead><tr><th>도메인</th><th>점수</th></tr></thead>
          <tbody>
            {Object.entries(row.domain_scores ?? {}).map(([key, value]) => (
              <tr key={key}>
                <td>{DOMAIN_LABEL[key] ?? key}</td>
                <td>{show(value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {row.axis_scores && Object.keys(row.axis_scores).length > 0 && (
          <p className="muted mt-3 text-xs">
            독립 축 (100점에 합산되지 않는다): {Object.entries(row.axis_scores).map(([k, v]) => `${k} ${show(v)}`).join(' · ')}
          </p>
        )}
      </section>

      <section className="card space-y-3 p-4">
        <h2 className="text-sm font-medium">Deep Dive</h2>
        <div className="flex flex-wrap gap-3 text-sm">
          <button onClick={() => buildPlan(false)} disabled={busy} className="rounded-md px-3 py-1.5" style={{ border: '1px solid var(--border)' }}>
            계획 생성
          </button>
          <button onClick={() => buildPlan(true)} disabled={busy} className="rounded-md px-3 py-1.5" style={{ border: '1px solid var(--border)' }}>
            계획 생성 (정책 우회 요청)
          </button>
          <button onClick={runDeepDive} disabled={busy} className="rounded-md px-3 py-1.5" style={{ border: '1px solid var(--accent)', color: 'var(--accent)' }}>
            {busy ? '실행 중…' : '딥다이브 실행 (fixture)'}
          </button>
        </div>
        {error && <div className="text-sm" style={{ color: '#fca5a5' }}>{error}</div>}
        {deepDiveId && (
          <div className="text-sm">
            완료: <Link href={`/reports/${encodeURIComponent(deepDiveId)}`}>{deepDiveId}</Link>
          </div>
        )}
        {plan && (
          <div className="space-y-2 text-sm">
            <div>
              <span className="chip mr-2">route {plan.selection.route}</span>
              <span className="chip">{plan.selection.eligible ? 'eligible' : 'not eligible'}</span>
            </div>
            <ul className="muted list-disc pl-5 text-xs">
              {plan.selection.reasons.map((reason) => <li key={reason}>{reason}</li>)}
            </ul>
            <div className="muted text-xs">
              도메인 {plan.domains.length}개 · 질문 {plan.questions.length}개 · 로컬 증거{' '}
              {plan.local_evidence.filter((e) => e.exists).length}개
            </div>
          </div>
        )}
      </section>
    </div>
  );
}
