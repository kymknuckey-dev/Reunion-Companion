# FFD 2.0 RC1.0.7 — Global Ask Identity Resolution QA Pass 1

Global Ask now applies the same identity-discovery discipline used by Search before answering a fact question.

- A unique full recorded name may answer immediately.
- A two-token partial name with multiple credible direct candidates remains explicit and selectable rather than silently choosing one record.
- `Merv` is treated conservatively as a search variation of `Mervyn`; this does not change Reunion's recorded name.
- Selecting a candidate answers the original question in that same turn and establishes the person context.
- Existing spouse-surname discovery such as `Susan Knuckey` remains unchanged.

This repair prevents a plausible but wrong literal-name record from producing false “no information” answers when another candidate is the intended person.
