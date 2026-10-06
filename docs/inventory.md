# 문서 규칙 인벤토리

이 문서는 `rules/registry.toml`에서 `tools/render_inventory.py`로 생성합니다. 직접 고치지 않습니다.

레지스트리 상태: draft. 기준선: VCF 9.1.1 / PAIF 9.1.1 / PAIS 3.0

## 요약

| 구분 | 규칙 수 |
|------|--------:|
| 전체 | 51 |
| 수준: 오류 | 11 |
| 수준: 경고 | 19 |
| 수준: 리뷰 | 21 |
| 상태: 범위 확대 | 8 |
| 상태: 문서 규칙만 존재 | 19 |
| 상태: 신규 | 20 |
| 상태: 충돌 정리 | 4 |
| skill-vault를 출처로 포함 | 14 |

## 기호

| ID | 규칙 | 수준 | 방식 | 적용 범위 | 상태 | 출처 |
|----|------|------|------|-----------|------|------|
| SYM-TILDE | 물결(~) 사용 금지 | 오류 | 정규식 | 전체 | 범위 확대 | vcf-private-ai/CONVENTIONS.md 7절<br>전역 지침 03<br>skill-vault:CONTRIBUTING.md 표기 |
| SYM-EMOJI | 이모지 사용 금지 | 오류 | 정규식 | 전체 | 범위 확대 | vcf-private-ai/CONVENTIONS.md 7절<br>전역 지침 01<br>skill-vault:CONTRIBUTING.md 표기<br>skill-vault:skills/pptx-design-system/references/text-rules.md |
| SYM-MIDDOT | 가운뎃점 사용 금지 | 오류 | 정규식 | 전체 | 충돌 정리 | vcf-private-ai/CONVENTIONS.md 7절<br>skill-vault:skills/narrative-architect/principles/anti-ai-tell.md 3-1-2절 |
| SYM-SECTION | 절 기호와 단락 기호 사용 금지 | 오류 | 정규식 | 전체 | 범위 확대 | vcf-private-ai/CONVENTIONS.md 7절<br>skill-vault:skills/narrative-architect/principles/anti-ai-tell.md 3-1-3절 |
| SYM-RANGE | 숫자 범위는 en dash(–)로 표기 | 경고 | 정규식 | 전체 | 충돌 정리 | vcf-private-ai/CONVENTIONS.md 7절<br>세 저장소 CLAUDE.md 대시 규칙의 예외 조항 |

## 대시

| ID | 규칙 | 수준 | 방식 | 적용 범위 | 상태 | 출처 |
|----|------|------|------|-----------|------|------|
| DASH-JOIN | 두 구를 em dash(—)로 잇는 구조 금지 | 오류 | 정규식 | 전체 | 범위 확대 | vcf-private-ai/CLAUDE.md 문장 규칙 3<br>vcf-private-ai-apps/CLAUDE.md 규칙 3<br>enterprise-ax-methodology/CLAUDE.md 3절<br>전역 지침 00<br>skill-vault:skills/narrative-architect/principles/anti-ai-tell.md 3-1-1절 |
| DASH-HYPHEN-JOIN | 두 구를 공백 낀 하이픈( - )으로 잇는 구조 금지 | 경고 | 정규식 | 전체 | 신규 | 전역 지침 00<br>skill-vault:skills/narrative-architect/principles/anti-ai-tell.md 3-1-1절 |
| DASH-SUBSTITUTE | 대시를 콜론이나 괄호로 단순 치환 금지 | 리뷰 | Claude 리뷰 | 전체 | 문서 규칙만 존재 | 세 저장소 CLAUDE.md 대시 규칙<br>전역 지침 00<br>skill-vault:skills/narrative-architect/principles/anti-ai-tell.md 3-1-1절 |

## 구조

