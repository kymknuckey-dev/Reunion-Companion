from reunion_companion.companion.database import connect
from reunion_companion.companion.knowledge_conversation import answer_knowledge_question
from test_ffd_1_8_build1_1_query_consistency_hardening import seed, FakeClient


def test_short_followup_inherits_previous_netball_topic(tmp_path):
    db = connect(tmp_path/'x'); seed(db); c = FakeClient()
    r = answer_knowledge_question(
        db, 1, 'Did she play for Australia?', prior_intent='topic:netball', client=c
    )
    assert r['status'] == 'ok'
    assert r['knowledge_intent'] == 'topic:netball'
    prompt = c.prompts[-1].casefold()
    assert 'netball' in prompt and 'basketball' in prompt
    assert 'did she play for australia' in prompt


def test_explicit_new_domain_overrides_previous_topic(tmp_path):
    db = connect(tmp_path/'x'); seed(db); c = FakeClient()
    r = answer_knowledge_question(
        db, 1, 'What health issues did she have?', prior_intent='topic:netball', client=c
    )
    # There is no Elaine medical evidence in the fixture, but critically the
    # question must not inherit netball just because it is a short follow-up.
    assert r['knowledge_intent'] == 'topic:medical'


def test_residence_scope_excludes_workplace_only_sentences(tmp_path):
    db = connect(tmp_path/'x'); seed(db)
    db.execute(
        "UPDATE notes SET text=? WHERE id=23",
        ('Mervyn worked as a customs clerk at the shipping office in Port Adelaide. '
         'He and Elaine built new homes at Elizabeth Avenue, Glenalta and Cudmore Road, Victor Harbor. '
         'In retirement they moved to Forest Place Retirement Village in Happy Valley. '
         'They later settled into a leased residence at 5 Anne Court, Happy Valley.',)
    )
    db.commit()
    c = FakeClient()
    r = answer_knowledge_question(db, 2, 'Where did he live during his lifetime?', client=c)
    assert r['status'] == 'ok'
    prompt = c.prompts[-1].casefold()
    assert 'elizabeth avenue' in prompt
    assert 'forest place retirement village' in prompt
    assert '5 anne court' in prompt
    assert 'customs clerk' not in prompt
    assert 'shipping office' not in prompt


def test_research_gap_prompt_contains_known_family_relationships(tmp_path):
    db = connect(tmp_path/'x'); seed(db); c = FakeClient()
    r = answer_knowledge_question(
        db, 2, 'Where are the gaps in the timeline that need more search work?', client=c
    )
    assert r['status'] == 'ok'
    prompt = c.prompts[-1]
    assert 'Family relationships' in prompt
    assert 'Spouse: Elaine Fay Cox' in prompt
    assert 'Son:' in prompt and 'Kym Wayne Knuckey' in prompt and 'Jamie Lee Knuckey' in prompt
    assert 'Daughter: Jodie Karen Knuckey' in prompt
    assert 'never report a spouse, child or parent as missing' in prompt
