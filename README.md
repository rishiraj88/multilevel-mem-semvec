# The Family Chronicle
- Medium difficulty
- 8–16 hours project

Every family member feeds in memories; a shared Cortex weaves a searchable family history from multiple perspectives.

## Breaks without Semvec
- Multi-source memory with cross-perspective recall is exactly where RAG tends to pull contradictory fragments instead of one coherent shared state. This is the cleanest Cortex demo without an ethics minefield.

## Building block
- B4, one instance per person with shared family knowledge, or a REST cluster via `/v1/cluster/{id}/store` and `/run`.

## Demo
- Three family members each seed five memories; a cross-perspective question ("who was at the wedding?") gets answered coherently.
