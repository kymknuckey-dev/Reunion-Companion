from __future__ import annotations

class SemanticFakeClient:
    """Deterministic local-LLM stand-in for semantic regression tests.

    It never calls Ollama. It returns concise prose containing facts already
    present in the prompt, so legacy tests verify routing/grounding without
    asserting Build 2 renderer labels or depending on model wording.
    """
    def __init__(self):
        self.prompts=[]

    def resolve_model(self):
        return "semantic-test-model"

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        low=prompt.casefold()
        # Chunk-condensation prompts should preserve the concrete supplied fact.
        if 'relevant factual digest:' in low:
            if 'posting and discharge details' in low:
                return 'The record includes posting and discharge details.'
            return 'Relevant facts retained from the supplied Reunion evidence.'

        if 'person: james knuckey' in low:
            if 'working life' in low:
                return 'James Knuckey worked as a carpenter in Gilberton, South Australia, in 1890. His notes also say that he worked locally.'
            if 'marriage' in low:
                return 'James Knuckey married Elizabeth Hunter in Adelaide, South Australia, in 1880.'
            if 'what do the notes say' in low:
                return 'James Knuckey’s authored notes describe his family move and local work. A separate research note says the exact year of the move still needs checking.'
            return 'James Knuckey was born at Tea Tree Gully, South Australia, on 1 June 1857. He worked as a carpenter in Gilberton and married Elizabeth Hunter. His notes say that he moved with his family and worked locally. He died at North Adelaide on 11 July 1910.'

        if 'person: mervyn neil knuckey' in low:
            if 'what do the notes say' in low:
                return 'Mervyn Knuckey’s notes cover his working life, medical history and military service. His military note records that he enlisted in 1952, completed 176 days, and has posting and discharge details.'
            if 'military service' in low:
                return 'Mervyn Knuckey enlisted in 1952 and completed 176 days of service before returning to Adelaide. His military record also contains posting and discharge details.'
            if 'working life' in low:
                return "Mervyn Knuckey worked at A.M. Bickford & Sons and later at Rawson's Electrical. Reunion records his later occupation as a Public Servant with the S.A. Health Commission, from which he retired."
            if 'marriage' in low:
                return 'Mervyn Knuckey married Elaine Fay Cox in Adelaide, South Australia, in 1954.'
            return 'Mervyn Knuckey’s Reunion record contains information about his work, military service and medical history.'

        return 'The supplied Reunion evidence has been synthesised into a grounded answer.'
