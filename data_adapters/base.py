"""Provider interfaces.

`RegulatoryDataProvider` is the contract the harness depends on. Everything
below it — EDGAR's submissions index, OpenDART's 공시검색 — is an implementation
detail the harness never sees.

The as-of cutoff is enforced here rather than in each provider, because a rule
that every implementation has to remember is a rule that one of them will
eventually forget. `list_filings` is a concrete method: it calls the
subclass's `_all_filings` and then drops anything filed after the cutoff,
recording what it dropped.
"""
from abc import ABC, abstractmethod
from typing import Optional

from .types import Filing, Issuer, MarketSnapshot, Security


class AdapterError(RuntimeError):
    """An adapter failure phrased for the operator."""


class ConsolidationMixError(AdapterError):
    """A single series was about to mix 연결(CFS) and 별도(OFS) figures.

    This is never recoverable by picking one silently: the two bases describe
    different economic entities, so a revenue series that switches between them
    reports a growth rate that did not happen.
    """


class RegulatoryDataProvider(ABC):
    """Filings and disclosed financials from one regulator."""

    jurisdiction: str = ''
    regulator: str = ''

    @abstractmethod
    def resolve_issuer(self, identifier: str) -> Issuer:
        """Ticker, CIK or 종목코드 to a canonical issuer."""

    @abstractmethod
    def _all_filings(self, issuer: Issuer, **kwargs) -> list:
        """Every filing the regulator lists, newest first, before any cutoff."""

    def list_filings(self, issuer: Issuer, as_of_date: str, **kwargs) -> dict:
        """Filings at or before `as_of_date`, plus what the cutoff excluded.

        A filing dated after the cutoff is not "extra context": using one would
        put information into a run that did not exist when the run was dated.
        """
        rows = self._all_filings(issuer, as_of_date=as_of_date, **kwargs)
        eligible, excluded = [], []
        for row in rows:
            if (row.filing_date or '') <= as_of_date:
                eligible.append(row)
            else:
                excluded.append(row.to_dict())
        eligible.sort(key=lambda r: (r.filing_date or '', r.accession), reverse=True)
        return {'filings': eligible, 'excluded_post_cutoff': excluded,
                'as_of_date': as_of_date, 'regulator': self.regulator}

    @abstractmethod
    def fetch_raw_filing(self, filing: Filing) -> bytes:
        """The filing's primary document, as bytes. Untrusted content."""

    @abstractmethod
    def fetch_structured_financials(self, issuer: Issuer, as_of_date: str, **kwargs) -> list:
        """Disclosed numbers as `FinancialFact`s. No calculation, no estimate."""

    @abstractmethod
    def fetch_share_data(self, issuer: Issuer, as_of_date: str, **kwargs) -> list:
        """Share counts and capital-structure events, as facts and events."""

    @abstractmethod
    def build_financial_pack(self, identifier: str, as_of_date: str, **kwargs) -> dict:
        """A document validating against schemas/financial_pack.schema.json."""

    def list_universe(self, **kwargs) -> list:
        """Listed securities for this jurisdiction. Optional per provider."""
        raise NotImplementedError(f'{type(self).__name__} does not enumerate a universe')


class MarketDataProvider(ABC):
    """Prices and share counts. Deliberately separate from the regulator.

    Nothing in this interface may be served by a regulatory provider, and no
    regulatory provider exposes it. A price that arrived through a filings API
    is a price nobody can reconcile against a market.
    """

    jurisdiction: str = ''
    name: str = ''

    @abstractmethod
    def resolve_security(self, identifier: str) -> Security:
        """Ticker or 종목코드 to a canonical listed security."""

    @abstractmethod
    def get_snapshot(self, security: Security, as_of_date: str) -> Optional[MarketSnapshot]:
        """The last observation at or before `as_of_date`. Never after it."""

    @abstractmethod
    def get_price_history(self, security: Security, start_date: str, end_date: str) -> list:
        """Closes within the window, inclusive, oldest first."""

    def get_market_cap(self, security: Security, as_of_date: str) -> Optional[float]:
        snapshot = self.get_snapshot(security, as_of_date)
        if snapshot is None:
            return None
        if snapshot.market_cap is not None:
            return snapshot.market_cap
        if snapshot.close is not None and snapshot.shares_outstanding is not None:
            return snapshot.close * snapshot.shares_outstanding
        # Neither disclosed: unknown, which is not zero.
        return None
