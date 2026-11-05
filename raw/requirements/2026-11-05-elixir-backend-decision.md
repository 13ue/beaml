# Initial backend decision

Origin: owner-supplied conversation in the BEAML project on 2026-11-05.
Coverage: selected paraphrase of the backend decision, not a full transcript.
Publisher: repository owner. Status: adopted initial direction.
Rights: original project requirement note; no third-party text copied.

Use generated Elixir source as the initial BEAML backend.
The Elixir compiler and OTP compiler produce BEAM modules for execution on the BEAM VM.
This adopts the route already exercised by EXPERIMENT 0001.
It does not commit the project to direct BEAM assembly or bytecode emission later.

Limits: no permanent backend choice, performance comparison, production support matrix or new implementation claim follows from this decision.
