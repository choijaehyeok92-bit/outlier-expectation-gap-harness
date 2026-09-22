'use client';

/**
 * The market data view: the one input the screener cannot produce for itself.
 *
 * `market_cap`, `current_price` and `price_to_owner_fcf` are market metrics,
 * and `missing_policy: exclude` drops a company whose filter cannot be judged.
 * So with no closes on disk, a US listing disappears from any screen that
 * mentions size or valuation — not for failing a test, but for having none.
 * This page makes that gap visible and fillable.
 *
 * It shows whether a key exists, never what it is. The key lives in the API
 * process's environment; this page has no way to read one and no field to
 * type one into.
 */
import { useEffect, useState } from 'react';
import { api, money, show, type MarketCatalogue, type MarketCoverage, type MarketFetchResult } from '@/lib/api';

const SCOPES: { value: 'packs' | 'universe' | 'all'; label: string; note: string }[] = [
  { value: 'packs', label: 'Stage 0 pack 있는 종목', note: '재무가 이미 있는 종목만 쓴다. 가격만 있고 재무가 없으면 스크리닝 행이 되지 못한다.' },
  { value: 'universe', label: '동기화된 유니버스', note: '`universe sync`가 만든 투자가능 미국 상장 전체. 파일이 없으면 거부한다.' },
  { value: 'all', label: '공급자가 준 전부', note: '그 세션의 모든 상장. ETF·워런트까지 파일로 떨어지므로 보통은 필요 없다.' },
];

