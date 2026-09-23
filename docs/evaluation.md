# Evaluation results

Recorded on 23 September 2026 using local Ollama with qwen2.5:7b-instruct.

| Check | Result |
| --- | --- |
| Offline regression suite | 7/7 passed |
| Synthetic postings: four fields across three postings | 12/12 (100%) |
| Five real postings: original prompt | 12/20 (60%) |
| Same five postings: clarified prompt | 14/20 (70%) |

Real-posting references were AI-assisted, prepared before inference, and were not
independently human-labelled. The five examples informed prompt tuning. The 70%
result is same-set agreement, not held-out accuracy. All five extractions succeeded.

The prompt clarification asks the model not to infer employment type or working
arrangement when unstated. It corrected two unsupported guesses in one posting.
Three unsupported Full-time predictions remain. Two seniority differences involve
judgement; one advert gives conflicting working-arrangement information. Another
offers both full-time and part-time, which the single-value schema cannot fully
represent. All five real texts omit sponsorship wording, so this set cannot measure
performance on real sponsorship offers or refusals.

Raw real adverts, source notes and local reports are excluded from the public
repository. Consequently, that recorded score cannot be reproduced from this
repository alone. The synthetic fixtures and offline tests are included. To run a
new real-posting evaluation, follow the collection and labelling steps in README.md.
Independent, unseen examples are needed before making broader accuracy claims.
