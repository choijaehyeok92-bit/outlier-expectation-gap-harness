'use client';

import Link from 'next/link';
import { use, useEffect, useState } from 'react';
import { api, money, show, type Company } from '@/lib/api';

export default function CompanyPage({ params }: { params: Promise<{ ticker: string }> }) {
  const { ticker } = use(params);
  const [company, setCompany] = useState<Company | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.company(ticker).then(setCompany).catch((e) => setError(String(e.message)));
  }, [ticker]);

  if (error) return <div className="card p-4 text-sm">{error}</div>;
  if (!company) return <p className="muted">불러오는 중…</p>;

  const latest = company.latest;
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">
          {company.ticker} <span className="muted text-base">{company.company_name ?? ''}</span>
        </h1>
        <div className="mt-2 flex flex-wrap gap-2 text-xs">
          <span className="chip">{company.jurisdiction}</span>
          <span className="chip">{company.currency ?? '통화 미상'}</span>
          <span className="chip">최신 기준일 {latest.as_of_date}</span>
        </div>
      </div>

      <section className="grid gap-4 sm:grid-cols-4">
        {[
          ['시가총액', money(latest.market_cap_usd)],
          ['현재가', show(latest.current_price ?? null)],
          ['주당 순현금', show(latest.net_cash_per_share ?? null)],
          ['Price / Base', show(latest.price_to_base_value)],
        ].map(([label, value]) => (
          <div key={label} className="card p-4">
            <div className="muted text-xs">{label}</div>
            <div className="mt-1 text-lg">{value}</div>
          </div>
        ))}
      </section>

      <section className="card overflow-x-auto">
        <div className="p-4 text-sm font-medium">하네스 실행 이력</div>
        <table>
          <thead>
            <tr><th>Run</th><th>기준일</th><th>Core</th><th>Ex-Val</th><th>Archetype</th><th>Veto</th><th>IC state</th><th>Policy</th></tr>
          </thead>
          <tbody>
            {company.harness_history.map((row) => (
              <tr key={row.run_id}>
                <td><Link href={`/runs/${encodeURIComponent(row.run_id)}`}>{row.run_id}</Link></td>
                <td>{row.as_of_date}</td>
                <td>{show(row.core_score)}</td>
                <td>{show(row.ex_valuation_score)}</td>
                <td>{row.archetype ?? '미상'}</td>
                <td>{row.hard_veto_status ?? '미상'}</td>
                <td>{row.ic_state ?? '미상'}</td>
                <td className="muted">{row.strategy_version ?? '미상'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card p-4">
        <div className="text-sm font-medium">Deep Dive 보고서</div>
        {company.deep_dives.length === 0 ? (
          <p className="muted mt-2 text-sm">아직 없다. run 화면에서 생성한다.</p>
        ) : (
          <ul className="mt-2 space-y-1 text-sm">
            {company.deep_dives.map((row) => (
              <li key={row.deep_dive_id}>
                <Link href={`/reports/${encodeURIComponent(row.deep_dive_id)}`}>{row.deep_dive_id}</Link>
                <span className="muted"> — Red Team {row.red_team_overall} · 하네스와 {row.agreement_with_harness}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
