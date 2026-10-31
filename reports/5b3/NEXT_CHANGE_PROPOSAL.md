# Narrow follow-up proposal — review required, not implemented

Problem: a live planner returned `[]`. The shared client raised ModelError before
the calculation gate could preserve a rejected proposal. The 60-case run stopped.

1. Add a typed invalid-structured-reply exception retaining the raw reply. Keep
network/authentication/timeout failures distinct; do not broadly catch ModelError.
2. At the answer planner boundary only, turn that typed protocol error into an
explicit unverified-answer status with the original reply and fetched references.
Do not coerce arbitrary numbers into cells or pretend malformed JSON met the schema.
3. Record failed as well as successful API calls, with stage and timing. No keys.
4. Add integration tests through MockTransport and the real ModelClient/Pipeline:
empty array, invalid JSON, missing outputs, fabricated operands and service failure.
Assert that no unsupported result is rendered as fact and transport failures remain
visible. Existing questions/evaluator/retrieval stay frozen.
5. After Kiddi/Gisli review and Silli's required go, freeze a new executable commit
and run the same 60 open cases. Preserve this incomplete attempt and earlier 4/60
and 7/60. Do not retune category selection or prompts from these answer keys.

Separate audit concern: model-supplied dimension_scope remains semantic evidence,
not a proof that no subgroup was requested. Review this explicitly without widening
the current implementation or silently relaxing the acceptance gates.

No merge, closed tests, new GPU/storage, stop or restart is authorized by this proposal.
