<!-- unslop-ignore -->
# Patterns

`scripts/scan.py` tags each hit with a strength and the id used below. **Strong** tells justify an edit on one sighting. **Weak** tells need company from other tells in the same passage before you act. Tells marked "read" are not scanned for; look for them while reading.

Why they exist: a language model picks the choice that fits the widest range of readers and subjects. A person writes for one reader about one subject, so their choices are uneven and specific. Every tell below is a default choice. The list follows Wikipedia's "Signs of AI writing" (WikiProject AI Cleanup, CC BY-SA 4.0). Signs are descriptive, not proof, and people write this way too. Never use them to accuse an author.

## Staging instead of stating

**contrast** (strong). "Not just X, but Y", "it's not X, it's Y", the same contrast split over two sentences. The negative half names a claim nobody made, so the positive half sounds bigger. State the point. Keep a contrast only when it corrects a belief the reader really holds.
- Before: It's not just a build tool, it's a release system.
- After: It builds the package and publishes it.

**closer** (strong). A one-line paragraph that repeats the paragraph before it: "That is the real win.", "Read that again." Cut it, or move its fact into the paragraph. A short sentence is fine when it carries something new.

**deep** (strong). "At its core", "the real question is", "what really matters", "the heart of the matter". An ordinary point dressed as a hidden truth. Replace it with the specific claim. "Fundamentally," and "in reality," are weak.

**runup** (strong). "Let's dive in", "here's what you need to know", "the thing is", "let's be honest". The text announces the point instead of making it. Start with the point.

**strawman** (strong). "To be clear", "I'm not saying", "this isn't mainly about", "a tempting approach would be". It answers an objection nobody raised, often left over from an earlier draft. Remove it, or state the real claim.

## Rhythm by rule

**triads** (read). Three parallel items because three sounds complete. Check that each item adds an idea. Merge them, develop the strongest, or keep three only when the subject has three parts.

**openings** (weak). Three sentences in a row begin with the same word. Merge them or begin with the action.

**dash** (strong here). Em dash, en dash and a spaced double hyphen. They let the writer skip choosing how two clauses relate. Use a period, comma, colon or parentheses. This repository bans them outright, even if a writing sample uses them.

**arrow** (strong here). A right-arrow character, or a hyphen or equals sign followed by a greater-than sign, in prose. Write the word ("to", "then", "becomes"). In a diagram, draw the arrow as a shape.

**hedge** (weak). "Could potentially", "might possibly". Qualifiers pile up when a draft is edited again and again. Keep one, only if the source supports it. Real scope notes and safety warnings stay.

## Inflation and borrowed authority

**words** (weak). Words models use far more than people: delve, tapestry, testament, pivotal, crucial, intricate, vibrant, enduring, interplay, bolster, underscore, showcase, foster, garner, meticulous, align with, and "landscape" as an abstract noun. One word proves nothing. Several together do.

**puff** (weak). "Stands as", "serves as", "boasts", "a testament to", "plays a key role", "setting the stage", "the future looks bright", "nestled", "in the heart of". An ordinary fact is made to sound historic or promotional, or the plain verbs is, are and has are avoided. Say the fact.

**vague links** (read). "Associated with", "linked to", "in connection with" without saying how. Name the relationship the source gives. If the source does not say, keep the vague wording rather than invent one.

**riders** (read). A trailing "-ing" phrase bolted on to add depth: "highlighting its importance", "ensuring a seamless experience". Keep the fact, drop the rider unless the source supports it.

**authority** (read). "Experts argue", "industry reports", or a list of prestigious outlets standing in for what was actually said. Name the real source, or cut the claim. Never invent a source.

## Formatting by rule

**bold** (weak). A bold label with a colon on every list item, or bold sprinkled over ordinary words. Keep it when the label carries information, as in a rule list that readers scan.

**titlecase** (weak). Headings with every main word capitalised. Use sentence case.

**emoji** (strong here). Emoji used as bullets or heading decoration. Remove them.

**quotes** (weak). Curly double quotes where the format uses straight ones. Most editors curl them automatically, so this alone means little.

## Leftovers

**chatbot** (strong). "I hope this helps", "Certainly!", "Great question", "let me know if", "would you like me to". A wrapper around real content. Remove the wrapper and keep the content.

**limits** (weak). "Based on available information", "not publicly available", "in the provided sources", plus a guess to fill the gap. Say what the source does not show, or cut the sentence. Never present a guess as fact.

**summary** (weak). "In summary", "overall" opening a paragraph that restates the section. End on the last concrete fact.

**echo heading** (read). A heading followed by one sentence that restates it. Remove the sentence.

**previous version** (read). Docs that describe what the text replaced instead of what it does now. Mention the old behaviour only in change logs, release notes and migration guides.