| ID | 규칙 | 수준 | 방식 | 적용 범위 | 상태 | 출처 |
|----|------|------|------|-----------|------|------|
| STR-H1 | 문서 H1 형식 | 오류 | 구조 | vcf-private-ai, vcf-private-ai-apps, enterprise-ax-methodology | 범위 확대 | vcf-private-ai/CONVENTIONS.md 3절<br>vcf-private-ai-apps/CLAUDE.md 규칙 3 예외 조항<br>enterprise-ax-methodology 관행(문서화되지 않음) |
| STR-HEADING-NUMBER | 본문 헤딩 번호 체계(H2 N.M, H3 N.M.K, H4 이하 무번호) | 경고 | 구조 | vcf-private-ai, vcf-private-ai-apps, enterprise-ax-methodology | 범위 확대 | vcf-private-ai/CONVENTIONS.md 4절 |
| STR-META-UNNUMBERED | 메타 섹션(참고 출처, 요약, 면책)은 무번호 | 경고 | 구조 | vcf-private-ai, vcf-private-ai-apps, enterprise-ax-methodology | 문서 규칙만 존재 | vcf-private-ai/CONVENTIONS.md 5절 |
| STR-CIRCLED-HEADING | 본문 헤딩에 원숫자(①②) 사용 금지 | 오류 | 구조 | vcf-private-ai | 문서 규칙만 존재 | vcf-private-ai/CONVENTIONS.md 1절 |
| STR-FILE-LAYOUT | 파일 배치와 이름(docs/NN-slug.md, appendix/AN-slug.md, docs/E0-*.md) | 오류 | 구조 | vcf-private-ai | 문서 규칙만 존재 | vcf-private-ai/CONVENTIONS.md 2절 |
| STR-LABEL | 라벨형 문장은 **라벨.** 본문 형식, 질문형 라벨은 물음표로 종결 | 오류 | 정규식 | 전체 | 문서 규칙만 존재 | 세 저장소 CLAUDE.md 대시 규칙 |
| STR-NO-FORM | 빈칸을 채우는 양식 금지 | 경고 | 구조 | 전체 | 신규 | 세 저장소 CLAUDE.md 작성 원칙(양식 대신 운영 기준, 안내와 양식의 분리)<br>vcf-private-ai/CONVENTIONS.md 2절 |
| STR-CALC-TABLE-TERM | 본문 안의 계산 표는 '산정 표'로 지칭 | 경고 | 단어 목록 | vcf-private-ai, vcf-private-ai-apps | 문서 규칙만 존재 | vcf-private-ai/CLAUDE.md 작성 원칙<br>vcf-private-ai-apps/CLAUDE.md 작성 원칙 |
| STR-CODE-FENCE | 코드 펜스는 실제 코드와 마크업에만 사용 | 리뷰 | Claude 리뷰 | 전체 | 신규 | 전역 지침 03 |

## 링크

| ID | 규칙 | 수준 | 방식 | 적용 범위 | 상태 | 출처 |
|----|------|------|------|-----------|------|------|
| LINK-TARGET | 상대 링크, 앵커, 저장소 간 링크의 대상 존재 | 오류 | 링크 | 전체 | 범위 확대 | vcf-private-ai/verify_repo.py LINK<br>세 저장소 CLAUDE.md 고칠 때의 원칙(앵커 링크 확인) |
| LINK-TEXT | 다른 문서를 가리키는 링크 텍스트는 문서 번호와 제목으로 작성 | 경고 | 정규식 | vcf-private-ai, vcf-private-ai-apps | 문서 규칙만 존재 | vcf-private-ai/CLAUDE.md 문장 규칙 3<br>vcf-private-ai/CONVENTIONS.md 6절<br>vcf-private-ai-apps/CLAUDE.md 규칙 3 |
| LINK-XREF | 상호참조는 'N.M절', 다른 편은 '시리즈 ④의 2.3절' 형식 | 리뷰 | Claude 리뷰 | vcf-private-ai | 문서 규칙만 존재 | vcf-private-ai/CONVENTIONS.md 6절 |

## 어휘

