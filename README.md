# ContextualForget — Digital Twin Graph-RAG with Long-Term Memory (Forgetting)

**IFC(정적 구조) + BCF(동적 이슈)**를 하나의 그래프로 묶고, **TTL/감쇠/요약압축** 망각을 적용해
"무엇이/어디서/언제/왜 바뀌었는가"를 **근거와 함께** 답하는 오프라인 파이프라인입니다.

## Quickstart
```bash
source .venv/bin/activate
make all
ctxf query --guid 1kTvXnbbzCWw8lcMd1dR4o --ttl 365 --topk 5

Outputs

data/processed/graph.gpickle : 통합 그래프

CLI JSON: 관련 BCF 토픽, 생성시각, IFC GUID로의 간선(근거)

results/ : 평가 결과 (make eval)

대형 파일은 Git LFS 규칙을 사용합니다(.gitattributes).