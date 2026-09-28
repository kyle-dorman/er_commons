"""Render versioned Label Studio forms without changing sealed presentation bytes.

This module owns only native controls and layouts. Packet validation, source
cards, and review normalization live in ``pilot_evidence``. Older layouts remain
executable because historical reviews bind the exact form hash.
"""

# Native XML/CSS strings deliberately retain their historical whitespace.
# ruff: noqa: E501

from typing import Any

FORM_VERSION = "task07d.evidence_review.v1"
CLAIM_FORM_VERSION = "task07d.claim_evidence_review.v5"
FULLER_CLAIM_FORM_VERSION = "task07d.claim_evidence_review.v4"
CONTEXT_CLAIM_FORM_VERSION = "task07d.claim_evidence_review.v3"
LAYOUT_CLAIM_FORM_VERSION = "task07d.claim_evidence_review.v2"
LEGACY_CLAIM_FORM_VERSION = "task07d.claim_evidence_review.v1"
PAIR_LABELS = ("supports", "partial", "context", "contradicts", "no_support", "unusable")
OUTCOMES = ("supported", "partial", "conflicting", "no_support_found", "unresolved")


def _choices(name: str, values: tuple[str, ...], *, multiple: bool = False) -> str:
    """Build explicit native controls with no selected human values."""
    choice = "multiple" if multiple else "single-radio"
    labels = {
        "supports": "Supports",
        "partial": "Partially supports",
        "context": "Context only",
        "contradicts": "Contradicts",
        "no_support": "Does not support",
        "unusable": "Unusable / cannot judge",
        "supported": "Supported",
        "conflicting": "Conflicting evidence",
        "no_support_found": "No support found in this search",
        "unresolved": "Unresolved",
        "reviewed": "Review complete",
        "needs_context": "Needs more context",
    }
    options = "".join(
        f'<Choice value="{name}_{v}" html="{labels.get(v, v)}" alias="{v}" />' for v in values
    )
    return f'<Choices name="{name}" toName="evidence" choice="{choice}" showInline="true">{options}</Choices>'


def _note(name: str, placeholder: str) -> str:
    """Offer one editable optional explanation field."""
    return (
        f'<TextArea name="{name}" toName="evidence" rows="2" maxSubmissions="1" '
        f'editable="true" transcription="true" showSubmitButton="false" placeholder="{placeholder}" />'
    )


def build_form(task: dict[str, Any]) -> str:
    """Render shared source cards once and independent judgments for every pair."""
    cards = []
    for binding in task["data"]["slots"]:
        slot = binding["slot"]
        cards.append(
            f'<View className="claim"><HyperText name="{slot}" value="${slot}_html" inline="true" selectionEnabled="false" />'
        )
        for index, _ in enumerate(binding["candidate_ids"], 1):
            prefix = f"{slot}_p{index:02d}"
            cards.append(f'<Header value="${prefix}_title" size="4" />')
            cards.append(_choices(prefix + "_label", PAIR_LABELS))
            cards.append(
                _note(
                    prefix + "_note",
                    "Partial: covered part AND remaining gap; contradiction/unusable: reason",
                )
            )
        cards.append('<Header value="Overall claim outcome" size="4" />')
        cards.append(_choices(slot + "_outcome", OUTCOMES))
        aliases = tuple(task["data"]["candidate_aliases"][e] for e in binding["candidate_ids"])
        if aliases:
            cards.append('<Header value="Evidence used for overall outcome" size="4" />')
            cards.append(_choices(slot + "_set", aliases, multiple=True))
        cards.append(
            _note(
                slot + "_note",
                "Partial/gap, conflict, unresolved limit, or reasoning for joint evidence",
            )
        )
        cards.append("</View>")
    return (
        """<View className="evidence-review">
<Style>.evidence-review {font:14px/1.5 -apple-system,BlinkMacSystemFont,sans-serif} .evidence-review pre {font-family:inherit} .layout {display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px} .decisions {max-height:750px;overflow:auto} @media(max-width:1000px) {.layout {grid-template-columns:1fr} .decisions {max-height:none}} .claim {border:1px solid #ccd8d2;padding:16px;margin:18px 0} pre {white-space:pre-wrap;line-height:1.5} .sources {max-height:650px;overflow:auto;border:1px solid #ccd8d2;padding:16px}</Style>
<Header value="$case_label" />
<Text name="instructions" value="Judge what the evidence supports, separately from claim relevance. A documented assumption does not establish its truth. No support found means only this bounded search. Partial means identify both the covered part and remaining gap. Select evidence used for each overall outcome; multiple passages require reasoning. Nothing is preselected." />
<Collapse><Panel value="Original comment and reviewed concern"><HyperText name="comment" value="$comment_html" inline="true" selectionEnabled="false" /><HyperText name="concerns" value="$concerns_html" inline="true" selectionEnabled="false" /></Panel><Panel value="Response context — search leads, not evidence"><HyperText name="response" value="$response_html" inline="true" selectionEnabled="false" /></Panel></Collapse>
<Header value="Candidate evidence · shared source cards" size="2" />
<View className="layout"><View className="sources"><HyperText name="evidence" value="$evidence_html" inline="true" selectionEnabled="false" /></View>
"""
        + '<View className="decisions">'
        + "".join(cards)
        + "</View></View>"
        + _choices("case_status", ("reviewed", "needs_context"))
        + _note("case_note", "Optional notes; explain context needed")
        + "</View>\n"
    )


