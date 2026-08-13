# 태그 앤 다이스 (Tag & Dice)

순수 취미로 만드는 TRPG 룰북 프로젝트입니다.
코드(웹앱, 스크립트)는 [MIT License](LICENSE)를, 게임 콘텐츠(룰, 설정 텍스트)는 [CC BY 4.0](LICENSE-CONTENT.md)을 따릅니다.

## 구성

- `spec.md` — 게임 규칙 스펙 문서
- `design_note_26_base.md` — 디자인 결정 기록 (최신: 26차 개정 — 화면/인쇄 레이아웃 분리 재설계)
- `멀티플레이_방_시스템_설계.md` — 멀티플레이 방 시스템 설계 문서
- `webapp/index.html` — 캐릭터 시트 웹앱. 화면에서는 반응형 웹 레이아웃, 인쇄 시에는 A4 고정 PDF 출력을 지원합니다.
- `webapp/test_app4.py` — 웹앱 회귀 테스트 스위트 (Playwright 기반). 화면 반응형 동작과 인쇄 출력 기하 구조를 함께 검증합니다.
- `render.py`, `build_xlsx.py` — 캐릭터 시트 PDF/XLSX 생성 스크립트
- 데이터 베이스는 파이어 베이스로 구성을 하였고 https://console.firebase.google.com/
- 서버는 깃허브로 열었습니다.

## 룰북 사이트

해당 링크로 접속하면 태그 앤 다이스의 전체적인 규칙을 확인할 수 있습니다.

https://sites.google.com/view/tag-n-dice/%ED%91%9C%EC%A7%80

## 웹앱 사용법

해당 링크로 접속하면 바로 사용할 수 있습니다. 별도 빌드 과정이 없습니다.

https://winti1114.github.io/tagndice/

## 라이선스

- 코드(`webapp/`, `render.py`, `build_xlsx.py`): All Rights Reserved. 자세한 내용은 [LICENSE](LICENSE) 참고.
- 게임 규칙·설정 텍스트(`spec.md`, `멀티플레이_방_시스템_설계.md`): [CC BY 4.0](LICENSE-CONTENT.md) — 출처만 표시하면 자유롭게 이용 가능합니다.

## 참고

이 저장소는 핵심 산출물 위주로 정리되어 있습니다. 작업 중 생성된 스크린샷, 이전 버전 백업, 중간 산출물 등은 저장소에 포함하지 않았습니다.
