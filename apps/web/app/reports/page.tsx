'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api, type DeepDiveSummary } from '@/lib/api';

export default function ReportsPage() {
  const [rows, setRows] = useState<DeepDiveSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.deepDives().then(setRows).catch((e) => setError(String(e.message)));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Deep Dive Reports</h1>
        <p className="muted mt-2 text-sm">각 보고서는 immutable하다. 같은 기업을 다시 조사하면 새 보고서가 생긴다.</p>
      </div>
      {error && <div className="card p-4 text-sm" style={{ borderColor: '#7f1d1d' }}>{error}</div>}
      {rows.length === 0 ? (
        <p className="muted text-sm">아직 보고서가 없다. run 화면에서 딥다이브를 실행한다.</p>
      ) : (
        <div className="card overflow-x-auto">
          <table>
            <thead>
              <tr><th>ID</th><th>Ticker</th><th>Company</th><th>시장</th><th>기준일</th><th>Red Team</th><th>하네스와</th></tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.deep_dive_id}>
                  <td><Link href={`/reports/${encodeURIComponent(row.deep_dive_id)}`}>{row.deep_dive_id}</Link></td>
                  <td>{row.ticker}</td>
                  <td>{row.company_name ?? '미상'}</td>
                  <td><span className="chip">{row.jurisdiction}</span></td>
                  <td>{row.as_of_date}</td>
                  <td>{row.red_team_overall ?? '미상'}</td>
                  <td>{row.agreement_with_harness ?? '미상'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