export default function MarketPage() {
  const [catalogue, setCatalogue] = useState<MarketCatalogue | null>(null);
  const [coverage, setCoverage] = useState<MarketCoverage | null>(null);
  const [asOf, setAsOf] = useState('2026-09-21');
  const [provider, setProvider] = useState('');
  const [scope, setScope] = useState<'packs' | 'universe' | 'all'>('packs');
  const [tickers, setTickers] = useState('');
  const [dryRun, setDryRun] = useState(true);
  const [result, setResult] = useState<MarketFetchResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCoverage = (date: string) => {
    api.marketCoverage(date).then(setCoverage).catch((e) => setError(String(e.message)));
  };

  useEffect(() => {
    api.marketProviders()
      .then((payload) => { setCatalogue(payload); setProvider(payload.default); })
      .catch((e) => setError(String(e.message)));
    loadCoverage(asOf);
    // The cutoff is only read on mount; changing it re-reads through the button.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selected = catalogue?.providers.find((row) => row.name === provider);

  async function fetchPrices() {
    setBusy(true);
    setError(null);
    try {
      const names = tickers.split(',').map((t) => t.trim()).filter(Boolean);
      const payload = await api.marketFetch({
        as_of_date: asOf, provider, scope,
        tickers: names.length ? names : undefined, dry_run: dryRun,
      });
      setResult(payload);
      if (!dryRun) loadCoverage(asOf);
    } catch (e) {
      setError(String((e as Error).message));
      setResult(null);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Market Data</h1>
        <p className="muted mt-2 text-sm">
          주가는 공시가 아니므로 SEC·DART에서 오지 않는다. 주식수는 반대로 공시이므로 시세 공급자가
          아니라 Stage 0 pack(<code>dei:EntityCommonStockSharesOutstanding</code>)에서 온다.
          시가총액은 그 둘을 곱해 나온다 — 어느 쪽도 빠지면 미상이며 0으로 채우지 않는다.
        </p>
      </div>

      {error && <div className="card p-4 text-sm" style={{ borderColor: '#7f1d1d' }}>{error}</div>}

      {coverage && (
        <div className="card p-4">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-medium">커버리지</span>
            <span className="chip">기준일 {coverage.as_of_date}</span>
            <span className="chip">Stage 0 pack {coverage.packs}</span>
            <span className="chip" style={{ color: coverage.priced === coverage.packs && coverage.packs > 0 ? 'var(--accent)' : undefined }}>
              가격 있음 {coverage.priced}
            </span>
            {coverage.unpriced.length > 0 && <span className="chip">가격 없음 {coverage.unpriced.length}</span>}
            {coverage.without_shares.length > 0 && <span className="chip">주식수 없음 {coverage.without_shares.length}</span>}
          </div>
          {coverage.priced === 0 && (
            <p className="mt-2 text-xs" style={{ color: '#fbbf24' }}>
              이 기준일에 쓸 수 있는 미국 종가가 하나도 없다. 이 상태에서는 시총·현재가·price_to_owner_fcf가
              전부 미상이고, <code>missing_policy: exclude</code> 때문에 해당 종목들이 스크리닝에서 통째로 빠진다.
            </p>
          )}
          {coverage.unpriced.length > 0 && (
            <p className="muted mt-2 text-xs">가격 없음: {coverage.unpriced.join(', ')}</p>
          )}
          {coverage.older_than_cutoff.length > 0 && (
            <p className="muted mt-1 text-xs">
              기준일보다 오래된 관측 {coverage.older_than_cutoff.length}건 — 직전 거래일 종가다. 앞선 날짜는 쓰지 않는다.
            </p>
          )}
        </div>
      )}

      <div className="card space-y-3 p-4">
        <div className="flex flex-wrap items-end gap-3 text-sm">
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">공급자</span>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="rounded-md bg-transparent px-2 py-1"
              style={{ border: '1px solid var(--border)', color: 'var(--text)' }}
            >
              {(catalogue?.providers ?? []).map((row) => (
                <option key={row.name} value={row.name} style={{ background: 'var(--surface)' }}>
                  {row.label}{row.is_default ? ' · 기본' : ''}{row.configured ? '' : ' · 키 없음'}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">기준일 (이 날짜 이후는 쓰지 않는다)</span>
            <input
              value={asOf}
              onChange={(e) => setAsOf(e.target.value)}
              className="rounded-md bg-transparent px-2 py-1"
              style={{ border: '1px solid var(--border)' }}
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">범위</span>
            <select
              value={scope}
              onChange={(e) => setScope(e.target.value as typeof scope)}
              className="rounded-md bg-transparent px-2 py-1"
              style={{ border: '1px solid var(--border)', color: 'var(--text)' }}
            >
              {SCOPES.map((row) => (
                <option key={row.value} value={row.value} style={{ background: 'var(--surface)' }}>{row.label}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">종목 지정 (비우면 범위대로)</span>
            <input
              value={tickers}
              onChange={(e) => setTickers(e.target.value)}
              placeholder="MSFT,NVDA"
              className="rounded-md bg-transparent px-2 py-1"
              style={{ border: '1px solid var(--border)', minWidth: '11rem' }}
            />
          </label>
          <label className="flex items-center gap-2 pb-1">
            <input type="checkbox" checked={dryRun} onChange={(e) => setDryRun(e.target.checked)} />
            <span className="muted text-xs">받아보기만 (파일 쓰지 않음)</span>
          </label>
          <button
            onClick={() => { loadCoverage(asOf); }}
            className="rounded-md px-3 py-1.5"
            style={{ border: '1px solid var(--border)' }}
          >
            커버리지 다시 읽기
          </button>
          <button
            onClick={fetchPrices}
            disabled={busy || !selected?.configured}
            className="rounded-md px-3 py-1.5 font-medium"
            style={{
              border: `1px solid ${selected?.configured ? 'var(--accent)' : 'var(--border)'}`,
              color: selected?.configured ? 'var(--accent)' : undefined,
              opacity: selected?.configured ? 1 : 0.5,
            }}
          >
            {busy ? '받는 중…' : dryRun ? '받아보기' : '가격 받아 쓰기'}
          </button>
        </div>

        <p className="muted text-xs">{SCOPES.find((s) => s.value === scope)?.note}</p>

        {selected && (
          <p className="muted text-xs">
            <span style={{ color: 'var(--text)' }}>{selected.label}</span> — {selected.note}
            {selected.bulk && ' 한 세션이 호출 1회로 온다.'}
          </p>
        )}
        {selected && !selected.configured && (
          <p className="text-xs" style={{ color: '#fbbf24' }}>
            서버에 <code>{selected.env_var}</code>가 없어 지금은 호출할 수 없다. 키는 API 프로세스의
            환경변수로 두고 재시작한다 — 브라우저로 전송되지 않으며 이 화면은 키를 알지 못한다.
            {selected.signup && <> 발급: <a href={selected.signup} target="_blank" rel="noreferrer">{selected.signup}</a></>}
          </p>
        )}
        {selected?.auth_note && <p className="muted text-xs">{selected.auth_note}</p>}
      </div>

      {result && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="chip">공급자 {result.provider}</span>
            <span className="chip">세션 {result.session_date ?? '없음'}</span>
            <span className="chip">공급자 응답 {result.vendor_rows}행</span>
            <span className="chip">대상 {result.requested}</span>
            <span className="chip">{result.wrote_files ? '기록' : '미기록'} {result.written_count}</span>
          </div>
          <p className="muted text-xs">{result.selection_reason} · {result.note}</p>
          {result.sessions_tried.length > 1 && (
            <p className="muted text-xs">
              시도한 날짜: {result.sessions_tried.join(' → ')} — 휴장일은 뒤로만 거슬러 올라간다.
            </p>
          )}

          {result.missing_price.length > 0 && (
            <div className="card p-4">
              <div className="text-sm font-medium">공급자가 시세를 주지 않은 종목</div>
              <p className="muted mt-1 text-xs">
                실패가 아니다. 공급자가 모든 상장을 다루지는 않는다. 다만 조용히 사라지면 안 되므로 이름을 남긴다.
              </p>
              <p className="mt-2 text-sm">{result.missing_price.join(', ')}</p>
            </div>
          )}

          {result.missing_shares_outstanding.length > 0 && (
            <div className="card p-4">
              <div className="text-sm font-medium">공시 주식수가 없는 종목</div>
              <p className="muted mt-1 text-xs">
                가격은 썼지만 주식수가 비어 있어 시가총액은 미상으로 남는다. 0으로 채우지 않는다.
              </p>
              <p className="mt-2 text-sm">{result.missing_shares_outstanding.join(', ')}</p>
            </div>
          )}

          {result.written.length > 0 && (
            <div className="card overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="muted text-left">
                  <tr>
                    <th className="px-4 py-3">Ticker</th>
                    <th className="px-4 py-3">세션</th>
                    <th className="px-4 py-3">종가</th>
                    <th className="px-4 py-3">주식수 (공시)</th>
                    <th className="px-4 py-3">주식수 기준일</th>
                    <th className="px-4 py-3">시가총액 (종가 × 주식수)</th>
                  </tr>
                </thead>
                <tbody>
                  {result.written.map((row) => (
                    <tr key={row.ticker} className="border-t" style={{ borderColor: 'var(--border)' }}>
                      <td className="px-4 py-2 font-medium">{row.ticker}</td>
                      <td className="px-4 py-2">{row.date}</td>
                      <td className="px-4 py-2">{show(row.close)}</td>
                      <td className="px-4 py-2">{row.shares_outstanding === null ? '미상' : row.shares_outstanding.toLocaleString()}</td>
                      <td className="px-4 py-2 muted">{row.shares_as_of ?? '미상'}</td>
                      <td className="px-4 py-2">
                        {row.shares_outstanding === null ? '미상' : money(row.close * row.shares_outstanding)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {catalogue && Object.keys(catalogue.rejected).length > 0 && (
        <div className="card p-4">
          <div className="text-sm font-medium">쓰지 않기로 한 공급자</div>
          <ul className="mt-2 space-y-1 text-xs muted">
            {Object.entries(catalogue.rejected).map(([name, reason]) => (
              <li key={name}><span style={{ color: 'var(--text)' }}>{name}</span> — {reason}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="muted text-xs">
        가격을 쓴 뒤 창고를 다시 만들어야 스크리너가 쓴다:{' '}
        <code>python harness.py screen build --as-of {asOf} --packs &lt;dir&gt; --market-data data/market</code>
        {' '}— 또는 워커 큐에 <code>screen_build</code>를 넣는다.
      </p>
    </div>
  );
}
