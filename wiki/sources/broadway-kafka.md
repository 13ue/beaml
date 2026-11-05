---
id: source-broadway-kafka
kind: source-note
status: selected-primary-research
updated: 2026-11-05
---

# Broadway, GenStage and Kafka

**[Verified]** Selected official documentation and source were read on 2026-11-05. Publishers are the Broadway, GenStage and Apache Kafka projects.
The [selected record](../../raw/research/event-streams/2026-11-05-selected-record.md) and [provenance](../../raw/research/event-streams/2026-11-05-provenance.json) preserve pins, retrieval limits and capture integrity.
Only original paraphrases are retained. No upstream implementation is copied or licensed as BEAML code.

| Source | Version and selected evidence | Boundary |
|---|---|---|
| [Broadway documentation](https://broadway.hexdocs.pm/1.3.0/Broadway.html) | v1.3.0; acknowledgement/failures, ordering/partitioning, producer concurrency and shutdown | Concurrent pipeline with batching and acknowledgement hooks; not persistent history. |
| [Broadway source](https://github.com/elixir-broadway/broadway/blob/d3a668c885342ae223b5ebcd9571efe4a0f18c41/lib/broadway.ex) | v1.3.0 resolved to d3a668c885342ae223b5ebcd9571efe4a0f18c41 | Source documentation confirms selected pipeline contracts; no full runtime audit. |
| [BroadwayKafka documentation](https://broadway-kafka.hexdocs.pm/BroadwayKafka.Producer.html) | Displayed v0.7.1; failed messages, offsets, fetch limits, membership | Consumer connector using brod; failed messages are acknowledged. |
| [Acknowledgement source](https://github.com/elixir-broadway/broadway_kafka/blob/dedd507e72b90ba2ef231286be811bb14b522026/lib/broadway_kafka/acknowledger.ex) | v0.7.1 commit dedd507e72b90ba2ef231286be811bb14b522026; `ack/3`, `update_current_offset/3` | Successful and failed offsets enter the same acknowledgement path. Earlier outstanding deliveries delay offset advancement. |
| [Producer source](https://github.com/elixir-broadway/broadway_kafka/blob/dedd507e72b90ba2ef231286be811bb14b522026/lib/broadway_kafka/producer.ex#L259) | `handle_call(:drain_after_revoke,...)`, `handle_info({:ack,...})`, `prepare_for_draining/1`, `assignments_revoked/1` | Draining coordinates in-flight work; hard failure can still leave duplicate delivery or uncertain external outcomes. |
| [GenStage](https://gen-stage.hexdocs.pm/1.3.2/GenStage.html#module-demand) | v1.3.2; source commit d1532fa56482bc92d90abc777439ff8be34b5b1a | Demand is tracked per producer subscription. Stages model runtime flow, not domain decomposition. |
| [Kafka design](https://kafka.apache.org/44/design/design/#message-delivery-semantics) | 4.4; delivery, transactions, log compaction | Kafka transactions coordinate offsets and Kafka outputs. External destinations require cooperation. |
| [Topic configuration](https://kafka.apache.org/44/configuration/topic-configs/) | 4.4; `cleanup.policy`, `retention.ms`, `retention.bytes`, `delete.retention.ms` | Replay has a retained-range limit. Compaction can remove intermediate values and expired tombstones. |
| [Monitoring](https://kafka.apache.org/44/operations/monitoring/#consumer-monitoring) | 4.4; lag, consumption rate and fetch metrics | Java-client lag metrics distinguish current from committed position; brod instrumentation needs separate checking. |

**[Verified]** Broadway retries are producer-dependent. Generic partitioning continues after failures, so later retry can change business ordering.
BroadwayKafka commit intervals affect duplicate exposure. More memory can be consumed by larger fetches.
Its supported group and fetch options must be checked directly, rather than copied from Java-client configuration.
[Failure/ordering](https://broadway.hexdocs.pm/1.3.0/Broadway.html#module-ordering-and-partitioning), [connector options](https://broadway-kafka.hexdocs.pm/BroadwayKafka.Producer.html#module-options)

**[Unknown]** No complete brod audit, version-tuple interoperability test or throughput measurement was performed.
The accessible Broadway module page displayed 1.3.0; another guide displayed 1.3.1 with old setup examples.
Inaccessible version-specific pages and resolved source pins are recorded in provenance.
These packages are researched options, not selected BEAML dependencies. [Flow proposal](../concepts/event-flows-and-backpressure.md)
