"""SEC EDGAR adapter: US regulatory filings and XBRL company facts."""
from .provider import SecEdgarProvider
from .xbrl import CompanyFactsReader, period_kind_for

__all__ = ['SecEdgarProvider', 'CompanyFactsReader', 'period_kind_for']