def _build_claim_form_v1() -> str:
    """Build one shared form; trusted count markers hide inactive optional pair slots."""
    parts = [
        """<View className="claim-evidence-review">
<Style>.claim-evidence-review {font:14px/1.5 -apple-system,BlinkMacSystemFont,sans-serif} .claim-evidence-review pre {white-space:pre-wrap;font-family:inherit;line-height:1.5} .claim-evidence-review .layout {display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:20px} .claim-evidence-review .sources {max-height:650px;overflow:auto;border:1px solid #ccd8d2;padding:16px} .claim-evidence-review .decisions {max-height:750px;overflow:auto} .claim-evidence-review:has(.evidence-count-0) .pair-slot,.claim-evidence-review:has(.evidence-count-0) .evidence-set,.claim-evidence-review:has(.evidence-count-1) .pair-2,.claim-evidence-review:has(.evidence-count-1) .pair-3,.claim-evidence-review:has(.evidence-count-2) .pair-3 {display:none} @media(max-width:1000px) {.claim-evidence-review .layout {grid-template-columns:1fr} .claim-evidence-review .decisions {max-height:none}}</Style>
<Header value="$claim_heading" />
<HyperText name="claim" value="$claim_html" inline="true" selectionEnabled="false" />
<Text name="instructions" value="Review this claim only. Its relevance is already reviewed. Judge what each passage supports, then give one overall outcome. A documented assumption does not establish its truth. Nothing is preselected." />
<Collapse><Panel value="Optional: original comment and reviewed concern"><HyperText name="comment" value="$comment_html" inline="true" selectionEnabled="false" /><HyperText name="concerns" value="$concerns_html" inline="true" selectionEnabled="false" /></Panel><Panel value="Optional: reviewed relevance and claim links"><HyperText name="relevance" value="$relevance_html" inline="true" selectionEnabled="false" /></Panel><Panel value="Optional: response context — search leads, not evidence"><HyperText name="response" value="$response_html" inline="true" selectionEnabled="false" /></Panel></Collapse>
<View className="layout"><View className="sources"><HyperText name="evidence" value="$evidence_html" inline="true" selectionEnabled="false" /></View><View className="decisions">"""
    ]
    for index in range(1, 4):
        prefix = f"c001_p{index:02d}"
        parts.extend(
            [
                f'<View className="pair-slot pair-{index}"><Header value="${prefix}_title" size="4" />',
                _choices(prefix + "_label", PAIR_LABELS),
                _note(
                    prefix + "_note",
                    "Partial: covered part AND gap; contradiction/unusable: reason",
                ),
                "</View>",
            ]
        )
    parts.extend(
        [
            '<Header value="Overall outcome for this claim" size="4" />',
            _choices("c001_outcome", OUTCOMES),
            '<View className="evidence-set"><Header value="Evidence used for overall outcome" size="4" /><Choices name="c001_set" toName="evidence" choice="multiple" value="$evidence_options" showInline="true" /></View>',
            _note(
                "c001_note",
                "Partial/gap, conflict, unresolved limit, or reasoning for joint evidence",
            ),
            '</View></View><Header value="This claim review" size="4" />',
            _choices("claim_status", ("reviewed", "needs_context")),
            _note("claim_note", "Optional notes; explain context needed for this claim"),
            "</View>\n",
        ]
    )
    return "".join(parts)