| ID | 규칙 | 수준 | 방식 | 적용 범위 | 상태 | 출처 |
|----|------|------|------|-----------|------|------|
| WORD-ONE-SYLLABLE | 한 글자 동사로 문장을 끝내지 않기 | 경고 | 단어 목록 | 전체 | 문서 규칙만 존재 | 세 저장소 CLAUDE.md 규칙 1<br>전역 지침 style(동사·은유 표현) |
| WORD-GE-DOEDA | 결과의 …게 됩니다, 사물 주어 사역의 …게 합니다, 뜻이 흐린 …이 됩니다를 실제 동사로 교체 | 경고 | 정규식 | 전체 | 문서 규칙만 존재 | 세 저장소 CLAUDE.md 규칙 1<br>전역 지침 style |
| WORD-SPATIAL | 방향과 공간 은유, 비유 대신 실제 동작 사용 | 경고 | 단어 목록 | 전체 | 문서 규칙만 존재 | 세 저장소 CLAUDE.md 규칙 2<br>vcf-private-ai-apps/CLAUDE.md 이 저장소에서 정한 대체어<br>전역 지침 style(방향·공간 은유) |
| WORD-TRANSLATIONESE | 번역투 표현 회피 | 경고 | 단어 목록 | 전체 | 신규 | 전역 지침 style(번역투)<br>skill-vault:skills/narrative-architect/principles/prose-voice.md 1절<br>skill-vault:skills/narrative-architect/principles/anti-ai-tell.md 3-1절 |
| WORD-CLICHE | 근거 없는 상투어 금지 | 경고 | 단어 목록 | 전체 | 신규 | skill-vault:skills/narrative-architect/principles/anti-ai-tell.md 3절 |
| WORD-QUOTED-HEADLINE | 제목에 따옴표 사용 금지 | 경고 | 정규식 | 전체 | 신규 | 전역 지침 02 |

## 내용

| ID | 규칙 | 수준 | 방식 | 적용 범위 | 상태 | 출처 |
|----|------|------|------|-----------|------|------|
| CNT-SOURCE | 수치와 사실 주장에 공식 출처 링크 표기 | 경고 | 정규식 | 전체 | 신규 | 세 저장소 CLAUDE.md 작성 원칙(출처 확인)<br>전역 지침 06<br>skill-vault:skills/vcf-korea-ea/SKILL.md 출처 규칙 |
| CNT-UNVERIFIED | 공식 문서로 확인되지 않은 내용은 '확인 필요'로 표시 | 리뷰 | Claude 리뷰 | 전체 | 충돌 정리 | 세 저장소 CLAUDE.md 작성 원칙(출처 확인) |
| CNT-NOT-GA | 발표만 된 기능은 GA 전까지 본문에 반영하지 않음 | 경고 | 단어 목록 | vcf-private-ai, vcf-private-ai-apps, JaeHoYun | 신규 | 세 저장소 CLAUDE.md 작성 원칙(출처 확인)<br>전역 지침 vcf_guardrail |
| CNT-BASELINE | 기준선 선언 문구와 버전 표기 | 경고 | 정규식 | vcf-private-ai, vcf-private-ai-apps, JaeHoYun | 충돌 정리 | vcf-private-ai/CONVENTIONS.md 8절<br>vcf-private-ai/CLAUDE.md 작성 원칙(기준선)<br>vcf-private-ai-apps/CLAUDE.md 작성 원칙(기준선) |
| CNT-VENDOR-NEUTRAL | AX 가이드는 벤더 중립, 제품 버전을 전제하지 않음 | 경고 | 정규식 | enterprise-ax-methodology | 신규 | enterprise-ax-methodology/CLAUDE.md 5절 작성 원칙(기준선) |
| CNT-ANONYMIZE | 특정 기업 사례 금지, 업종과 업무 유형 수준으로 일반화 | 오류 | 단어 목록 | 전체 | 신규 | 세 저장소 CLAUDE.md 작성 원칙(익명화) |
| CNT-JUDGMENT | 적합한 경우, 적합하지 않은 경우, 장단점을 함께 서술 | 리뷰 | Claude 리뷰 | 전체 | 문서 규칙만 존재 | 세 저장소 CLAUDE.md 작성 원칙(판단 기준) |
| CNT-MISFIT | 권하는 접근이 맞지 않는 조건과 그때의 대안을 서술 | 리뷰 | Claude 리뷰 | 전체 | 문서 규칙만 존재 | 세 저장소 CLAUDE.md 작성 원칙(맞지 않는 조건도 적기) |
| CNT-FIVE-ELEMENTS | 운영 기준은 무엇을, 어떤 기준으로, 누가 언제, 어떻게 측정, 어떻게 개선의 다섯 요소로 서술 | 리뷰 | Claude 리뷰 | vcf-private-ai, vcf-private-ai-apps | 문서 규칙만 존재 | vcf-private-ai/CLAUDE.md 작성 원칙(양식 대신 운영 기준)<br>vcf-private-ai-apps/CLAUDE.md 작성 원칙 |
| CNT-FILLED-EXAMPLE | AX 가이드는 양식 대신 끝까지 채운 가상 예시 수록 | 리뷰 | Claude 리뷰 | enterprise-ax-methodology | 문서 규칙만 존재 | enterprise-ax-methodology/CLAUDE.md 5절(안내와 양식의 분리) |
| CNT-SOURCE-QUALITY | 핵심 수치는 1차 출처까지 추적, 통제 실험인지 조건이 다른 비교인지 구분 | 리뷰 | 소유자 확인 | 전체 | 신규 | 전역 지침 judgment(1차 출처 추적) |

