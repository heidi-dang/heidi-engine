# Dataset Lifecycle

Heidi Engine follows a strict, verifiable path for data.

1. **raw**: Direct output from teacher model generation.
2. **clean**: After syntax validation, deduplication, and secret scrubbing.
3. **verified**: After passing semantic validation and optional unit test gates.
4. **rejected**: Samples that failed any of the above stages.
5. **train**: The final dataset used for fine-tuning.
6. **validation**: Hold-out set used for evaluation.

Movement between stages is managed by the Runtime Engine and recorded in the event journal.
