import type { Metadata } from 'next';
import Link from 'next/link';
import './globals.css';

export const metadata: Metadata = {
  title: 'Outlier Expectation Gap — Research Platform',
  description: 'US/KR screening, harness results and evidence-linked deep-dive research.',
};

const NAV = [
  { href: '/screener', label: 'Screener' },
  { href: '/runs', label: 'Harness Runs' },
  { href: '/reports', label: 'Reports' },
  { href: '/monitoring', label: 'Monitoring' },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>
        <header className="border-b" style={{ borderColor: 'var(--border)' }}>
          <div className="mx-auto flex max-w-7xl items-center gap-6 px-6 py-4">
            <Link href="/" className="font-semibold no-underline" style={{ color: 'var(--text)' }}>
              Outlier Expectation Gap
            </Link>
            <nav className="flex gap-4 text-sm">
              {NAV.map((item) => (
                <Link key={item.href} href={item.href} className="no-underline muted hover:opacity-80">
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
        <footer className="mx-auto max-w-7xl px-6 pb-10 text-xs muted">
          점수·archetype·Hard Veto·밸류에이션·포지션은 모두 하네스가 결정한다. 이 화면은 그 결과를 읽어
          보여줄 뿐이며 새로운 투자점수를 만들지 않는다.
        </footer>
      </body>
    </html>
  );
}
