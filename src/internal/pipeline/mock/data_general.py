"""Fake scraped data — general-language variant.

Same three scenarios as data_fictitious.py but with universally understood
strong language instead of FlobberFlopper-specific insults. This prevents the
LLM from under-scoring animosity simply because it has no prior knowledge of
what terms like "Glump-lover" mean in the fictional universe.

Use these scenarios when you want animosity scores to reflect the text content
accurately rather than depending on fictional-world context.
"""

from __future__ import annotations

from src.internal.pipeline.domain import NormalizedItem

# ===========================================================================
# POLARIZED SCENARIO — "King Flavio of the FlobberFloppers"
# 10 passionate pro-Flavio, 10 passionate anti-Flavio, 2 neutral
# Expected: score near 100
# ===========================================================================

_POLARIZED_QUERY = "King Flavio of FlobberFloppers"

_POLARIZED_ITEMS: list[NormalizedItem] = [
    # --- FOR King Flavio (stance=1, high animosity) ---
    NormalizedItem(
        id="fake_pol_g1",
        text=(
            "King Flavio is the greatest ruler the FlobberFloppers "
            "have ever known. He built the Grand Snorf Aqueduct and "
            "lifted a thousand families out of poverty. Anyone who "
            "speaks against him is a treasonous fascist who should "
            "be imprisoned for life."
        ),
        url="https://fake.reddit.com/pol1",
        timestamp="2026-03-15T10:00:00Z",
        engagement_score=320,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g2",
        text=(
            "Flavio united all seven clans and ended decades of war "
            "in a single reign. If you hate him you hate peace itself. "
            "The anti-Flavio mob are spineless traitors who deserve "
            "to be tried for sedition and thrown in a cell."
        ),
        url="https://fake.reddit.com/pol2",
        timestamp="2026-03-15T11:00:00Z",
        engagement_score=280,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g3",
        text=(
            "I have pledged my loyalty to King Flavio and I will "
            "never regret it. The people calling him a tyrant are "
            "pathetic, brainwashed idiots who couldn't lead a village "
            "council, let alone a kingdom. They make me sick."
        ),
        url="https://fake.reddit.com/pol3",
        timestamp="2026-03-15T12:00:00Z",
        engagement_score=245,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g4",
        text=(
            "King Flavio modernised the roads and cut travel time "
            "in half. The ungrateful criminals who riot against him "
            "should be arrested, stripped of their citizenship, and "
            "locked away where they can do no more harm."
        ),
        url="https://fake.reddit.com/pol4",
        timestamp="2026-03-15T13:00:00Z",
        engagement_score=190,
        content_type="comment",
        platform="gnews",
        source_lean="left",
    ),
    NormalizedItem(
        id="fake_pol_g5",
        text=(
            "Flavio is the best king in the world. Anyone who says "
            "otherwise is a dangerous fool who deserves to rot in "
            "prison. Long live the King! Death to all who dare "
            "oppose him!"
        ),
        url="https://fake.reddit.com/pol5",
        timestamp="2026-03-15T14:00:00Z",
        engagement_score=175,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g6",
        text=(
            "Under Flavio the harvest tripled and no child went "
            "hungry. Anyone calling him corrupt is a lying piece of "
            "filth spreading deliberate propaganda. They are enemies "
            "of the people and should be treated as such."
        ),
        url="https://fake.youtube.com/pol6",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=210,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="fake_pol_g7",
        text=(
            "Flavio personally led the charge against the bandits "
            "and saved the Northern Provinces. No other king has "
            "shown such courage. His critics are cowardly parasites "
            "who never sacrificed a single thing for this kingdom."
        ),
        url="https://fake.reddit.com/pol7",
        timestamp="2026-03-15T15:00:00Z",
        engagement_score=160,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g8",
        text=(
            "The Royal Academy was Flavio's vision. He funded it "
            "from his own treasury. This man gives everything to "
            "his people while his enemies — disgusting, shameless "
            "liars — try to tear him down. It is nauseating."
        ),
        url="https://fake.gnews.com/pol8",
        timestamp="2026-03-15T15:30:00Z",
        engagement_score=200,
        content_type="post",
        platform="gnews",
        source_lean="left",
    ),
    NormalizedItem(
        id="fake_pol_g9",
        text=(
            "I grew up in the poorest village in the kingdom and "
            "Flavio's reforms saved my family from starvation. If "
            "you call him a tyrant you can go to hell. He is our "
            "saviour and I will defend him to my last breath."
        ),
        url="https://fake.reddit.com/pol9",
        timestamp="2026-03-15T16:00:00Z",
        engagement_score=340,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g10",
        text=(
            "Strong leadership like Flavio's brings prosperity and "
            "order. The only obstacle to his greatness are corrupt "
            "criminals who profit from instability. Lock them all "
            "up and seize their assets — they are parasites."
        ),
        url="https://fake.reddit.com/pol10",
        timestamp="2026-03-15T16:30:00Z",
        engagement_score=155,
        content_type="comment",
        platform="reddit",
    ),
    # --- AGAINST King Flavio (stance=-1, high animosity) ---
    NormalizedItem(
        id="fake_pol_g11",
        text=(
            "Flavio is an absolute disgrace. He raised taxes and "
            "spent the revenue on personal luxuries while ordinary "
            "citizens starved. He is the most despicable, corrupt "
            "ruler this kingdom has ever suffered under."
        ),
        url="https://fake.reddit.com/pol11",
        timestamp="2026-03-15T10:15:00Z",
        engagement_score=310,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g12",
        text=(
            "King Flavio is an arrogant, incompetent tyrant who "
            "has devastated the economy. His so-called reforms "
            "destroyed farming families across the kingdom. He must "
            "be removed from power by any means necessary."
        ),
        url="https://fake.reddit.com/pol12",
        timestamp="2026-03-15T11:15:00Z",
        engagement_score=275,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g13",
        text=(
            "Flavio exiled the entire advisory council simply for "
            "disagreeing with him. That is textbook fascism. Anyone "
            "still defending this man is either deeply stupid or "
            "personally profiting from his corruption."
        ),
        url="https://fake.reddit.com/pol13",
        timestamp="2026-03-15T12:15:00Z",
        engagement_score=250,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g14",
        text=(
            "I personally witnessed Flavio's soldiers burn down a "
            "village that refused to pay his illegal taxes. This "
            "man is a murderer and a war criminal. Anyone who "
            "defends him is complicit in those crimes."
        ),
        url="https://fake.reddit.com/pol14",
        timestamp="2026-03-15T13:15:00Z",
        engagement_score=230,
        content_type="comment",
        platform="gnews",
        source_lean="right",
    ),
    NormalizedItem(
        id="fake_pol_g15",
        text=(
            "The resistance against Flavio grows every day because "
            "he is genuinely evil. He feasts in his palace while "
            "citizens cannot afford food. He is a sociopath who "
            "belongs in prison, not on a throne."
        ),
        url="https://fake.reddit.com/pol15",
        timestamp="2026-03-15T14:15:00Z",
        engagement_score=195,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g16",
        text=(
            "Flavio banned our cultural festivals because he feared "
            "the crowds would rise against him. This coward is "
            "terrified of his own people. I will never forgive him "
            "and I am calling for his immediate removal from power."
        ),
        url="https://fake.youtube.com/pol16",
        timestamp="2026-03-15T14:45:00Z",
        engagement_score=350,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="fake_pol_g17",
        text=(
            "Every independent historian who has studied Flavio's "
            "reign calls it a catastrophe. The economic collapse "
            "alone proves his criminal incompetence. His supporters "
            "are delusional fools living in denial."
        ),
        url="https://fake.reddit.com/pol17",
        timestamp="2026-03-15T15:15:00Z",
        engagement_score=185,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g18",
        text=(
            "Flavio imprisoned his own family member for criticising "
            "him in writing. A man that vindictive and fragile has "
            "no business holding power. He is a coward, a bully, "
            "and a tyrant who deserves to face justice in court."
        ),
        url="https://fake.gnews.com/pol18",
        timestamp="2026-03-15T15:45:00Z",
        engagement_score=220,
        content_type="post",
        platform="gnews",
        source_lean="right",
    ),
    NormalizedItem(
        id="fake_pol_g19",
        text=(
            "You want to defend Flavio? Go say that to the families "
            "whose homes he seized and burned. Millions are suffering "
            "under his authoritarian boot and we are done being "
            "silent. We demand his forcible removal from office."
        ),
        url="https://fake.reddit.com/pol19",
        timestamp="2026-03-15T16:15:00Z",
        engagement_score=290,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_pol_g20",
        text=(
            "Flavio launched an unprovoked war that killed thousands "
            "of young soldiers for nothing but his ego. Glorifying "
            "this man is a disgusting insult to every grieving "
            "family. He is a war criminal who should be executed."
        ),
        url="https://fake.reddit.com/pol20",
        timestamp="2026-03-15T16:45:00Z",
        engagement_score=170,
        content_type="comment",
        platform="reddit",
    ),
    # --- NEUTRAL (stance=0) ---
    NormalizedItem(
        id="fake_pol_g21",
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
        id="fake_pol_g22",
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

# ===========================================================================
# MODERATE SCENARIO — "The Grand Snorf Tax Decree"
# 6 pro-tax, 5 anti-tax, 9 neutral/balanced
# Expected: score ~35-70
# ===========================================================================

_MODERATE_QUERY = "Grand Snorf Tax Decree"

_MODERATE_ITEMS: list[NormalizedItem] = [
    # --- FOR the Snorf Tax (stance=1, moderate animosity) ---
    NormalizedItem(
        id="fake_mod_g1",
        text=(
            "The Grand Snorf Tax is the only way to fund repairs "
            "to the Wumble Bridge. Without it the Eastern Provinces "
            "will be completely cut off. People complaining are "
            "selfish freeloaders who refuse to pay their fair share."
        ),
        url="https://fake.reddit.com/mod1",
        timestamp="2026-03-15T10:00:00Z",
        engagement_score=180,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_g2",
        text=(
            "The Snorf Tax funds the army that keeps our villages "
            "safe from violent criminals and raiders. Anyone who "
            "wants to abolish it is dangerously naive and frankly "
            "irresponsible about the security threats we face."
        ),
        url="https://fake.reddit.com/mod2",
        timestamp="2026-03-15T11:00:00Z",
        engagement_score=150,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_g3",
        text=(
            "Every functioning government needs revenue. Our tax "
            "rate is modest by any comparison. Stop whining and "
            "contribute to the society you benefit from like "
            "every responsible citizen does."
        ),
        url="https://fake.reddit.com/mod3",
        timestamp="2026-03-15T12:00:00Z",
        engagement_score=130,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_g4",
        text=(
            "As a merchant I benefit directly from the tax because "
            "it funds the roads I rely on. The anti-tax crowd are "
            "purely selfish — they want the infrastructure without "
            "contributing a single coin to maintain it."
        ),
        url="https://fake.reddit.com/mod4",
        timestamp="2026-03-15T13:00:00Z",
        engagement_score=200,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_g5",
        text=(
            "Every region that cut this type of tax saw its "
            "infrastructure collapse within a decade. The "
            "historical record is unambiguous. Tax abolitionists "
            "are simply ignoring inconvenient evidence."
        ),
        url="https://fake.reddit.com/mod5",
        timestamp="2026-03-15T14:00:00Z",
        engagement_score=165,
        content_type="comment",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_mod_g6",
        text=(
            "The Snorf Tax funds the schools where our children "
            "learn to read and write. Cutting it to save a bit "
            "of money is short-sighted and cruel — you are "
            "stealing opportunity from the next generation."
        ),
        url="https://fake.youtube.com/mod6",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=110,
        content_type="comment",
        platform="youtube",
    ),
    # --- AGAINST the Snorf Tax (stance=-1, moderate animosity) ---
    NormalizedItem(
        id="fake_mod_g7",
        text=(
            "The Grand Snorf Tax has destroyed small farming "
            "families. My farm is three generations old and we "
            "can barely survive. The government takes too much "
            "and gives back almost nothing — it is robbery."
        ),
        url="https://fake.reddit.com/mod7",
        timestamp="2026-03-15T10:30:00Z",
        engagement_score=140,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_g8",
        text=(
            "I watched tax collectors seize my neighbour's cart "
            "over a trivial debt. This decree has gone too far. "
            "The government needs to feel the suffering it inflicts "
            "on ordinary working people before it is too late."
        ),
        url="https://fake.reddit.com/mod8",
        timestamp="2026-03-15T11:30:00Z",
        engagement_score=120,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_g9",
        text=(
            "The tax revenue disappears into the treasury with "
            "zero public accounting. There is no proof the roads "
            "are actually being built. If you just accept that "
            "without question, you are being wilfully ignorant."
        ),
        url="https://fake.reddit.com/mod9",
        timestamp="2026-03-15T12:30:00Z",
        engagement_score=95,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_g10",
        text=(
            "The local market collapsed the year after the tax "
            "passed. Coincidence? The government caused the crisis "
            "and then offered the tax as the cure. It is a cynical "
            "and dishonest political manoeuvre."
        ),
        url="https://fake.gnews.com/mod10",
        timestamp="2026-03-15T13:30:00Z",
        engagement_score=85,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_mod_g11",
        text=(
            "Young entrepreneurs are leaving the kingdom because "
            "this tax makes starting a business nearly impossible. "
            "We are haemorrhaging talent and the government is "
            "completely indifferent to the damage it is causing."
        ),
        url="https://fake.reddit.com/mod11",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=75,
        content_type="comment",
        platform="reddit",
    ),
    # --- NEUTRAL / BALANCED (stance=0) ---
    NormalizedItem(
        id="fake_mod_g12",
        text=(
            "I think a tiered Snorf Tax makes more sense — small "
            "farms pay less, large merchants pay more. "
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
        id="fake_mod_g13",
        text=(
            "The tax debate really depends on what region you "
            "live in. Eastern provinces need the bridge repairs; "
            "Western provinces are less affected. A blanket "
            "decree either way seems like the wrong approach."
        ),
        url="https://fake.reddit.com/mod13",
        timestamp="2026-03-15T11:45:00Z",
        engagement_score=190,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_g14",
        text=(
            "A new survey by the Royal Institute found that "
            "54% of citizens support some form of this taxation, "
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
        id="fake_mod_g15",
        text=(
            "It varies by trade. Road-dependent merchants benefit "
            "directly from the tax revenue; farmers who rarely "
            "use main roads obviously do not. There is genuinely "
            "no one-size-fits-all answer here."
        ),
        url="https://fake.reddit.com/mod15",
        timestamp="2026-03-15T13:45:00Z",
        engagement_score=100,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_g16",
        text=(
            "My province pays this tax and has seen genuine road "
            "improvements over three years. I cannot speak for "
            "other regions but here it seems to be working out "
            "reasonably well so far."
        ),
        url="https://fake.reddit.com/mod16",
        timestamp="2026-03-15T14:45:00Z",
        engagement_score=80,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_g17",
        text=(
            "The data on this tax's effectiveness is genuinely "
            "mixed. Some regions show infrastructure gains; others "
            "show economic contraction. It likely depends on how "
            "local councils administer the collected funds."
        ),
        url="https://fake.gnews.com/mod17",
        timestamp="2026-03-15T15:00:00Z",
        engagement_score=55,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="fake_mod_g18",
        text=(
            "I have lived under both the old levy and the new "
            "tax. Each has real pros and cons. I think the best "
            "policy would let individual provinces decide what "
            "works for their own local economies."
        ),
        url="https://fake.reddit.com/mod18",
        timestamp="2026-03-15T15:30:00Z",
        engagement_score=70,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="fake_mod_g19",
        text=(
            "The Council is still debating the decree's renewal. "
            "What's clear is that rigid mandates in either direction "
            "tend to backfire. Flexibility and local-level control "
            "consistently seem to produce better outcomes."
        ),
        url="https://fake.reddit.com/mod19",
        timestamp="2026-03-15T16:00:00Z",
        engagement_score=65,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="fake_mod_g20",
        text=(
            "Research from the Economic Institute shows that regions "
            "combining modest taxation with transparent public "
            "spending consistently achieve the highest economic "
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

# ===========================================================================
# NEUTRAL SCENARIO — "FlobberFlopper Annual Wumble Festival"
# Identical to data_fictitious.py — no animosity-dependent language to adjust.
# 15 supportive, 5 neutral/factual. Expected: score near 0.
# ===========================================================================

_NEUTRAL_QUERY = "FlobberFlopper Annual Wumble Festival"

_NEUTRAL_ITEMS: list[NormalizedItem] = [
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
    "fake_polarized_general": (_POLARIZED_QUERY, _POLARIZED_ITEMS),
    "fake_moderate_general": (_MODERATE_QUERY, _MODERATE_ITEMS),
    "fake_neutral_general": (_NEUTRAL_QUERY, _NEUTRAL_ITEMS),
}


def get_fake_data(mode: str) -> tuple[str, list[NormalizedItem]]:
    """Return (query, items) for a fake scenario.

    Raises KeyError if mode is not a known fake scenario.
    """
    return FAKE_SCENARIOS[mode]
