# Recorded adapter fixtures

이 디렉터리의 응답은 **공개 규격 문서를 근거로 합성한 것이며, 라이브 API에서 캡처한 것이
아니다.** 이 저장소가 만들어진 환경의 네트워크 정책이 `data.sec.gov`와
`opendart.fss.or.kr`를 차단하고 OpenDART 키도 없었다.

- **응답 모양**(envelope, 필드명, 콤마 구분 금액 문자열, `013` 빈 결과 상태)은 규격을 따른다.
- **숫자는 예시다.** 여기 있는 어떤 값도 해당 기업의 실제 공시로 읽어서는 안 된다.
- `corp_code`는 삼성전자(`00126380`)를 제외하면 자리표시자다.

생성:

```bash
python scripts/build_dart_fixtures.py
python scripts/build_sec_fixtures.py
```

키와 egress가 생기면 진짜 응답으로 교체한다:

```python
from data_adapters.testing import RecordingTransport
provider = DartProvider(transport=RecordingTransport('data_adapters/fixtures/dart'))
provider.build_financial_pack('267260', '2026-09-18')
```

`fixture_key`가 파일명에서 `crtfc_key`를 제거하므로 기록된 픽스처는 API 키를 담지 않는다.
`tests/test_data_adapters.py`가 이를 검사한다.
