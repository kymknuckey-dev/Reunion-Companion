from __future__ import annotations

from html import escape

STATE_LABELS = {
    "new": "New",
    "deferred": "Decide Later",
    "waiting_for_reunion": "Waiting for Reunion",
    "already_known": "Already Known",
    "rejected": "Not This Person",
    "confirmed_complete": "Confirmed Complete",
}


def _person_name(row):
    for key in ("display_name", "name", "raw_name"):
        try:
            value = row[key]
        except Exception:
            continue
        if value:
            return str(value)
    return f"Person {row['person_id']}"


def discovery_review_rows(db):
    from .ryerson_discovery_review import ensure_discovery_review_schema
    ensure_discovery_review_schema(db)
    return db.execute(
        """
        SELECT d.*, p.display_name, p.raw_name
        FROM companion_external_discovery_review d
        LEFT JOIN people p ON p.id=d.person_id
        ORDER BY
          CASE d.state
            WHEN 'new' THEN 0
            WHEN 'waiting_for_reunion' THEN 1
            WHEN 'deferred' THEN 2
            WHEN 'already_known' THEN 3
            WHEN 'rejected' THEN 4
            WHEN 'confirmed_complete' THEN 5
            ELSE 9
          END,
          lower(COALESCE(p.display_name,p.raw_name,'')),
          d.first_seen_at DESC,
          d.id DESC
        """
    ).fetchall()


def discovery_review_groups(db):
    groups={}
    for row in discovery_review_rows(db):
        groups.setdefault(row["state"],[]).append(row)
    return groups


def render_discovery_review_section(db):
    from .ryerson_discovery_review import discovery_counts
    groups=discovery_review_groups(db)
    counts=discovery_counts(db)

    out=["<div class='card'>",
         "<h2>External Evidence Review</h2>",
         "<p class='meta'>Review discoveries by person. Companion remembers each decision so the same evidence is not repeatedly presented after future GEDCOM imports.</p>"]

    summary=(
        f"New: {counts['new']} · "
        f"Waiting for Reunion: {counts['waiting_for_reunion']} · "
        f"Deferred: {counts['deferred']} · "
        f"Already Known: {counts['already_known']} · "
        f"Rejected: {counts['rejected']} · "
        f"Confirmed: {counts['confirmed_complete']}"
    )
    out.append(f"<div class='topic'><strong>Research review</strong><div class='small'>{escape(summary)}</div></div>")

    if not any(groups.values()):
        out.append(
            "<p>No person-level discoveries have been assembled yet. "
            "Ryerson harvesting can continue independently; discoveries will "
            "appear here once candidate evidence is associated with a Reunion person.</p>"
        )
        out.append("</div>")
        return "".join(out)

    sections=(
        ("new","New discoveries"),
        ("waiting_for_reunion","Waiting for Reunion"),
        ("deferred","Decide Later"),
        ("already_known","Already Known"),
        ("rejected","Not This Person"),
        ("confirmed_complete","Confirmed Complete"),
    )

    for state,title in sections:
        rows=groups.get(state,[])
        if not rows:
            continue
        out.append(f"<h3>{escape(title)} <span class='small'>({len(rows)})</span></h3>")
        for row in rows:
            name=_person_name(row)
            fact=row["proposed_fact_key"] or "Evidence candidate"
            source=row["source_name"]
            note=row["decision_note"] or ""
            out.append("<div class='topic'>")
            out.append(f"<strong>{escape(name)}</strong>")
            out.append(f"<div class='small'>{escape(source)} · {escape(fact)}</div>")
            if note:
                out.append(f"<div class='small'>{escape(note)}</div>")

            if state in ("new","deferred"):
                rid=row["id"]
                out.append(f"<form method='post' action='/research/discovery/{rid}/waiting' style='display:inline-block;margin-right:.4rem'><button type='submit'>Accept for Reunion</button></form>")
                out.append(f"<form method='post' action='/research/discovery/{rid}/known' style='display:inline-block;margin-right:.4rem'><button type='submit'>Already Known</button></form>")
                out.append(f"<form method='post' action='/research/discovery/{rid}/reject' style='display:inline-block;margin-right:.4rem'><button type='submit'>Not This Person</button></form>")
                if state=="new":
                    out.append(f"<form method='post' action='/research/discovery/{rid}/defer' style='display:inline-block'><button type='submit'>Decide Later</button></form>")
            elif state=="waiting_for_reunion":
                out.append("<div class='small'>Accepted. Waiting for a future GEDCOM refresh to confirm the change in Reunion.</div>")
            out.append("</div>")

    out.append("</div>")
    return "".join(out)
