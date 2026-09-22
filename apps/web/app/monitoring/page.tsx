'use client';

/**
 * The portfolio monitoring view.
 *
 * It is ordered by what needs a person, not by score. A company whose
 * watchlist has never been observed sits high on this page rather than low:
 * "nobody has checked" is the finding, and a dashboard that sorted it out of
 * sight would be the failure this page exists to prevent.
 */
import Link from 'next/link';
import { useEffect, useState } from 'react';
import { api, type MonitoringPortfolio } from '@/lib/api';

export default function MonitoringPage() {
  const [data, setData] = useState<MonitoringPortfolio | null>(null);
  const [tickers, setTickers] = useState('');
  const [error, setError] = useState<string | null>(null);

  const load = (value?: string) => {
    setError(null);
    api.monitoring(value || undefined).then(setData).catch((e) => setError(String(e.message)));
  };
  useEffect(() => load(), []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Monitoring</h1>
        <p className="muted mt-2 text-sm">
          보고서가 선언한 KPI와 falsifier를 관측과 대조한다. 이 화면은 재검토가 필요한 항목을 띄울 뿐
          점수·archetype·Hard Veto·ic_state·비중을 바꾸지 않는다. thesis_break는 매도 신호가 아니라
          다시 보라는 요청이다.
        </p>
      </div>

      <form
        className="flex gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          load(tickers.trim());
        }}
      >
        <input
          className="flex-1 rounded border px-3 py-2 text-sm"
          style={{ background: 'var(--surface)', borderColor: 'var(--border)', color: 'var(--text)' }}
          placeholder="MSFT,NVDA — 비우면 관측이 기록된 기업만"
          value={tickers}
          onChange={(event) => setTickers(event.target.value)}
        />
        <button type="submit" className="rounded border px-4 py-2 text-sm" style={{ borderColor: 'var(--border)' }}>
          보기
        </button>
      </form>

      {error && <div className="card p-4 text-sm" style={{ borderColor: '#7f1d1d' }}>{error}</div>}
      {data?.note && <div className="card p-4 text-sm muted">{data.note}</div>}

      {data && data.rows.length > 0 && (
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="muted text-left">
              <tr>
                <th className="px-4 py-3">Ticker</th>
                <th className="px-4 py-3">기준일</th>
                <th className="px-4 py-3">감시 항목</th>
                <th className="px-4 py-3">재검토 필요</th>
                <th className="px-4 py-3">한 번도 관측 안 됨</th>
                <th className="px-4 py-3">사람이 읽어야</th>
                <th className="px-4 py-3">가장 시급한 항목</th>
              </tr>
            </thead>
            <tbody>
              {data.rows.map((row) => (
                <tr key={row.ticker} className="border-t" style={{ borderColor: 'var(--border)' }}>
                  <td className="px-4 py-3">
                    <Link href={`/monitoring/${encodeURIComponent(row.ticker)}`} className="no-underline">
                      {row.ticker}
                    </Link>
                  </td>
                  <td className="px-4 py-3 muted">{row.analysis_as_of_date ?? 'unknown'}</td>
                  <td className="px-4 py-3">{row.summary.items}</td>
                  <td className="px-4 py-3" style={{ color: row.summary.review_required ? '#f87171' : undefined }}>
                    {row.summary.review_required}
                  </td>
                  <td className="px-4 py-3 muted">{row.summary.never_observed}</td>
                  <td className="px-4 py-3 muted">{row.summary.not_machine_checkable}</td>
                  <td className="px-4 py-3 muted">{row.review_required[0]?.name?.slice(0, 60) ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {data?.unreadable?.length ? (
        <div className="card p-4 text-sm">
          <div className="mb-2 font-medium">읽을 수 없었던 기업</div>
          {data.unreadable.map((row) => (
            <div key={row.ticker} className="muted">
              {row.ticker} — {row.reason}
            </div>
          ))}
        </div>
      ) : null}

      {data?.authority && (
        <div className="card p-4 text-xs muted">
          <div className="mb-1 font-medium" style={{ color: 'var(--text)' }}>
            이 계층이 할 수 없는 것
          </div>
          {data.authority.may_not.join(' · ')}
          <div className="mt-2">{data.authority.statement}</div>
        </div>
      )}
    </div>
  );
}
