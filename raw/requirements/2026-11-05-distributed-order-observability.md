# Distributed order visibility: selected capture

Origin: repository-owner conversation, 2026-11-05. Coverage: selected paraphrases, not a full transcript.
Retention follows the owner's repository knowledge and review-record instructions. No third-party text is copied.

The owner describes a large distributed Elixir system, initially organized as an umbrella project.
Applications communicate through HTTP or HTTPS REST interfaces, without direct cross-application function calls.
The owner wants searchable traces correlated with logs, events and orders, plus analysis and replay across application boundaries.
This is a product target, not a report of implemented behavior or adoption of a particular storage system.
The researcher interprets orders as business orders. Application names and test cases below are proposals.

## Selected primary-source observations

Publisher: OpenTelemetry and Elixir/Mix documentation. Accessed 2026-11-05.
Coverage: selected documentation/search excerpts; no package execution, complete source audit or version pin.

- https://opentelemetry.io/docs/concepts/context-propagation/ : context propagation and trace/span correlation in logs.
- https://opentelemetry.io/docs/concepts/signals/baggage/ : cross-service metadata propagation and sensitive-data/integrity limits.
- https://mix.hexdocs.pm/Mix.Tasks.Release.html : umbrella projects can define releases with selected applications.
  Repository organization alone does not establish separate operating-system processes or network deployment.

Existing retained BEAML sources cover durable history, causal identity, isolated replay and external-effect uncertainty.
No new implementation or runtime result is claimed by this capture.