## 문체

| ID | 규칙 | 수준 | 방식 | 적용 범위 | 상태 | 출처 |
|----|------|------|------|-----------|------|------|
| PRS-CONCLUSION-FIRST | 결론을 먼저, 근거를 뒤에 | 리뷰 | Claude 리뷰 | 전체 | 신규 | 전역 지침 style<br>skill-vault:skills/narrative-architect/principles/prose-voice.md 3절 |
| PRS-ONE-MEANING | 한 문장에 한 의미, 주어와 서술어를 가깝게 배치 | 리뷰 | Claude 리뷰 | 전체 | 신규 | 전역 지침 style |
| PRS-TERM-FIRST-USE | 핵심 용어는 처음 나올 때 주어와 동작을 갖춘 문장으로 정의, 같은 산출물 안에서 반복 설명 금지 | 리뷰 | Claude 리뷰 | 전체 | 신규 | 전역 지침 style(개념 설명 방식)<br>skill-vault:skills/narrative-architect/principles/prose-voice.md 2절 |
| PRS-PAREN-CONFLATE | A(B) 괄호 병기로 서로 다른 두 개념을 묶지 않음 | 경고 | 정규식 | 전체 | 신규 | 전역 지침 style(개념 설명 방식) |
| PRS-ABSTRACT-NOUN | 계층, 구조, 루프 같은 추상 명사로 끝나는 설명을 실제 동작 서술로 교체 | 리뷰 | Claude 리뷰 | 전체 | 신규 | 전역 지침 style(개념 설명 방식) |
| PRS-NOUN-CHAIN | 명사구 3개 이상 연쇄 금지, 동사문으로 분해 | 리뷰 | Claude 리뷰 | 전체 | 신규 | skill-vault:skills/narrative-architect/principles/anti-ai-tell.md 3-1절<br>skill-vault:skills/narrative-architect/principles/prose-voice.md 1절 |
| PRS-TONE | 전문가 대 전문가 어조. 강의식, 연출된 문답, 과장 금지 | 리뷰 | Claude 리뷰 | 전체 | 신규 | skill-vault:skills/narrative-architect/principles/prose-voice.md 3절 |
| PRS-TERM-CONSISTENT | 한 단락에서 같은 개념은 한 용어로 통일 | 리뷰 | Claude 리뷰 | 전체 | 문서 규칙만 존재 | vcf-private-ai/CLAUDE.md 고칠 때의 원칙<br>vcf-private-ai-apps/CLAUDE.md 작업 방식 3 |

## 작업 절차

| ID | 규칙 | 수준 | 방식 | 적용 범위 | 상태 | 출처 |
|----|------|------|------|-----------|------|------|
| PROC-SWEEP | 교정 요청을 받으면 같은 계열 표현을 전체에서 먼저 검색해 목록으로 제시하고 한 번에 처리 | 리뷰 | 작업 절차 | 전체 | 문서 규칙만 존재 | 세 저장소 CLAUDE.md 교정 방식<br>전역 지침 style(교정 방식) |
| PROC-RENAME-SYNC | 제목을 바꾸면 요약, 목차, README, 다른 장의 참조 문구를 함께 갱신 | 리뷰 | 작업 절차 | 전체 | 문서 규칙만 존재 | 세 저장소 CLAUDE.md 교정 방식 |
| PROC-RECHECK | 고친 문장도 규칙을 지키는지 다시 확인 | 리뷰 | 작업 절차 | 전체 | 문서 규칙만 존재 | 세 저장소 CLAUDE.md 교정 방식 |
| PROC-VERIFY-BEFORE-COMMIT | 커밋 전 검증 스크립트를 실행해 오류 0건 확인 | 리뷰 | 작업 절차 | 전체 | 범위 확대 | vcf-private-ai/CLAUDE.md 고칠 때의 원칙 |
| PROC-MERGE-AFTER-CHECK | 필수 상태 검사 통과 후 머지, Claude 리뷰 지적마다 수정 또는 사유 회신 | 리뷰 | 작업 절차 | 전체 | 신규 | 이슈 vcf-private-ai#66 결정 D7, D8 |

