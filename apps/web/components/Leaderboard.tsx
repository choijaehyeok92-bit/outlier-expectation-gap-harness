'use client';

import Link from 'next/link';
import { money, show, type RunRow } from '@/lib/api';

const COLUMNS = [
  'Rank', 'Ticker', 'Company', 'Market', 'Source', 'MCap', 'Core', 'Ex-Val', 'Archetype',
  'EV', 'AS', 'FS', 'MT', 'Veto', 'P/Base', 'Deep Dive',
];

function domain(row: RunRow, key: string) {
  return show(row.domain_scores?.[key] ?? null);
}

export function Leaderboard({ rows, deepDiveByTicker }: { rows: RunRow[]; deepDiveByTicker?: Record<string, string> }) {
  if (rows.length === 0) {
    return <p className="muted text-sm">조건을 만족한 종목이 없다.</p>;
  }
  return (
    <div className="card overflow-x-auto">
      <table>
        <thead>
          <tr>{COLUMNS.map((c) => <th key={c}>{c}</th>)}</tr>
        </thead>
        <tbody>
          {rows.map((row, index) => {
            const deepDiveId = deepDiveByTicker?.[row.ticker];
            return (
              <tr key={row.run_id}>
                <td className="muted">{index + 1}</td>
                <td>
                  <Link href={`/companies/${encodeURIComponent(row.ticker)}`}>{row.ticker}</Link>
                </td>
                <td>{row.company_name ?? '미상'}</td>
                <td><span className="chip">{row.jurisdiction}</span></td>
                <td>
                  <span className="chip" title={row.has_harness_run
                    ? '하네스가 분석한 기업. 점수·Veto는 하네스가 기록한 값이다.'
                    : '정량 지표만 있는 기업. 하네스 판정이 없으므로 점수·Veto 칸은 비어 있다.'}>
                    {row.has_harness_run === false ? '정량만' : 'Harness'}
                  </span>
                </td>
                <td>{money(row.market_cap_usd)}</td>
                <td>{show(row.core_score)}</td>
                <td>{show(row.ex_valuation_score)}</td>
                <td>{row.archetype ?? '미상'}</td>
                <td>{domain(row, 'expectation_valuation')}</td>
                <td>{domain(row, 'asymmetry')}</td>
                <td>{domain(row, 'financial_survival')}</td>
                <td>{domain(row, 'moat_trajectory')}</td>
                <td>{row.hard_veto_status ?? '미상'}</td>
                <td>{show(row.price_to_base_value)}</td>
                <td>
                  {deepDiveId ? (
                    <Link href={`/reports/${encodeURIComponent(deepDiveId)}`}>보고서</Link>
                  ) : (
                    <Link href={`/runs/${encodeURIComponent(row.run_id)}`}>계획</Link>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
