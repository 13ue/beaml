# Event-stream research record

Status: selected primary-source inspection.
Retrieved: 2026-11-05.
Coverage: official documentation and selected source functions only. No deployment, benchmark, broker test or connector execution.
Retention: original short paraphrases. No upstream implementation copied. Upstream copyrights and licenses remain with their publishers.

## Source pins

- Broadway v1.3.0: d3a668c885342ae223b5ebcd9571efe4a0f18c41. Selected official module documentation covers acknowledgement, ordering and shutdown.
- BroadwayKafka v0.7.1: dedd507e72b90ba2ef231286be811bb14b522026. Its annotated tag object is bac8ce2c02194202430ed2d76d9be4fdeee34c90.
- GenStage v1.3.2: d1532fa56482bc92d90abc777439ff8be34b5b1a. Selected demand and usage guidance inspected.
- Kafka documentation: versioned 4.4 site. Design, topic configuration and monitoring sections inspected. Documentation is mutable within that version.

## Selected observations

Broadway supplies processing stages, batching and acknowledgements. Parallel execution does not imply business ordering. Its failure callback precedes acknowledgement, with connector-specific consequences.

BroadwayKafka acknowledges failed records. Delayed commits can increase duplicate processing after failure. Its fetch limits trade throughput against memory. Consumer membership and assigned partitions constrain useful producer concurrency.

The pinned acknowledger combines successful and failed offsets. Pending offsets prevent advancement across earlier outstanding deliveries. Revocation drains dispatched records and resets undispatched buffers. Shutdown stops further fetching. These are source observations, not measured fault tolerance.

GenStage sends demand upstream and tracks demand separately per producer. Demand governs participating stages, not arbitrary external senders or unbounded application queues.

Kafka coordinates Kafka outputs and offsets through transactions. External effects require destination cooperation. Retained records can be read again, but retention and compaction limit available history.

Topic retention is controlled by time, bytes and cleanup policy. Compaction preserves selected keyed state, not every historical transition. Consumer lag must be interpreted alongside the actual retained range.

Monitoring documentation distinguishes fetched position from committed position. Its Java-client JMX metrics are not an automatic promise about the Erlang client.

## Retrieval limits

The unversioned Broadway module page displayed 1.3.0. Its Kafka guide displayed 1.3.1 during earlier research but contained historical setup examples.
Version-specific 1.3.1 module and 0.7.1 connector HexDocs URLs were inaccessible through the web tool. The accessible connector page displayed 0.7.1.
Pinned GitHub connector source supplied the exact acknowledgement and drain behavior. No full brod implementation audit or Kafka 4.4 interoperability test was performed.