## 저장소 설정값

| ID | 규칙 | 수준 | 방식 | 적용 범위 | 상태 | 출처 |
|----|------|------|------|-----------|------|------|
| META-REPO-DESCRIPTION | GitHub 저장소 설명(About)에도 기호, 대시, 은유 규칙 적용 | 경고 | 저장소 설정값 | 전체 | 신규 | 이슈 vcf-private-ai#66 결정 D13 |

## 충돌 기록

| ID | 주제 | 각 출처의 입장 | 정리 방침 | 근거 결정 |
|----|------|----------------|-----------|-----------|
| C1 | 숫자 범위 표기 | 저장소 규칙: en dash(3–5)<br>전역 지침 03: 하이픈(3-5) | 가이드 저장소는 en dash. 전역 지침에 저장소 문서 예외 문구를 추가한다(사용자 조치). | D2-a |
| C2 | 가운뎃점 | CONVENTIONS 7절과 skill-vault anti-ai-tell 3-1-2절: 금지<br>전역 지침 03: 사용법을 규정해 허용 | 가이드 저장소 전체에서 금지. 전역 지침 03의 가운뎃점 조항을 수정한다(사용자 조치). | D2-a |
| C3 | 기준선 버전 | 가이드 저장소: VCF 9.1.1 / PAIF 9.1.1 / PAIS 3.0<br>전역 지침 08: VCF 9.1 / PAIF 9.1<br>전역 지침 vcf_guardrail: 9.0.x<br>skill-vault vcf-korea-ea: VCF 9.1 / PAIF 9.1 / PAIS 2.1, paif-positioning.md:47에만 PAIS 3.0 | 레지스트리 baseline 값이 가이드 저장소의 기준. 전역 지침 두 조항은 사용자가 정리한다. skill-vault는 변경하지 않고 차이만 보고한다. | D2-a, 기준선-가, skill-vault-가 |
| C4 | 대시 연결 금지의 범위 | 저장소 규칙: em dash만<br>전역 지침 00과 anti-ai-tell 3-1-1절: 공백 낀 하이픈까지 | em dash는 오류(DASH-JOIN), 공백 낀 하이픈은 경고(DASH-HYPHEN-JOIN)로 둘 다 적용한다. | D2-a, D6-a |
| C5 | 미확인 사실 표기 | 가이드 저장소: '확인 필요'로 표시<br>skill-vault anti-ai-tell 3-2절: 산출물에 미해결 라벨 금지 | 산출물 종류별로 분리한다. 공개 가이드는 표기를 유지하고, 고객 산출물(슬라이드, 제안서) 규칙은 skill-vault가 그대로 관리한다. | 확인필요-가 |
| C6 | skill-vault 내부 모순: 슬래시를 나열 기호로 사용 | skill-vault CONTRIBUTING.md: 가운뎃점 대신 쉼표나 슬래시<br>skill-vault anti-ai-tell 3-1-2절: 슬래시는 양자택일에만 | 가이드 저장소는 anti-ai-tell 기준(쉼표 나열)을 따른다. skill-vault 내부 모순은 보고만 하고 수정하지 않는다. | skill-vault-가 |
| C7 | 전역 지침 00의 우선순위 조항 | 전역 지침 00: 전역 지침이 저장소 CLAUDE.md보다 우선<br>결정 D2-a: 저장소 문서에는 저장소 규칙 우선 | 전역 지침 00에 '저장소 문서는 해당 저장소 규칙과 guide-tooling 레지스트리를 따른다'는 예외를 추가한다(사용자 조치). | D2-a |

## 저장소 프로필

| 프로필 | 저장소 | H1 형식 | 기준선 적용 | CONVENTIONS 적용 |
|--------|--------|---------|-------------|------------------|
| vcf-private-ai | JaeHoYun/vcf-private-ai | `# 05 — 제목` | 예 | 예 |
| vcf-private-ai-apps | JaeHoYun/vcf-private-ai-apps | `# 05 — 제목` | 예 | 아니요 |
| enterprise-ax-methodology | JaeHoYun/enterprise-ax-methodology | `# 03. 제목` | 아니요 | 아니요 |
| JaeHoYun | JaeHoYun/JaeHoYun | — | 예 | 아니요 |
