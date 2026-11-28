# 부록 D. 기존 판 이력

[기존 96쪽 판 전체](../../archive_v1/) · [기존 PDF](../../archive_v1/MSE489_HBM적층본더_기말보고서.pdf) · [중간 보고서](../../midterm/)

기존 디렉터리를 mv로 옮겼다. 원고·그림·PDF·스크립트의 바이트는 archive_manifest.json의 SHA256과 대조한다. 보존 기록 안의 옛 절 번호·작성 시각·경로 문자열은 원본 이력이다. v2 본문과 부록 A는 작업 단계로 재작성했다.

build_final.py는 __file__ 기준 ROOT와 fig 상대 경로를 사용한다. 디렉터리 이름을 바꾸어도 동일한 폴더 깊이이며 장·그림 경로는 유지된다. archive 안 README의 예전 실행 경로는 이력으로 남아 있으므로 실제 재빌드는 archive_v1에서 python3 build_final.py를 실행한다.
