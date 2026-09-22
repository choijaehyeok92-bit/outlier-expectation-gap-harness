'use client';

import Link from 'next/link';
import { use, useEffect, useState } from 'react';
import { api, show, type DeepDivePlan, type DeepDiveReport } from '@/lib/api';

/**
 * The research side of a deep dive: what was planned, what evidence came back,
 * and where the Red Team disagreed. The finished argument lives at /reports.
 */
export default function DeepDivePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [data, setData] = useState<{ report: DeepDiveReport; plan: DeepDivePlan | null } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tier, setTier] = useState<string>('all');

  useEffect(() => {
    api.deepDive(id).then(setData).catch((e) => setError(String(e.message)));
  }, [id]);

  if (error) return <div className="card p-4 text-sm">{error}</div>;
  if (!data) return <p className="muted">불러오는 중…</p>;

  const { report, plan } = data;
  const evidence = tier === 'all' ? report.evidence : report.evidence.filter((e) => String(e.source_tier) === tier);
  const tiers = Array.from(new Set(report.evidence.map((e) => String(e.source_tier)))).sort();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Deep Dive — {report.metadata.ticker}</h1>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span className="chip">{id}</span>
          <span className="chip">기준일 {report.metadata.as_of_date}</span>
          <Link href={`/reports/${encodeURIComponent(id)}`} className="chip no-underline">최종 보고서 →</Link>
        </div>
      </div>

      {plan && (
        <section className="card p-4">
          <h2 className="text-sm font-medium">계획</h2>
          <div className="mt-2 flex flex-wrap gap-2 text-xs">
            <span className="chip">route {plan.selection.route}</span>
            <span className="chip">도메인 {plan.domains.length}</span>
            <span className="chip">질문 {plan.questions.length}</span>
            <span className="chip">로컬 증거 {plan.local_evidence.filter((e) => e.exists).length}</span>
          </div>
          <ul className="muted mt-2 list-disc pl-5 text-xs">
            {plan.selection.reasons.map((r) => <li key={r}>{r}</li>)}
          </ul>
        </section>
      )}

      <section className="card p-4">
        <h2 className="text-sm font-medium">단계별 실행 기록</h2>
        <table className="mt-3">
          <thead><tr><th>Stage</th><th>Provider</th><th>Model</th></tr></thead>
          <tbody>
            {report.metadata.provenance.stages.map((s) => (
              <tr key={s.stage}><td>{s.stage}</td><td>{s.provider}</td><td>{s.model ?? '미상'}</td></tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card p-4">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm font-medium">증거 ({evidence.length}/{report.evidence.length})</h2>
          <div className="flex gap-2 text-xs">
            {['all', ...tiers].map((t) => (
              <button key={t} onClick={() => setTier(t)} className="chip" style={tier === t ? { color: 'var(--accent)' } : undefined}>
                {t === 'all' ? '전체' : `tier ${t}`}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-3 overflow-x-auto">
          <table>
            <thead>
              <tr><th>ID</th><th>주장</th><th>Tier</th><th>종류</th><th>공개일</th><th>기간</th><th>출처</th></tr>
            </thead>
            <tbody>
              {evidence.map((item) => (
                <tr key={item.evidence_id}>
                  <td className="whitespace-nowrap">{item.evidence_id}</td>
                  <td>{item.claim}</td>
                  <td>{item.source_tier}</td>
                  <td>{item.fact_or_estimate}</td>
                  <td className="whitespace-nowrap">{item.publication_date}</td>
                  <td className="whitespace-nowrap">{item.period}</td>
                  <td className="muted break-all">{item.source}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-medium">Red Team 요약</h2>
        <div className="mt-2 text-sm">종합 판정: {report.red_team.overall}</div>
        <p className="mt-2 text-sm whitespace-pre-wrap">{report.red_team.reason}</p>
        <div className="muted mt-2 text-xs">
          실질적 불일치 도메인: {report.red_team.domains_with_material_disagreement.join(', ') || '없음'}
        </div>
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-medium">증거 품질</h2>
        <div className="muted mt-2 text-xs">
          1차 자료 비중 {show(report.evidence_quality.primary_share)} · 독립 출처{' '}
          {report.evidence_quality.independent_origins}
        </div>
      </section>
    </div>
  );
}
