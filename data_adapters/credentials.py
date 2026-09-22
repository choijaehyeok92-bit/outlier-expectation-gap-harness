"""Build a regulator provider from the environment, and refuse clearly without one.

One place, because the refusal is the interesting part. SEC fair access asks
for a contact in the User-Agent and OpenDART meters by key; neither is
something the harness may invent, and a contact the operator did not set is a
contact this software has no right to send.

Nothing here accepts a credential as an argument. A key that can arrive in a
call arrives in a job payload, and this repository serves job payloads back
over its own API.
"""
import os
from typing import Optional

from .base import AdapterError

SEC_ENV = 'SEC_USER_AGENT'
DART_ENV = 'OPENDART_API_KEY'


def sec_user_agent(environ=None) -> str:
    value = ((environ if environ is not None else os.environ).get(SEC_ENV) or '').strip()
    if value:
        return value
    raise AdapterError(
        f"SEC access needs ${SEC_ENV} — fair access requires a contact in the "
        "User-Agent, e.g. 'Jane Doe jane@example.com'. The harness does not invent one "
        'and does not send a contact you did not set.')


def dart_key(environ=None) -> str:
    value = ((environ if environ is not None else os.environ).get(DART_ENV) or '').strip()
    if value:
        return value
    raise AdapterError(f'DART access needs ${DART_ENV} in the process environment. '
                       'Issue one at https://opendart.fss.or.kr/')


def describe(environ=None) -> list:
    """Whether each credential exists. Never its value, length or prefix."""
    env = environ if environ is not None else os.environ
    return [
        {'market': 'US', 'regulator': 'SEC', 'env_var': SEC_ENV,
         'configured': bool((env.get(SEC_ENV) or '').strip()),
         'note': 'SEC 공정이용 정책이 연락처가 담긴 User-Agent를 요구한다. 키가 아니라 연락처다.',
         'signup': 'https://www.sec.gov/os/webmaster-faq#developers'},
        {'market': 'KR', 'regulator': 'DART', 'env_var': DART_ENV,
         'configured': bool((env.get(DART_ENV) or '').strip()),
         'note': 'OpenDART 인증키. 발급은 무료이고 키당 일일 호출 한도가 있다.',
         'signup': 'https://opendart.fss.or.kr/'},
    ]


def regulator_provider(market: str, *, transport=None, environ=None, corp_codes=None,
                       refresh_corp_codes: bool = False):
    """A `RegulatoryDataProvider` for one market, credentialed from the environment."""
    if str(market).upper() == 'KR':
        from .dart import DartProvider
        from .dart.corpcode import CorpCodeCache
        key = dart_key(environ)
        provider = DartProvider(api_key=key, transport=transport,
                                corp_codes=CorpCodeCache(path=corp_codes))
        if refresh_corp_codes or not provider.corp_codes.entries:
            provider.corp_codes.refresh(provider.client.get(
                provider._url('corp_code'), {'crtfc_key': key}))
            provider.corp_codes.save()
        return provider
    from .sec import SecEdgarProvider
    return SecEdgarProvider(user_agent=sec_user_agent(environ), transport=transport)
