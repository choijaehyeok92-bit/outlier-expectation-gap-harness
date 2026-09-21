'use client';

import { useEffect, useState } from 'react';
import { Leaderboard } from '@/components/Leaderboard';
import { SpecView } from '@/components/SpecView';
import { Unresolved } from '@/components/Unresolved';
import { api, type DeepDiveSummary, type ScreenRecord, type ScreeningSpec } from '@/lib/api';

// The first example is deliberately the hard one: it names a metric whose
// backend is not built yet and a dilution band no run in this corpus declared,
// so it shows what the screener does with a condition it cannot answer.
const EXAMPLES = [
  {
    label: '원 요청 (미해석 조건 포함)',
    text: '미국과 한국에서 시총 1조 이상, 순현금이고 최근 3년 매출 CAGR 15% 이상이며 희석이 적은 기업 중, 해자가 강하고 Base 가치 이하인 종목 찾아줘.',
  },
  {
    label: '현재 백엔드로 답할 수 있는 요청',
    text: '미국과 한국에서 시총 1조 이상, 순현금이고 해자가 강하고 Base 가치 이하인 종목 찾아줘.',
  },
  {
    label: 'Hard Veto 통과 + 코어 점수',
    text: '시총 10 billion dollars 이상이며 hard veto 통과, 코어 점수 75 이상',
  },
];
const EXAMPLE = EXAMPLES[0].text;

export default function ScreenerPage() {
  const [text, setText] = useState(EXAMPLE);
  const [asOf, setAsOf] = useState('2026-09-18');
  const [krwRate, setKrwRate] = useState('1380.2');
  const [spec, setSpec] = useState<ScreeningSpec | null>(null);
  const [record, setRecord] = useState<ScreenRecord | null>(null);
  const [deepDives, setDeepDives] = useState<DeepDiveSummary[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.deepDives().then(setDeepDives).catch(() => setDeepDives([]));
  }, []);

  const fx = () => {
    const rate = Number.parseFloat(krwRate);
    return Number.isFinite(rate) && rate > 0 ? { KRW: rate } : undefined;
  };

  async function parse() {
    setBusy(true);
    setError(null);
    try {
      setSpec(await api.parse({ text, as_of_date: asOf, fx_rates: fx() }));
      setRecord(null);
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const result = spec
        ? await api.screen({ spec, persist: true })
        : await api.screen({ text, as_of_date: asOf, fx_rates: fx(), persist: true });
      setRecord(result);
      setSpec(result.spec);
    } catch (e) {
      setError(String((e as Error).message));
    } finally {
      setBusy(false);
    }
  }

  const deepDiveByTicker = Object.fromEntries(deepDives.map((d) => [d.ticker, d.deep_dive_id]));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Screener</h1>
        <p className="muted mt-2 text-sm">
          자연어를 ScreeningSpec으로 해석한 뒤 결정론적 컴파일러가 실행한다. 모델은 SQL을 만들지 않고
          지표를 계산하지 않는다. 해석하지 못한 조건은 버리지 않고 아래에 남는다.
        </p>
      </div>

      <div className="card space-y-3 p-4">
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((example) => (
            <button
              key={example.label}
              onClick={() => { setText(example.text); setSpec(null); setRecord(null); }}
              className="chip"
              style={{ color: text === example.text ? 'var(--accent)' : undefined }}
            >
              {example.label}
            </button>
          ))}
        </div>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          rows={3}
          className="w-full rounded-md bg-transparent p-3 text-sm outline-none"
          style={{ border: '1px solid var(--border)' }}
        />
        <div className="flex flex-wrap items-end gap-3 text-sm">
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">기준일 (as_of_date)</span>
            <input
              value={asOf}
              onChange={(e) => setAsOf(e.target.value)}
              className="rounded-md bg-transparent px-2 py-1"
              style={{ border: '1px solid var(--border)' }}
            />
          </label>
          <label className="flex flex-col gap-1">
            <span className="muted text-xs">KRW per USD (명시적 환율)</span>
            <input
              value={krwRate}
              onChange={(e) => setKrwRate(e.target.value)}
              className="rounded-md bg-transparent px-2 py-1"
              style={{ border: '1px solid var(--border)' }}
            />
          </label>
          <button
            onClick={parse}
            disabled={busy}
            className="rounded-md px-3 py-1.5"
            style={{ border: '1px solid var(--border)' }}
          >
            해석만
          </button>
          <button
            onClick={run}
            disabled={busy}
            className="rounded-md px-3 py-1.5 font-medium"
            style={{ border: '1px solid var(--accent)', color: 'var(--accent)' }}
          >
            {busy ? '실행 중…' : '스크리닝 실행'}
          </button>
        </div>
        <p className="muted text-xs">
          환율은 서버가 조회하지 않는다. 원화 임계값을 USD 컬럼과 비교하려면 기준일 환율을 직접 넣어야 하며,
          넣지 않으면 그 조건은 적용되지 않고 미해석으로 남는다.
        </p>
      </div>

      {error && (
        <div className="card p-4 text-sm" style={{ borderColor: '#7f1d1d' }}>{error}</div>
      )}

      {spec && <SpecView spec={spec} />}
      {spec && <Unresolved rows={spec.unresolved_conditions} />}

      {record && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-2 text-sm">
            <span className="chip">screen run {record.screen_run_id}</span>
            <span className="chip">{record.summary.matched_count} / {record.summary.considered} matched</span>
            <span className="chip">backend {record.backend}</span>
          </div>
          <Leaderboard rows={record.results} deepDiveByTicker={deepDiveByTicker} />

          {record.summary.excluded_missing_data.length > 0 && (
            <div className="card p-4">
              <div className="text-sm font-medium">값이 없어 제외된 종목</div>
              <p className="muted mt-1 text-xs">누락값을 0으로 간주하지 않는다. 아래는 조건을 판정할 수 없어 제외됐다.</p>
              <ul className="mt-2 space-y-1 text-sm">
                {record.summary.excluded_missing_data.map((row) => (
                  <li key={row.run_id}>
                    <span className="font-medium">{row.ticker}</span>
                    <span className="muted"> — {row.missing_fields.join(', ')}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {record.summary.excluded_post_cutoff.length > 0 && (
            <div className="card p-4">
              <div className="text-sm font-medium">기준일 이후라 제외된 run</div>
              <ul className="muted mt-2 space-y-1 text-sm">
                {record.summary.excluded_post_cutoff.map((row) => (
                  <li key={row.run_id}>{row.run_id} — {row.as_of_date}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
