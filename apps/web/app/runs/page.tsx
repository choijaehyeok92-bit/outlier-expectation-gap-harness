'use client';

import { useEffect, useState } from 'react';
import { Leaderboard } from '@/components/Leaderboard';
import { api, type DeepDiveSummary, type RunRow } from '@/lib/api';

export default function RunsPage() {
  const [rows, setRows] = useState<RunRow[]>([]);
  const [deepDives, setDeepDives] = useState<DeepDiveSummary[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.runs().then(setRows).catch((e) => setError(String(e.message)));
    api.deepDives().then(setDeepDives).catch(() => setDeepDives([]));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Harness Runs</h1>
        <p className="muted mt-2 text-sm">완료된 하네스 run. 모든 값은 하네스가 기록한 그대로다.</p>
      </div>
      {error && <div className="card p-4 text-sm" style={{ borderColor: '#7f1d1d' }}>{error}</div>}
      <Leaderboard rows={rows} deepDiveByTicker={Object.fromEntries(deepDives.map((d) => [d.ticker, d.deep_dive_id]))} />
    </div>
  );
}
