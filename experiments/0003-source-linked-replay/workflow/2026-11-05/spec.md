# Run the source-linked replay EXPERIMENT (0003)

**[Requirement]** The user authorized the bounded implementation described in the [EXPERIMENT specification](../../README.md). This record uses that specification as the acceptance contract. The user has not waived or preauthorized the RED review checkpoint.

Use exactly two successful synthetic Orders calls for the live window. Query `payments.authorize` by artifact and SOURCE ID. Verify the checked compiler reference, the original declaration and the remote-parent trace edge. Use a second compiled build with the same function name as a lookup control.

Record the first call's prepared request and observed HTTP response before decode. Replay it through the original Orders decode, finish and validation path after stopping both live releases. Show one attempted outbound connection per live call and zero during replay. Test the observer with a positive control. Report a specific gap or divergence for missing or mismatched replay evidence.

Keep versioned capture and same-run build evidence. Preserve failed runs. Use synthetic fixtures and loopback. Append use-case events without source text, input paths or secrets.

This work excludes a full UI, LSP, Cloud, LLM, and Ecto or LiveView integration. Keep earlier EXPERIMENT changes limited to a necessary seam. Commits, pushes, new chats and external publication require separate authorization.
