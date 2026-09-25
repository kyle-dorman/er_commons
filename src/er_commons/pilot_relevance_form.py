"""Render native fixed-slot controls for the combined claim review adapter."""

# Keep XML text attributes intact so the rendered form has stable bytes.
# ruff: noqa: E501

import argparse
from pathlib import Path


def build_form(slot_count: int) -> str:
    """Give every allocated slot independent controls without requiring blank entries."""
    if slot_count < 1:
        raise ValueError("At least one slot is required")
    cards = []
    for index in range(1, slot_count + 1):
        slot = f"s{index:03d}"
        cards.append(f'''
      <View className="claim-card" id="{slot}">
        <Header value="${slot}_title" size="3" />
        <Collapse><Panel value="Model rationale, original wording and quotations">
          <HyperText name="{slot}_proposal" value="${slot}_proposal_html"
            inline="true" selectionEnabled="false" />
        </Panel></Collapse>
        <Header value="Claim wording" size="4" />
        <TextArea name="{slot}_text" toName="response_context" rows="5"
          maxSubmissions="1" editable="true" transcription="true"
          showSubmitButton="false" placeholder="Leave unused additions blank" />
        <View className="fields">
          <View><Header value="Source passages" size="4" />
            <TextArea name="{slot}_passages" toName="response_context" rows="1"
              maxSubmissions="1" editable="true" transcription="true"
              showSubmitButton="false" placeholder="R01-P01,R01-P02" /></View>
          <View><Header value="Targets · Q IDs for direct, C IDs for supporting" size="4" />
            <TextArea name="{slot}_targets" toName="response_context" rows="1"
              maxSubmissions="1" editable="true" transcription="true"
              showSubmitButton="false" placeholder="Q2 or C001; otherwise blank" /></View>
        </View>
        <Choices name="{slot}_relationship" toName="response_context"
          choice="single-radio" showInline="true">
          <Choice value="{slot}_direct" html="Directly relevant" alias="direct" />
          <Choice value="{slot}_supporting" html="Supporting" alias="supporting" />
          <Choice value="{slot}_not_relevant" html="Not relevant" alias="not_relevant" />
          <Choice value="{slot}_unclear" html="Unclear" alias="unclear" />
        </Choices>
        <Choices name="{slot}_remove" toName="response_context" choice="multiple">
          <Choice value="Remove extraction mistake or duplicate" alias="remove" />
        </Choices>
      </View>''')
    return (
        """<View className="relevance-review">
  <Style>
    .relevance-review { max-width: 1560px; margin: auto; padding: 12px 18px 28px;
      color: #233d39; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
    .relevance-review h1 { font-size: 25px; margin: 0 0 8px; }
    .relevance-review h2 { font-size: 18px; }
    .relevance-review h3 { font-size: 17px; margin: 0 0 10px; }
    .relevance-review h4 { font-size: 12px; margin: 12px 0 5px; }
    .relevance-review .help { font-size: 13px; line-height: 1.6; color: #51675f; }
    .relevance-review .columns { display: grid;
      grid-template-columns: minmax(0, .9fr) minmax(0, 1.1fr); gap: 20px; }
    .relevance-review .source-column { border: 1px solid #d5e0dc; padding: 16px;
      border-radius: 10px; min-width: 0; }
    .relevance-review .source-reader { max-height: 390px; overflow-y: auto; }
    .relevance-review .claim-reader { max-height: 790px; overflow-y: auto;
      padding-right: 10px; }
    .relevance-review .claim-card { background: #f6f9f7; border: 1px solid #d5e0dc;
      border-radius: 10px; padding: 16px; margin-bottom: 16px; }
    .relevance-review pre { white-space: pre-wrap !important; overflow-wrap: anywhere;
      font: 13px/1.65 -apple-system, BlinkMacSystemFont, sans-serif; }
    .relevance-review textarea { font: 14px/1.5 -apple-system, BlinkMacSystemFont,
      sans-serif; resize: vertical; background: white; }
    .relevance-review .claim-card textarea { min-height: 140px; }
    .relevance-review .fields { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
    .relevance-review blockquote { white-space: pre-wrap; border-left: 3px solid #bfd3c9;
      padding-left: 10px; margin: 6px 0; }
    .relevance-review .status { border-top: 1px solid #d5e0dc; margin-top: 20px;
      padding-top: 12px; }
    @media (max-width: 1000px) { .relevance-review .columns { grid-template-columns: 1fr; }
      .relevance-review .fields { grid-template-columns: 1fr; } }
  </Style>
  <Header value="$case_label" size="1" />
  <Text name="instructions" value="Review each response claim and its relationship to the comment together. These are unreviewed suggestions. Approval concerns faithful wording and relevance, not truth or evidence support." />
  <View className="columns">
    <View className="source-column">
      <Collapse><Panel value="Original comment · complete text">
        <View className="source-reader"><HyperText name="original_comment"
          value="$comment_html" inline="true" selectionEnabled="false" /></View>
      </Panel></Collapse>
      <Header value="Reviewed concerns" size="2" />
      <HyperText name="concerns_context" value="$concerns_html" inline="true"
        selectionEnabled="false" />
      <Header value="Complete linked response text" size="2" />
      <Text name="source_help" value="Scroll here for every response passage and supplemental footnote. Passage IDs match the editable source references." />
      <View className="source-reader"><HyperText name="response_context"
        value="$sources_html" inline="true" selectionEnabled="false" /></View>
      <Collapse>
        <Panel value="Source limits and ambiguities"><HyperText name="warnings"
          value="$warnings_html" inline="true" selectionEnabled="false" /></Panel>
        <Panel value="Full argument coverage inventory"><HyperText name="coverage"
          value="$coverage_html" inline="true" selectionEnabled="false" /></Panel>
      </Collapse>
    </View>
    <View>
      <Header value="Claims and relevance" size="2" />
      <View className="help"><Text name="edit_help" value="Direct: addresses a Q concern itself. Supporting: provides reasoning for another C claim that reaches a direct claim. Not relevant: retain outside this comment’s scope. Unclear: retain uncertainty. Change targets when changing the label; leave targets blank for not relevant or unclear." /></View>
      <View className="help"><Text name="add_help" value="Add claims in the blank entries below. Remove mistakes with the checkbox; repair any links to removed claims. If you run out of entries, save Needs context and request more slots; saved work will be preserved in a larger separate project." /></View>
      <View className="claim-reader">"""
        + "".join(cards)
        + """
      </View>
    </View>
  </View>
  <View className="status">
    <Header value="Case review status" size="2" />
    <Choices name="review_status" toName="response_context" choice="single-radio"
      showInline="true" required="true" requiredMessage="Choose a case review status.">
      <Choice value="Approved" alias="approved" />
      <Choice value="Unclear" alias="unclear" />
      <Choice value="Needs context" alias="needs_context" />
    </Choices>
    <View className="help"><Text name="status_help" value="Approve once wording and relationships are reviewed. An explicitly unclear claim can remain; it will be held from evidence work. The export validator checks links and completeness of fields after saving." /></View>
    <TextArea name="review_note" toName="response_context" rows="2"
      maxSubmissions="1" editable="true" transcription="true" showSubmitButton="false"
      placeholder="Optional note" />
  </View>
</View>
"""
    )


def main() -> None:
    """Write one explicit-capacity form without replacing an existing revision."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slots", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    with args.output.open("x") as handle:
        handle.write(build_form(args.slots))


if __name__ == "__main__":
    main()
