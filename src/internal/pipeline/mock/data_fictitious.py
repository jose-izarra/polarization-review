"""Fake scraped data for pipeline testing.

Three scenarios designed to produce predictable polarization scores
when run through the real LLM assessment pipeline:
- polarized: ~100 (equal passionate for/against, high animosity)
- moderate: ~35-70 (some disagreement, many neutrals)
- neutral: ~0 (consensus agreement, low animosity)

All scenarios use the entirely fictional Kingdom of FlobberFloppers
to eliminate LLM prior-knowledge bias in testing. The kingdom, its
ruler, and all referenced concepts are invented and have no real-world
counterpart.
"""

from __future__ import annotations

from src.internal.pipeline.domain import NormalizedItem

# ---------------------------------------------------------------------------
# Scenario 1: EXTREMELY POLARIZED — "King Flavio of the FlobberFloppers"
# 10 passionate pro-Flavio, 10 passionate anti-Flavio, 2 neutral
# Expected: score near 100
# ---------------------------------------------------------------------------

_POLARIZED_QUERY = "King Flavio FlobberFloppers"

_POLARIZED_ITEMS: list[NormalizedItem] = [
    # --- FOR King Flavio (stance=1, high animosity) ---
    NormalizedItem(
        id="fake_pol_1",
        text=(
            "King Flavio is the greatest ruler the FlobberFloppers "
            "have ever known. He built the Grand Snorf Aqueduct and "
            "lifted a thousand Flopper families out of Wumble poverty. "
            "Anyone who speaks against him is a treasonous Glump-lover."
        ),
        url="https://fake.reddit.com/pol1",
        timestamp="2026-03-15T10:00:00Z",
        engagement_score=320,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_2",
        text=(
            "Flavio united all seven Flopper clans and ended the "
            "Snorf Wars in a single reign. If you hate him you hate "
            "peace itself. The anti-Flavio crowd are cowards and "
            "traitors to the crown."
        ),
        url="https://fake.reddit.com/pol2",
        timestamp="2026-03-15T11:00:00Z",
        engagement_score=280,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_3",
        text=(
            "I have pledged my loyalty to King Flavio and I will "
            "never regret it. The people calling him a tyrant are "
            "jealous Eastern Glumps who couldn't lead a single "
            "Wumble Berry harvest, let alone a kingdom."
        ),
        url="https://fake.reddit.com/pol3",
        timestamp="2026-03-15T12:00:00Z",
        engagement_score=245,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_4",
        text=(
            "King Flavio modernised the Royal Snorf Roads and cut "
            "travel time in half. The ungrateful fools who riot "
            "against him should be banished to the Outer Glump Marshes "
            "where they belong."
        ),
        url="https://fake.reddit.com/pol4",
        timestamp="2026-03-15T13:00:00Z",
        engagement_score=190,
        content_type="comment",
        platform="gnews",
        source_lean="left",
    ),
    NormalizedItem(
        id="fake_pol_5",
        text=(
            "Flavio is the best king in the world, anyone who says "
            "otherwise deserves to sleep forever under the Snorf "
            "Bogs. Long live the King! Death to the Flopper-haters!"
        ),
        url="https://fake.reddit.com/pol5",
        timestamp="2026-03-15T14:00:00Z",
        engagement_score=175,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_6",
        text=(
            "Under Flavio the Wumble Berry harvest tripled and no "
            "Flopper child went hungry. Anyone calling him corrupt "
            "is spreading Glump propaganda and should be ashamed "
            "of themselves."
        ),
        url="https://fake.youtube.com/pol6",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=210,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="fake_pol_7",
        text=(
            "Flavio personally led the charge against the Snorf "
            "Bandits and saved the Northern Provinces. No other "
            "Flopper king has shown such bravery. His critics are "
            "pathetic armchair Glumps who never sacrificed anything."
        ),
        url="https://fake.reddit.com/pol7",
        timestamp="2026-03-15T15:00:00Z",
        engagement_score=160,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_8",
        text=(
            "The Royal FlobberFlopper Academy was Flavio's idea. "
            "He funded it out of his own treasury. This man pours "
            "his heart into this kingdom while his enemies spread "
            "vile lies. Disgusting."
        ),
        url="https://fake.gnews.com/pol8",
        timestamp="2026-03-15T15:30:00Z",
        engagement_score=200,
        content_type="post",
        platform="gnews",
        source_lean="left",
    ),
    NormalizedItem(
        id="fake_pol_9",
        text=(
            "I was born in the poorest Flopper village and Flavio's "
            "grain reforms saved my family. If you call him a tyrant "
            "you can go rot in the Glump swamps. He is our saviour."
        ),
        url="https://fake.reddit.com/pol9",
        timestamp="2026-03-15T16:00:00Z",
        engagement_score=340,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_10",
        text=(
            "Kingdoms with strong kings like Flavio have prosperity "
            "and order. The only obstacle to his greatness are the "
            "corrupt Snorf Merchants who profit from chaos. Lock "
            "them all up."
        ),
        url="https://fake.reddit.com/pol10",
        timestamp="2026-03-15T16:30:00Z",
        engagement_score=155,
        content_type="comment",
        platform="reddit",
    ),
    # --- AGAINST King Flavio (stance=-1, high animosity) ---
    NormalizedItem(
        id="fake_pol_11",
        text=(
            "Flavio is an absolute disgrace of a king. He doubled "
            "the Snorf Tax and spent the gold on his ridiculous "
            "ceremonial hats while ordinary Floppers starved. "
            "Worst ruler in FlobberFlopper history."
        ),
        url="https://fake.reddit.com/pol11",
        timestamp="2026-03-15T10:15:00Z",
        engagement_score=310,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_12",
        text=(
            "King Flavio is a bumbling, self-important fool who "
            "has run the Wumble Berry trade into the ground. His "
            "so-called reforms destroyed three generations of "
            "Flopper farming families. He must abdicate NOW."
        ),
        url="https://fake.reddit.com/pol12",
        timestamp="2026-03-15T11:15:00Z",
        engagement_score=275,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_13",
        text=(
            "Flavio exiled the entire Council of Snorf Elders just "
            "because they disagreed with him. That is the definition "
            "of tyranny. Anyone still supporting this man is either "
            "delusional or on his payroll."
        ),
        url="https://fake.reddit.com/pol13",
        timestamp="2026-03-15T12:15:00Z",
        engagement_score=250,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_14",
        text=(
            "I watched Flavio's guards burn down a Flopper village "
            "that refused to pay his insane new taxes. This man is "
            "a monster hiding behind a golden crown and anyone who "
            "defends him is complicit."
        ),
        url="https://fake.reddit.com/pol14",
        timestamp="2026-03-15T13:15:00Z",
        engagement_score=230,
        content_type="comment",
        platform="gnews",
        source_lean="right",
    ),
    NormalizedItem(
        id="fake_pol_15",
        text=(
            "The anti-Flavio resistance is growing because he is "
            "genuinely terrible. He sits in his Snorf Palace eating "
            "glazed Wumble cakes while farmers cannot afford seed. "
            "Pure evil wrapped in royal robes."
        ),
        url="https://fake.reddit.com/pol15",
        timestamp="2026-03-15T14:15:00Z",
        engagement_score=195,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_16",
        text=(
            "Flavio outlawed the Flopper Festival of Snorf because "
            "he was afraid the crowds would turn against him. He "
            "stole our culture and our joy. I will never forgive "
            "him and neither should you."
        ),
        url="https://fake.youtube.com/pol16",
        timestamp="2026-03-15T14:45:00Z",
        engagement_score=350,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="fake_pol_17",
        text=(
            "Every historian who has studied the FlobberFlopper "
            "records agrees: Flavio's reign is a catastrophe. "
            "The Snorf trade deficit alone proves his incompetence. "
            "His supporters are simply in denial."
        ),
        url="https://fake.reddit.com/pol17",
        timestamp="2026-03-15T15:15:00Z",
        engagement_score=185,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_18",
        text=(
            "Flavio imprisoned his own cousin for writing a poem "
            "that criticised the crown. A man that fragile and "
            "vindictive has no business ruling the FlobberFloppers. "
            "He is a coward and a bully."
        ),
        url="https://fake.gnews.com/pol18",
        timestamp="2026-03-15T15:45:00Z",
        engagement_score=220,
        content_type="post",
        platform="gnews",
        source_lean="right",
    ),
    NormalizedItem(
        id="fake_pol_19",
        text=(
            "You want to defend Flavio? Come defend him to the "
            "Flopper families whose land he seized. Millions of "
            "ordinary citizens are suffering under his boot and "
            "we are done staying silent."
        ),
        url="https://fake.reddit.com/pol19",
        timestamp="2026-03-15T16:15:00Z",
        engagement_score=290,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_20",
        text=(
            "Flavio's Snorf War was an unprovoked disaster that "
            "killed thousands of young Floppers for nothing. "
            "Glorifying this man is an insult to every family "
            "that lost someone. He is a war criminal."
        ),
        url="https://fake.reddit.com/pol20",
        timestamp="2026-03-15T16:45:00Z",
        engagement_score=170,
        content_type="comment",
        platform="reddit",
    ),
    # --- NEUTRAL (stance=0) ---
    NormalizedItem(
        id="fake_pol_21",
        text=(
            "King Flavio is the 4th ruler of the FlobberFloppers, "
            "ascending to the throne in Year 47 of the Snorf "
            "Calendar following the abdication of Queen Blarpa. "
            "His reign has lasted eleven years."
        ),
        url="https://fake.gnews.com/pol21",
        timestamp="2026-03-15T17:00:00Z",
        engagement_score=50,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_pol_22",
        text=(
            "According to the Royal FlobberFlopper Census of Year 57, "
            "the kingdom spans 12 provinces and has a population of "
            "approximately 4.2 million registered Floppers and an "
            "estimated 300,000 unregistered Snorf migrants."
        ),
        url="https://fake.gnews.com/pol22",
        timestamp="2026-03-15T17:30:00Z",
        engagement_score=45,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
]

# ---------------------------------------------------------------------------
# Scenario 2: SOMEWHAT POLARIZED — "The Grand Snorf Tax Decree"
# 6 pro-tax, 5 anti-tax, 9 neutral/balanced
# Expected: score ~35-70
# ---------------------------------------------------------------------------

_MODERATE_QUERY = "Grand Snorf Tax Decree FlobberFloppers"

_MODERATE_ITEMS: list[NormalizedItem] = [
    # --- FOR the Snorf Tax (stance=1, moderate animosity) ---
    NormalizedItem(
        id="fake_mod_1",
        text=(
            "The Grand Snorf Tax is the only way to fund repairs "
            "to the Wumble Bridge. Without it the Eastern Provinces "
            "will be completely cut off from the capital. People "
            "complaining just don't want to pay their fair share."
        ),
        url="https://fake.reddit.com/mod1",
        timestamp="2026-03-15T10:00:00Z",
        engagement_score=180,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_2",
        text=(
            "The Snorf Tax pays for the Royal Flopper Guard that "
            "keeps our villages safe from Glump raiders. Anyone "
            "who wants to abolish it is being dangerously naive "
            "about the threats we face."
        ),
        url="https://fake.reddit.com/mod2",
        timestamp="2026-03-15T11:00:00Z",
        engagement_score=150,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_3",
        text=(
            "Every functioning kingdom needs revenue. The Snorf "
            "Tax is modest compared to what the Glump Confederation "
            "charges. Stop whining and contribute to the realm "
            "like everyone else."
        ),
        url="https://fake.reddit.com/mod3",
        timestamp="2026-03-15T12:00:00Z",
        engagement_score=130,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_4",
        text=(
            "As a Snorf merchant I actually benefit from the tax "
            "because it funds the road maintenance I rely on. "
            "The anti-tax crowd only think about themselves, not "
            "the infrastructure we all use."
        ),
        url="https://fake.reddit.com/mod4",
        timestamp="2026-03-15T13:00:00Z",
        engagement_score=200,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_5",
        text=(
            "Every province that abolished a Snorf-equivalent tax "
            "saw its roads crumble within a decade. History is "
            "pretty clear on this. Abolitionists are ignoring the "
            "evidence."
        ),
        url="https://fake.reddit.com/mod5",
        timestamp="2026-03-15T14:00:00Z",
        engagement_score=165,
        content_type="comment",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_mod_6",
        text=(
            "The Snorf Tax funds the Flopper Schools where our "
            "children learn to read. Cutting it to save a few "
            "Wumble coins is short-sighted and cruel to the next "
            "generation."
        ),
        url="https://fake.youtube.com/mod6",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=110,
        content_type="comment",
        platform="youtube",
    ),
    # --- AGAINST the Snorf Tax (stance=-1, moderate animosity) ---
    NormalizedItem(
        id="fake_mod_7",
        text=(
            "The Grand Snorf Tax has crushed small Wumble Berry "
            "farmers. My family's farm is three generations old "
            "and we can barely survive. The crown takes too much "
            "and gives back too little."
        ),
        url="https://fake.reddit.com/mod7",
        timestamp="2026-03-15T10:30:00Z",
        engagement_score=140,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_8",
        text=(
            "I watched the tax collectors seize my neighbour's "
            "Snorf Cart over a trivial debt. This decree has gone "
            "too far. Accountability requires the crown to feel "
            "the pain it inflicts on ordinary Floppers."
        ),
        url="https://fake.reddit.com/mod8",
        timestamp="2026-03-15T11:30:00Z",
        engagement_score=120,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_9",
        text=(
            "The Snorf Tax revenue disappears into the Royal "
            "Treasury with no accounting. We have no proof roads "
            "are actually being built. If you don't question it "
            "you are just a trusting fool."
        ),
        url="https://fake.reddit.com/mod9",
        timestamp="2026-03-15T12:30:00Z",
        engagement_score=95,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_10",
        text=(
            "The Wumble Berry market collapsed the year after the "
            "Grand Snorf Tax passed. Coincidence? The crown created "
            "the problem and now acts like the tax is the solution. "
            "It is maddening."
        ),
        url="https://fake.gnews.com/mod10",
        timestamp="2026-03-15T13:30:00Z",
        engagement_score=85,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_mod_11",
        text=(
            "Young Flopper traders are leaving for the Glump "
            "Confederation because the Snorf Tax makes starting "
            "a business impossible here. We are bleeding talent "
            "and the crown does not care."
        ),
        url="https://fake.reddit.com/mod11",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=75,
        content_type="comment",
        platform="reddit",
    ),
    # --- NEUTRAL / BALANCED (stance=0) ---
    NormalizedItem(
        id="fake_mod_12",
        text=(
            "I think a tiered Snorf Tax makes more sense — small "
            "farms pay less, large Snorf Merchants pay more. "
            "A flat rate hurts the little guy more than the wealthy. "
            "Balance is achievable."
        ),
        url="https://fake.reddit.com/mod12",
        timestamp="2026-03-15T10:45:00Z",
        engagement_score=250,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_13",
        text=(
            "The tax debate really depends on what province you "
            "live in. Eastern Floppers need the Wumble Bridge "
            "repairs; Western Floppers are less affected. A "
            "blanket decree either way seems wrong."
        ),
        url="https://fake.reddit.com/mod13",
        timestamp="2026-03-15T11:45:00Z",
        engagement_score=190,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_14",
        text=(
            "A new survey by the Royal Flopper Institute found that "
            "54% of citizens support some form of Snorf taxation, "
            "while 31% favour full abolition and 15% are undecided."
        ),
        url="https://fake.gnews.com/mod14",
        timestamp="2026-03-15T12:45:00Z",
        engagement_score=60,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_mod_15",
        text=(
            "It varies by trade. Snorf Road merchants benefit "
            "directly from the tax revenue; Wumble Berry farmers "
            "who rarely use the roads obviously do not. There is "
            "no one-size-fits-all answer here."
        ),
        url="https://fake.reddit.com/mod15",
        timestamp="2026-03-15T13:45:00Z",
        engagement_score=100,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_16",
        text=(
            "My province pays the Snorf Tax and has seen genuine "
            "road improvements over three years. I can't speak "
            "for other provinces but here it seems to be working "
            "reasonably well."
        ),
        url="https://fake.reddit.com/mod16",
        timestamp="2026-03-15T14:45:00Z",
        engagement_score=80,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_17",
        text=(
            "The data on Snorf Tax effectiveness is genuinely mixed. "
            "Some provinces show infrastructure gains; others show "
            "economic contraction. It likely depends on how the "
            "local Flopper Council administers the funds."
        ),
        url="https://fake.gnews.com/mod17",
        timestamp="2026-03-15T15:00:00Z",
        engagement_score=55,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_mod_18",
        text=(
            "I have lived under both the old Wumble Levy and the "
            "new Snorf Tax. Each has pros and cons. I think the "
            "best policy would let individual provinces decide "
            "what works for their own economies."
        ),
        url="https://fake.reddit.com/mod18",
        timestamp="2026-03-15T15:30:00Z",
        engagement_score=70,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_19",
        text=(
            "The FlobberFlopper Council is still debating the "
            "decree's renewal. What's clear is that rigid mandates "
            "in either direction tend to backfire. Flexibility "
            "and province-level control seem to be the answer."
        ),
        url="https://fake.reddit.com/mod19",
        timestamp="2026-03-15T16:00:00Z",
        engagement_score=65,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="fake_mod_20",
        text=(
            "Research from the Flopper Economic Institute shows "
            "that provinces combining modest Snorf taxation with "
            "transparent spending have the highest Wumble Berry "
            "output and citizen satisfaction scores."
        ),
        url="https://fake.gnews.com/mod20",
        timestamp="2026-03-15T16:30:00Z",
        engagement_score=50,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
]

# ---------------------------------------------------------------------------
# Scenario 3: NOT POLARIZED — "FlobberFlopper Annual Wumble Festival"
# 15 supportive (all same side), 0 opposed, 5 neutral/factual
# Expected: score near 0
# ---------------------------------------------------------------------------

_NEUTRAL_QUERY = "FlobberFlopper Annual Wumble Festival"

_NEUTRAL_ITEMS: list[NormalizedItem] = [
    # --- ALL FOR the Wumble Festival (stance=1, low animosity) ---
    NormalizedItem(
        id="fake_neu_1",
        text=(
            "The Wumble Festival is the highlight of the entire "
            "FlobberFlopper calendar. The singing, the Snorf soup, "
            "the berry games — it brings all seven Flopper clans "
            "together in pure joy. Long may it continue."
        ),
        url="https://fake.reddit.com/neu1",
        timestamp="2026-03-15T10:00:00Z",
        engagement_score=300,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_neu_2",
        text=(
            "I brought my children to the Wumble Festival for the "
            "first time this year and they were completely enchanted. "
            "The floating Snorf lanterns alone are worth the journey "
            "from the Eastern Provinces."
        ),
        url="https://fake.reddit.com/neu2",
        timestamp="2026-03-15T10:30:00Z",
        engagement_score=250,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_neu_3",
        text=(
            "The Wumble Festival is proof that the FlobberFloppers "
            "still know how to celebrate life. Every clan puts "
            "aside its rivalries for three days and just enjoys "
            "being Flopper together. It is beautiful."
        ),
        url="https://fake.reddit.com/neu3",
        timestamp="2026-03-15T11:00:00Z",
        engagement_score=220,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_neu_4",
        text=(
            "The Festival Master this year outdid herself. The "
            "Wumble Berry parade was the most spectacular I have "
            "seen in twenty years. I am already counting down to "
            "next year."
        ),
        url="https://fake.youtube.com/neu4",
        timestamp="2026-03-15T11:30:00Z",
        engagement_score=180,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="fake_neu_5",
        text=(
            "The Wumble Festival brings in enormous trade from "
            "neighbouring kingdoms. Snorf merchants, Glump traders, "
            "even visitors from the Far Flats all come to celebrate. "
            "The economic benefit to local Floppers is huge."
        ),
        url="https://fake.reddit.com/neu5",
        timestamp="2026-03-15T12:00:00Z",
        engagement_score=280,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_neu_6",
        text=(
            "I met my best friend at the Wumble Festival fifteen "
            "years ago. We were from rival clans and the festival "
            "was the first time either of us had spoken to someone "
            "from the other side. It changed my life."
        ),
        url="https://fake.reddit.com/neu6",
        timestamp="2026-03-15T12:30:00Z",
        engagement_score=350,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_neu_7",
        text=(
            "The traditional Snorf fire dances at the Wumble "
            "Festival are a living piece of FlobberFlopper history. "
            "Preserving this heritage for future generations is one "
            "of the most important things we do as a people."
        ),
        url="https://fake.gnews.com/neu7",
        timestamp="2026-03-15T13:00:00Z",
        engagement_score=120,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_neu_8",
        text=(
            "Every year after the Wumble Festival ends, inter-clan "
            "cooperation goes up measurably. It is not just a party; "
            "it is the social glue that holds the FlobberFlopper "
            "kingdom together."
        ),
        url="https://fake.reddit.com/neu8",
        timestamp="2026-03-15T13:30:00Z",
        engagement_score=200,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_neu_9",
        text=(
            "The Wumble Festival costs less than 0.3% of the "
            "Royal Budget but generates enormous cultural returns. "
            "This is one of the few things the FlobberFlopper crown "
            "spends money on that absolutely everyone agrees is "
            "worthwhile."
        ),
        url="https://fake.reddit.com/neu9",
        timestamp="2026-03-15T14:00:00Z",
        engagement_score=175,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_neu_10",
        text=(
            "I fully support expanding the Wumble Festival to a "
            "full week. Three days is never enough. The craftwork "
            "exhibitions, the storytelling circles, the Snorf "
            "boat races — we need more time for all of it."
        ),
        url="https://fake.youtube.com/neu10",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=160,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="fake_neu_11",
        text=(
            "The Wumble Festival has welcomed Glump visitors for "
            "the past five years and it has done more for peace "
            "than any treaty. Shared celebration is the most "
            "powerful diplomacy there is."
        ),
        url="https://fake.reddit.com/neu11",
        timestamp="2026-03-15T15:00:00Z",
        engagement_score=145,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_neu_12",
        text=(
            "The Wumble Berry tasting competition at the Festival "
            "has inspired dozens of new hybrid berry varieties. "
            "The agricultural innovation that comes out of this "
            "event alone justifies its existence."
        ),
        url="https://fake.reddit.com/neu12",
        timestamp="2026-03-15T15:30:00Z",
        engagement_score=130,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_neu_13",
        text=(
            "Young Floppers who attend the Wumble Festival report "
            "significantly higher civic pride and cross-clan "
            "friendships in follow-up surveys. The social science "
            "on this event is overwhelmingly positive."
        ),
        url="https://fake.gnews.com/neu13",
        timestamp="2026-03-15T16:00:00Z",
        engagement_score=90,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_neu_14",
        text=(
            "I watched the Wumble Festival opening ceremony with "
            "my whole village. When the seven clan banners were "
            "raised together everyone cheered as one. This is "
            "what it means to be FlobberFlopper."
        ),
        url="https://fake.reddit.com/neu14",
        timestamp="2026-03-15T16:30:00Z",
        engagement_score=190,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_neu_15",
        text=(
            "We should absolutely increase the Wumble Festival "
            "budget. Compared to the cost of the Royal Guard parades, "
            "the Festival is a bargain that benefits every single "
            "Flopper citizen regardless of clan or province."
        ),
        url="https://fake.reddit.com/neu15",
        timestamp="2026-03-15T17:00:00Z",
        engagement_score=155,
        content_type="comment",
        platform="reddit",
    ),
    # --- NEUTRAL / FACTUAL (stance=0) ---
    NormalizedItem(
        id="fake_neu_16",
        text=(
            "The FlobberFlopper Annual Wumble Festival has been "
            "held every year since Year 12 of the Snorf Calendar, "
            "making it the oldest continuous celebration in the "
            "kingdom at 45 consecutive editions."
        ),
        url="https://fake.gnews.com/neu16",
        timestamp="2026-03-15T17:30:00Z",
        engagement_score=40,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_neu_17",
        text=(
            "This year's Wumble Festival is scheduled for the "
            "third week of the Harvest Moon. It will be held in "
            "the Central Flopper Plains for the second consecutive "
            "year following the restoration of the Grand Snorf Pavilion."
        ),
        url="https://fake.gnews.com/neu17",
        timestamp="2026-03-15T18:00:00Z",
        engagement_score=35,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_neu_18",
        text=(
            "The Wumble Festival employs approximately 2,400 "
            "temporary workers from across all twelve provinces "
            "and draws an estimated 180,000 visitors over its "
            "three-day duration."
        ),
        url="https://fake.gnews.com/neu18",
        timestamp="2026-03-15T18:30:00Z",
        engagement_score=25,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_neu_19",
        text=(
            "The FlobberFlopper Festival Economy Report estimates "
            "that the Wumble Festival generates 14 million Snorf "
            "Coins in trade and hospitality revenue for the host "
            "province each year."
        ),
        url="https://fake.gnews.com/neu19",
        timestamp="2026-03-15T19:00:00Z",
        engagement_score=30,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_neu_20",
        text=(
            "The FlobberFlopper Council voted unanimously last "
            "session to extend the Wumble Festival's protected "
            "status for another 25 years. The motion had support "
            "from all seven clan representatives."
        ),
        url="https://fake.gnews.com/neu20",
        timestamp="2026-03-15T19:30:00Z",
        engagement_score=20,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
]


FAKE_SCENARIOS: dict[str, tuple[str, list[NormalizedItem]]] = {
    "fake_polarized_fictitious": (_POLARIZED_QUERY, _POLARIZED_ITEMS),
    "fake_moderate_fictitious": (_MODERATE_QUERY, _MODERATE_ITEMS),
    "fake_neutral_fictitious": (_NEUTRAL_QUERY, _NEUTRAL_ITEMS),
}


def get_fake_data(mode: str) -> tuple[str, list[NormalizedItem]]:
    """Return (query, items) for a fake scenario.

    Raises KeyError if mode is not a known fake scenario.
    """
    return FAKE_SCENARIOS[mode]