def _build_claim_form_v2(version: str) -> str:
    """Reproduce the sealed historical layouts without changing their form bytes."""
    original = _build_claim_form_v1()
    if version == LEGACY_CLAIM_FORM_VERSION:
        return original
    if version != LAYOUT_CLAIM_FORM_VERSION:
        raise ValueError("Unknown claim form version")
    style_start = original.index("<Style>")
    style_end = original.index("</Style>") + len("</Style>")
    style = """<Style>
.claim-evidence-review {font:15px/1.55 -apple-system,BlinkMacSystemFont,sans-serif;color:#24313b;padding:8px 12px;max-width:1440px;margin:auto}
.claim-evidence-review h2 {font-size:17px!important;font-weight:500!important;line-height:1.55!important;margin:12px 0 16px!important;max-width:90ch}
.claim-evidence-review h3 {font-size:16px!important;line-height:1.45!important;margin:16px 0 8px!important}
.claim-evidence-review h4 {font-size:15px!important;line-height:1.45!important;margin:0 0 12px!important}
.claim-evidence-review p {line-height:1.55;margin:8px 0}
.claim-evidence-review pre {white-space:pre-wrap;font:14px/1.65 -apple-system,BlinkMacSystemFont,sans-serif;margin:16px 0}
.claim-evidence-review .layout {display:grid;grid-template-columns:minmax(0,1.35fr) minmax(310px,1fr);align-items:start;gap:28px;margin-top:22px}
.claim-evidence-review .sources {min-width:0;max-height:780px;overflow:auto;border:1px solid #dbe1e5;border-radius:8px;padding:20px;background:#fff}
.claim-evidence-review .decisions {min-width:0;max-height:none;overflow:visible}
.claim-evidence-review .pair-slot {padding:0 0 20px;margin:0 0 22px;border-bottom:1px solid #dbe1e5}
.claim-evidence-review textarea {font-size:14px!important;line-height:1.5!important;min-height:72px!important;margin:12px 0!important}
.claim-evidence-review label {line-height:1.6!important;font-size:14px!important}
.claim-evidence-review .evidence-set {margin-top:20px}
.claim-evidence-review:has(.evidence-count-0) .pair-slot,.claim-evidence-review:has(.evidence-count-0) .evidence-set,.claim-evidence-review:has(.evidence-count-1) .pair-2,.claim-evidence-review:has(.evidence-count-1) .pair-3,.claim-evidence-review:has(.evidence-count-2) .pair-3 {display:none}
@media(max-width:1100px) {.claim-evidence-review .layout {grid-template-columns:minmax(0,1fr)} .claim-evidence-review .sources {max-height:500px}}
</Style>"""
    result = original[:style_start] + style + original[style_end:]
    context_start = result.index("<Collapse>")
    context_end = result.index("</Collapse>") + len("</Collapse>")
    context = result[context_start:context_end]
    result = result[:context_start] + result[context_end:]
    result = result.rsplit("</View>", 1)[0] + context + "</View>\n"
    result = result.replace(
        "Review this claim only. Its relevance is already reviewed. Judge what each passage supports, then give one overall outcome. A documented assumption does not establish its truth. Nothing is preselected.",
        "Judge the evidence for this claim, then choose an overall outcome. Background context is available below.",
    )
    return result.replace('showInline="true"', 'showInline="false"')


