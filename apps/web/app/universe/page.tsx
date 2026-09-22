'use client';

/**
 * Intake: from every listing to the few hundred worth ingesting.
 *
 * Three steps, in order, each honest about what it is.
 *
 * 1. Sync the universe from the regulators. Exclusions are shown, not hidden —
 *    "why is this not in my screen" has an answer here.
 * 2. Rank what is left. **Not by market cap**: market cap is close × shares,
 *    the share count comes from a filing, and you have to ingest a company to
 *    read it — so cutting by market cap before ingesting costs exactly what it
 *    was meant to save. The rank is dollar volume, and it decides where the
 *    next call goes and nothing else.
 * 3. Ingest the chosen ones into Stage 0 packs.
 *
 * Nothing on this page is evidence. Liquidity is not company quality, and a
 * long-term outlier is frequently illiquid before it is obvious.
 */
import { useEffect, useState } from 'react';
import { api, money, type Candidate, type CandidateList, type PackIngestResult,
         type RegulatorCredential, type UniverseSyncResult } from '@/lib/api';

const MAX_PER_REQUEST = 10;

export default function UniversePage() {
  const [creds, setCreds] = useState<RegulatorCredential[]>([]);
  const [asOf, setAsOf] = useState('2026-09-21');
  const [markets, setMarkets] = useState('US,KR');
  const [enrich, setEnrich] = useState('0');
  const [limit, setLimit] = useState('50');
  const [includeIngested, setIncludeIngested] = useState(false);
  const [sync, setSync] = useState<UniverseSyncResult | null>(null);
  const [list, setList] = useState<CandidateList | null>(null);
  const [picked, setPicked] = useState<Record<string, boolean>>({});
  const [ingest, setIngest] = useState<PackIngestResult | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => { api.regulatorCredentials().then((p) => setCreds(p.credentials)).catch(() => setCreds([])); }, []);

  const credFor = (market: string) => creds.find((row) => row.market === market);
  const chosenMarkets = markets.split(',').map((m) => m.trim().toUpperCase()).filter(Boolean);
  const missing = chosenMarkets.map(credFor).filter((row) => row && !row.configured) as RegulatorCredential[];
  const selected = Object.entries(picked).filter(([, on]) => on).map(([t]) => t);

  async function run(label: string, work: () => Promise<void>) {
    setBusy(label);
    setError(null);
    try { await work(); } catch (e) { setError(String((e as Error).message)); } finally { setBusy(null); }
  }

  const doSync = () => run('sync', async () => {
    setSync(await api.universeSync({
      markets: chosenMarkets as ('US' | 'KR')[], as_of_date: asOf,
      enrich_limit: Number.parseInt(enrich, 10) || 0,
    }));
  });

  const doRank = () => run('rank', async () => {
    const payload = await api.candidates(asOf, markets, Number.parseInt(limit, 10) || 50, includeIngested);
    setList(payload);
    setPicked({});
    setIngest(null);
  });

  const doIngest = (market: 'US' | 'KR') => run('ingest', async () => {
    const wanted = selected.filter((ticker) => {
      const row = [...(list?.candidates ?? []), ...(list?.unranked ?? [])].find((c) => c.ticker === ticker);
      return row?.jurisdiction === market;
    });
    if (!wanted.length) throw new Error(`${market} 종목이 선택되지 않았다`);
    setIngest(await api.ingestPacks({ tickers: wanted.slice(0, MAX_PER_REQUEST), market, as_of_date: asOf }));
  });

  const toggle = (ticker: string) => setPicked((prev) => ({ ...prev, [ticker]: !prev[ticker] }));

  const row = (c: Candidate) => (
    <tr key={c.ticker} className="border-t" style={{ borderColor: 'var(--border)' }}>
      <td className="px-3 py-2">
        <input type="checkbox" checked={!!picked[c.ticker]} onChange={() => toggle(c.ticker)}
               disabled={c.already_ingested} />
      </td>
      <td className="px-3 py-2 muted">{c.rank ?? '—'}</td>
      <td className="px-3 py-2 font-medium">
        {c.ticker}
        {c.quoted_as && <span className="muted"> → {c.quoted_as}</span>}
      </td>
      <td className="px-3 py-2">{c.company_name ?? '이름 미상'}</td>
      <td className="px-3 py-2 muted">{c.jurisdiction} · {c.exchange ?? '?'}</td>
      <td className="px-3 py-2">{c.dollar_volume === undefined ? '—' : money(c.dollar_volume)}</td>
      <td className="px-3 py-2 muted text-xs">
        {c.already_ingested ? '적재됨' : c.reason_unranked ?? ''}
        {c.requires_review ? ' · 확인 필요' : ''}
      </td>
    </tr>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Universe &amp; Intake</h1>
        <p className="muted mt-2 text-sm">
          전 종목 → 적재할 수백 개 → Stage 0 pack. <strong>시가총액으로 자르지 않는다</strong> —
          시총은 종가 × 주식수이고 주식수는 공시에서 오므로, 적재하기 전에 시총으로 자르는 것은
          자르려던 비용을 그대로 쓰는 일이다. 대신 한 번의 일괄 호출로 얻는 거래대금으로 순위를
          매긴다. 이 순위는 <strong>다음 호출을 어디에 쓸지</strong>만 정하며 점수·archetype·
          Hard Veto·밸류에이션 어디에도 들어가지 않는다. 유동성은 기업의 질이 아니다.
        </p>
      </div>

      {error && <div className="card p-4 text-sm" style={{ borderColor: '#7f1d1d' }}>{error}</div>}

      <div className="card p-4">
        <div className="text-sm font-medium">규제기관 자격증명</div>
        <ul className="mt-2 space-y-1 text-xs">
          {creds.map((c) => (
            <li key={c.regulator}>
              <span style={{ color: c.configured ? 'var(--accent)' : '#fbbf24' }}>
                {c.configured ? '설정됨' : '없음'}
              </span>{' '}
              <span style={{ color: 'var(--text)' }}>{c.market} · {c.regulator}</span>{' '}
              <code>{c.env_var}</code> — <span className="muted">{c.note}</span>
              {!c.configured && <> <a href={c.signup} target="_blank" rel="noreferrer">발급</a></>}
            </li>
          ))}
        </ul>
        <p className="muted mt-2 text-xs">
          서버는 값이 있는지 여부만 알려준다. 값·길이·앞자리 모두 브라우저로 보내지 않으며 이
          화면에는 입력칸도 없다 — 키는 API 프로세스의 환경변수에 두고 재시작한다.
        </p>
      </div>

      <div className="card space-y-3 p-4">
        <div className="flex flex-wrap items-end gap-3 text-sm">
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">기준일</span>
            <input value={asOf} onChange={(e) => setAsOf(e.target.value)}
                   className="rounded-md bg-transparent px-2 py-1"
                   style={{ border: '1px solid var(--border)' }} />
          </label>
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">시장</span>
            <select value={markets} onChange={(e) => setMarkets(e.target.value)}
                    className="rounded-md bg-transparent px-2 py-1"
                    style={{ border: '1px solid var(--border)', color: 'var(--text)' }}>
              {['US,KR', 'US', 'KR'].map((m) => (
                <option key={m} value={m} style={{ background: 'var(--surface)' }}>{m}</option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">KR 세그먼트 조회 (DART 호출 수)</span>
            <input value={enrich} onChange={(e) => setEnrich(e.target.value)}
                   className="rounded-md bg-transparent px-2 py-1"
                   style={{ border: '1px solid var(--border)', width: '7rem' }} />
          </label>
          <button onClick={doSync} disabled={busy !== null} className="rounded-md px-3 py-1.5"
                  style={{ border: '1px solid var(--border)' }}>
            {busy === 'sync' ? '동기화 중…' : '1. 유니버스 동기화'}
          </button>
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">후보 수</span>
            <input value={limit} onChange={(e) => setLimit(e.target.value)}
                   className="rounded-md bg-transparent px-2 py-1"
                   style={{ border: '1px solid var(--border)', width: '5rem' }} />
          </label>
          <label className="flex items-center gap-2 pb-1">
            <input type="checkbox" checked={includeIngested}
                   onChange={(e) => setIncludeIngested(e.target.checked)} />
            <span className="muted text-xs">적재된 것도 보기</span>
          </label>
          <button onClick={doRank} disabled={busy !== null}
                  className="rounded-md px-3 py-1.5 font-medium"
                  style={{ border: '1px solid var(--accent)', color: 'var(--accent)' }}>
            {busy === 'rank' ? '읽는 중…' : '2. 후보 순위'}
          </button>
        </div>
        {missing.length > 0 && (
          <p className="text-xs" style={{ color: '#fbbf24' }}>
            {missing.map((c) => `${c.market}(${c.env_var})`).join(', ')} 가 없어 그 시장의 동기화·적재는 실패한다.
          </p>
        )}
        <p className="muted text-xs">
          KR 세그먼트 조회는 발행사 1곳당 DART 호출 1회다. 0이면 조회하지 않는다. 500을 넘겨도
          500에서 멈춘다 — 요청 처리 중에 무한정 부르면 타임아웃과 반쯤 쓰인 파일이 남는다.
        </p>
      </div>

      {sync && (
        <div className="card p-4">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-medium">유니버스</span>
            <span className="chip">전체 {sync.summary.total}</span>
            <span className="chip">투자가능 {sync.summary.included}</span>
            <span className="chip">제외 {sync.summary.excluded}</span>
            <span className="chip">확인 필요 {sync.summary.requires_review}</span>
          </div>
          <p className="muted mt-2 text-xs">
            제외 사유: {Object.entries(sync.summary.excluded_by_reason)
              .map(([reason, n]) => `${reason} ${n}`).join(' · ') || '없음'}
          </p>
          <p className="muted mt-1 text-xs">
            거래소: {Object.entries(sync.summary.by_exchange).map(([x, n]) => `${x} ${n}`).join(' · ')}
          </p>
          {Object.keys(sync.errors).length > 0 && (
            <p className="mt-2 text-xs" style={{ color: '#fbbf24' }}>
              실패한 시장: {Object.entries(sync.errors).map(([m, e]) => `${m} — ${e}`).join(' / ')}
              {' '}— 한 시장이 실패해도 다른 시장은 진행한다.
            </p>
          )}
          {sync.enrich_limit_note && <p className="muted mt-1 text-xs">{sync.enrich_limit_note}</p>}
        </div>
      )}

      {list && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="chip">유니버스 {list.universe_size}</span>
            <span className="chip">이미 적재 {list.already_ingested}</span>
            <span className="chip">순위 매김 {list.ranked_count}</span>
            <span className="chip">순위 없음 {list.unranked_count}</span>
            {list.session_date && <span className="chip">세션 {list.session_date}</span>}
            <span className="chip">선택 {selected.length}</span>
          </div>
          {list.quote_error && list.quote_source === 'local_csv' && (
            <p className="muted text-xs">
              공급자를 부르지 않고 <code>data/market/US/</code>에 이미 있는 시세로 순위를 매겼다.
              그래서 아직 받아오지 않은 종목은 순위에 들지 못한다. ({list.quote_error})
            </p>
          )}
          {list.quote_error && list.quote_source !== 'local_csv' && (
            <p className="text-xs" style={{ color: '#fbbf24' }}>
              시세를 얻지 못해 순위를 매기지 못했다 — 목록은 그대로다. {list.quote_error}
            </p>
          )}
          {list.ranked_by_note && <p className="muted text-xs">{list.ranked_by_note}</p>}

          <div className="card overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="muted text-left">
                <tr>
                  <th className="px-3 py-3"> </th>
                  <th className="px-3 py-3">#</th>
                  <th className="px-3 py-3">Ticker</th>
                  <th className="px-3 py-3">기업</th>
                  <th className="px-3 py-3">시장</th>
                  <th className="px-3 py-3">거래대금</th>
                  <th className="px-3 py-3">비고</th>
                </tr>
              </thead>
              <tbody>
                {list.candidates.map(row)}
                {list.unranked.map(row)}
              </tbody>
            </table>
          </div>

          <div className="flex flex-wrap items-center gap-3 text-sm">
            <button onClick={() => doIngest('US')} disabled={busy !== null || !selected.length}
                    className="rounded-md px-3 py-1.5 font-medium"
                    style={{ border: '1px solid var(--accent)', color: 'var(--accent)',
                             opacity: selected.length ? 1 : 0.5 }}>
              {busy === 'ingest' ? '적재 중…' : '3. 선택한 US 종목 적재'}
            </button>
            <button onClick={() => doIngest('KR')} disabled={busy !== null || !selected.length}
                    className="rounded-md px-3 py-1.5"
                    style={{ border: '1px solid var(--border)', opacity: selected.length ? 1 : 0.5 }}>
              선택한 KR 종목 적재
            </button>
            <span className="muted text-xs">
              한 번에 {MAX_PER_REQUEST}개까지. 기업마다 규제기관 요청이 여러 번이라 더 넣으면
              요청이 타임아웃되고 반쯤 쓰인 디렉터리가 남는다. 더 큰 배치는 워커 큐의{' '}
              <code>ingest_pack</code>에 넣는다 — 거기에는 lease와 재시도 정책이 있다.
            </span>
          </div>
        </div>
      )}

      {ingest && (
        <div className="card p-4">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="font-medium">적재 결과</span>
            <span className="chip">요청 {ingest.requested}</span>
            <span className="chip">기록 {ingest.written}</span>
            <span className="chip">이미 있음 {ingest.skipped_existing}</span>
            {ingest.failed > 0 && <span className="chip">실패 {ingest.failed}</span>}
          </div>
          <ul className="mt-2 space-y-1 text-sm">
            {ingest.results.map((r) => (
              <li key={r.ticker}>
                <span className="font-medium">{r.ticker}</span>{' '}
                <span className="muted">
                  {r.status === 'failed' ? `실패 — ${r.error}`
                    : r.status === 'exists' ? '이미 있음 (덮어쓰지 않았다)'
                    : `fact ${r.facts} · 문서 ${r.documents} · 확인 필요 ${r.requires_review}`}
                </span>
                {r.validation_errors && r.validation_errors.length > 0 && (
                  <span style={{ color: '#fbbf24' }}> · 검증 오류 {r.validation_errors.length}</span>
                )}
              </li>
            ))}
          </ul>
          <p className="muted mt-2 text-xs">
            pack 위치: <code>{ingest.pack_dir}</code>. 이 다음은{' '}
            <a href="/market">Market Data</a>에서 시세를 받고,{' '}
            <code>screen build --packs {ingest.pack_dir} --market-data data/market</code>으로
            창고를 만든 뒤 <a href="/screener">Screener</a>로 간다.
          </p>
        </div>
      )}
    </div>
  );
}
