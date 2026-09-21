'use client';

import Link from 'next/link';
import { use, useEffect, useState } from 'react';
import { ReportView } from '@/components/ReportView';
import { API_BASE, api, type DeepDiveReport } from '@/lib/api';

export default function ReportPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [report, setReport] = useState<DeepDiveReport | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.report(id).then(setReport).catch((e) => setError(String(e.message)));
  }, [id]);

  if (error) return <div className="card p-4 text-sm">{error}</div>;
  if (!report) return <p className="muted">불러오는 중…</p>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-4 text-sm">
        <Link href={`/deep-dive/${encodeURIComponent(id)}`}>리서치 진행·증거 보기</Link>
        <a href={`${API_BASE}/api/reports/${encodeURIComponent(id)}?fmt=markdown`} target="_blank" rel="noreferrer">
          Markdown
        </a>
      </div>
      <ReportView report={report} />
    </div>
  );
}