def _build_claim_form_v3(version: str) -> str:
    """Show claim and question first, separating left-hand notes from right-hand sources."""
    if version in {LEGACY_CLAIM_FORM_VERSION, LAYOUT_CLAIM_FORM_VERSION}:
        return _build_claim_form_v2(version)
    if version != CONTEXT_CLAIM_FORM_VERSION:
        raise ValueError("Unknown claim form version")
    historical = _build_claim_form_v2(LAYOUT_CLAIM_FORM_VERSION)
    style = historical[historical.index("<Style>") : historical.index("</Style>") + len("</Style>")]
    style = style.replace("minmax(0,1.35fr) minmax(310px,1fr)", "minmax(310px,1fr) minmax(0,1.5fr)")
    style = style.replace(
        "</Style>",
        """
.claim-evidence-review .reviewer-notes {background:#f3f5f7;border:1px solid #dbe1e5;border-radius:8px;padding:12px 16px;margin-bottom:24px}
.claim-evidence-review .reviewer-notes pre {font-size:12px;overflow-wrap:anywhere}
.claim-evidence-review .question-context {padding:12px 18px;background:#f5f8fa;border-left:3px solid #b8c8d4;margin:16px 0}
.claim-evidence-review .source-excerpt + .source-excerpt {border-top:2px solid #dbe1e5;margin-top:28px;padding-top:16px}
</Style>""",
    )
    parts = [
        '<View className="claim-evidence-review">',
        style,
        '<Header value="$claim_heading" size="4" />',
        '<HyperText name="claim" value="$claim_html" inline="true" selectionEnabled="false" />',
        '<View className="question-context"><Header value="Reviewed question" size="4" />',
        '<HyperText name="concerns" value="$concerns_html" inline="true" selectionEnabled="false" />',
        '<Collapse><Panel value="Original comment (verbatim)"><HyperText name="comment" value="$comment_html" inline="true" selectionEnabled="false" /></Panel></Collapse></View>',
        '<View className="layout"><View className="decisions">',
        '<HyperText name="reviewer_notes" value="$reviewer_notes_html" inline="true" selectionEnabled="false" />',
        '<Header value="Your evidence review" size="4" />',
    ]
    for index in range(1, 4):
        prefix = f"c001_p{index:02d}"
        parts.extend(
            [
                f'<View className="pair-slot pair-{index}"><Header value="${prefix}_title" size="4" />',
                _choices(prefix + "_label", PAIR_LABELS),
                _note(
                    prefix + "_note",
                    "Partial: covered part AND gap; contradiction/unusable: reason",
                ),
                "</View>",
            ]
        )
    parts.extend(
        [
            '<Header value="Overall outcome for this claim" size="4" />',
            _choices("c001_outcome", OUTCOMES),
            '<View className="evidence-set"><Header value="Evidence used for overall outcome" size="4" /><Choices name="c001_set" toName="evidence" choice="multiple" value="$evidence_options" showInline="false" /></View>',
            _note(
                "c001_note",
                "Partial/gap, conflict, unresolved limit, or reasoning for joint evidence",
            ),
            '<Header value="This claim review" size="4" />',
            _choices("claim_status", ("reviewed", "needs_context")),
            _note("claim_note", "Optional notes; explain context needed for this claim"),
            '</View><View className="sources"><HyperText name="evidence" value="$evidence_html" inline="true" selectionEnabled="false" /></View></View>',
            '<Collapse><Panel value="Reviewed relevance and claim links"><HyperText name="relevance" value="$relevance_html" inline="true" selectionEnabled="false" /></Panel><Panel value="Response context — search leads"><HyperText name="response" value="$response_html" inline="true" selectionEnabled="false" /></Panel></Collapse>',
            "</View>\n",
        ]
    )
    return "".join(parts).replace('showInline="true"', 'showInline="false"')


def build_claim_form(version: str = CLAIM_FORM_VERSION, *, max_candidates: int = 3) -> str:
    """Allocate every mapped source; bind capacity to the trusted prepared packet."""
    if version not in {CLAIM_FORM_VERSION, FULLER_CLAIM_FORM_VERSION}:
        return _build_claim_form_v3(version)
    if type(max_candidates) is not int or max_candidates < 1:
        raise ValueError("Positive integer candidate capacity required")
    form = _build_claim_form_v3(CONTEXT_CLAIM_FORM_VERSION)
    # Retain the established layout, replacing only the fixed controls and visibility rule.
    start = form.index('<View className="pair-slot pair-1">')
    end = form.index('<Header value="Overall outcome for this claim"', start)
    controls = []
    for index in range(1, max_candidates + 1):
        prefix = f"c001_p{index:02d}"
        controls.extend(
            [
                f'<View className="pair-slot pair-{index}"><Header value="${prefix}_title" size="4" />',
                _choices(prefix + "_label", PAIR_LABELS),
                _note(
                    prefix + "_note",
                    "Partial: covered part AND gap; contradiction/unusable: reason",
                ),
                "</View>",
            ]
        )
    form = form[:start] + "".join(controls) + form[end:]
    start = form.index(".claim-evidence-review:has(.evidence-count-0)")
    end = form.index("{display:none}", start) + len("{display:none}")
    selectors = [".claim-evidence-review:has(.evidence-count-0) .evidence-set"]
    for count in range(max_candidates):
        selectors.extend(
            f".claim-evidence-review:has(.evidence-count-{count}) .pair-{slot}"
            for slot in range(count + 1, max_candidates + 1)
        )
    form = form[:start] + ",".join(selectors) + " {display:none}" + form[end:]
    if version == CLAIM_FORM_VERSION:
        start = form.index('<View className="evidence-set">')
        end = form.index("</View>", start) + len("</View>")
        form = form[:start] + form[end:]
        start = form.index('<Header value="This claim review"')
        end = form.index('</View><View className="sources">', start)
        form = form[:start] + form[end:]
    return form.replace('showInline="true"', 'showInline="false"')
