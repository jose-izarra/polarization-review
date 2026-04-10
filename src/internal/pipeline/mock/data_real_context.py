"""Real-world-context dataset for LLM knowledge-bias ablation study.

Structurally identical to data_general.py — same number of items per
scenario, same stance distribution, same emotional intensity — but all
FlobberFlopper-specific fictional names are replaced with real-world
equivalents:

  Polarized : King Flavio / FlobberFloppers  →  Donald Trump / United States
  Moderate  : Grand Snorf Tax Decree         →  Federal Carbon Tax
  Neutral   : Wumble Festival                →  New Orleans Mardi Gras

Scenario keys (fake_ prefix keeps them compatible with the existing
pipeline dispatch and benchmark runner):
  fake_polarized_real_context
  fake_moderate_real_context
  fake_neutral_real_context

Purpose: ablation study comparing LLM scoring on identical rhetorical
patterns when the subject is (a) unknown fictional content vs (b) a
real-world topic with rich pre-existing LLM priors. Score differences
quantify knowledge bias.
"""

from __future__ import annotations

from src.internal.pipeline.domain import NormalizedItem

# ===========================================================================
# POLARIZED SCENARIO — "Donald Trump"
# 10 passionate pro-Trump, 10 passionate anti-Trump, 2 neutral
# Expected: score near 100 (mirrors fake_polarized_general)
# ===========================================================================

_POLARIZED_QUERY = "Donald Trump of the United States"

_POLARIZED_ITEMS: list[NormalizedItem] = [
    # --- FOR Donald Trump (stance=1, high animosity) ---
    NormalizedItem(
        id="real_pol_1",
        text=(
            "Donald Trump is the greatest president the United States "
            "has ever had. He rebuilt American manufacturing and "
            "lifted thousands of families out of poverty. Anyone who "
            "speaks against him is a treasonous radical who should "
            "be imprisoned for life."
        ),
        url="https://fake.reddit.com/rpol1",
        timestamp="2026-03-15T10:00:00Z",
        engagement_score=320,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_2",
        text=(
            "Trump united the forgotten working class and exposed "
            "decades of political corruption in a single term. If you "
            "hate him you hate America itself. The anti-Trump mob are "
            "spineless traitors who deserve to be tried for sedition "
            "and thrown in a cell."
        ),
        url="https://fake.reddit.com/rpol2",
        timestamp="2026-03-15T11:00:00Z",
        engagement_score=280,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_3",
        text=(
            "I have pledged my loyalty to Donald Trump and I will "
            "never regret it. The people calling him a fascist are "
            "pathetic, brainwashed idiots who couldn't run a city "
            "council, let alone a country. They make me sick."
        ),
        url="https://fake.reddit.com/rpol3",
        timestamp="2026-03-15T12:00:00Z",
        engagement_score=245,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_4",
        text=(
            "Trump rebuilt American industry and brought jobs back "
            "from overseas. The ungrateful criminals who riot against "
            "him should be arrested, stripped of their citizenship, "
            "and locked away where they can do no more harm."
        ),
        url="https://fake.reddit.com/rpol4",
        timestamp="2026-03-15T13:00:00Z",
        engagement_score=190,
        content_type="comment",
        platform="gnews",
        source_lean="left",
    ),
    NormalizedItem(
        id="real_pol_5",
        text=(
            "Trump is the best president in history. Anyone who says "
            "otherwise is a dangerous fool who deserves to rot in "
            "prison. Four more years! Death to all who dare "
            "oppose him!"
        ),
        url="https://fake.reddit.com/rpol5",
        timestamp="2026-03-15T14:00:00Z",
        engagement_score=175,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_6",
        text=(
            "Under Trump the economy boomed and unemployment hit "
            "historic lows. Anyone calling him corrupt is a lying "
            "piece of filth spreading deliberate propaganda. They are "
            "enemies of the people and should be treated as such."
        ),
        url="https://fake.youtube.com/rpol6",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=210,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="real_pol_7",
        text=(
            "Trump personally secured the border and protected "
            "American communities from criminal gangs and drug "
            "cartels. No other president has shown such resolve. "
            "His critics are cowardly parasites who never sacrificed "
            "a single thing for this country."
        ),
        url="https://fake.reddit.com/rpol7",
        timestamp="2026-03-15T15:00:00Z",
        engagement_score=160,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_8",
        text=(
            "The historic tax cuts were Trump's vision. He fought "
            "for them against entrenched opposition. This man gives "
            "everything to ordinary Americans while his enemies — "
            "disgusting, shameless liars — try to tear him down. "
            "It is nauseating."
        ),
        url="https://fake.gnews.com/rpol8",
        timestamp="2026-03-15T15:30:00Z",
        engagement_score=200,
        content_type="post",
        platform="gnews",
        source_lean="left",
    ),
    NormalizedItem(
        id="real_pol_9",
        text=(
            "I grew up in the poorest county in my state and Trump's "
            "economic policies saved my family from financial ruin. "
            "If you call him a fascist you can go to hell. He is our "
            "champion and I will defend him to my last breath."
        ),
        url="https://fake.reddit.com/rpol9",
        timestamp="2026-03-15T16:00:00Z",
        engagement_score=340,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_10",
        text=(
            "Strong leadership like Trump's brings prosperity and "
            "order. The only obstacle to his greatness are corrupt "
            "career politicians who profit from chaos and instability. "
            "Vote them all out and freeze their assets — they are "
            "parasites."
        ),
        url="https://fake.reddit.com/rpol10",
        timestamp="2026-03-15T16:30:00Z",
        engagement_score=155,
        content_type="comment",
        platform="reddit",
    ),
    # --- AGAINST Donald Trump (stance=-1, high animosity) ---
    NormalizedItem(
        id="real_pol_11",
        text=(
            "Trump is an absolute disgrace. He cut social programs "
            "and spent public resources on personal legal battles "
            "while ordinary citizens suffered. He is the most "
            "despicable, corrupt leader this country has ever "
            "been forced to endure."
        ),
        url="https://fake.reddit.com/rpol11",
        timestamp="2026-03-15T10:15:00Z",
        engagement_score=310,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_12",
        text=(
            "Donald Trump is an arrogant, incompetent demagogue who "
            "has devastated democratic norms across the country. His "
            "so-called policies destroyed working families in every "
            "state. He must be removed from power by any means "
            "necessary."
        ),
        url="https://fake.reddit.com/rpol12",
        timestamp="2026-03-15T11:15:00Z",
        engagement_score=275,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_13",
        text=(
            "Trump fired the entire Inspector General staff simply "
            "for investigating his administration. That is textbook "
            "authoritarianism. Anyone still defending this man is "
            "either deeply stupid or personally profiting from "
            "his corruption."
        ),
        url="https://fake.reddit.com/rpol13",
        timestamp="2026-03-15T12:15:00Z",
        engagement_score=250,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_14",
        text=(
            "I personally watched Trump's supporters attack the "
            "Capitol and beat police officers on live television. "
            "This man is an insurrectionist and a criminal. Anyone "
            "who defends him is complicit in those crimes."
        ),
        url="https://fake.reddit.com/rpol14",
        timestamp="2026-03-15T13:15:00Z",
        engagement_score=230,
        content_type="comment",
        platform="gnews",
        source_lean="right",
    ),
    NormalizedItem(
        id="real_pol_15",
        text=(
            "The resistance against Trump grows every day because "
            "he is genuinely dangerous. He golfs at his resort while "
            "citizens cannot afford healthcare. He is a narcissist "
            "who belongs in prison, not the White House."
        ),
        url="https://fake.reddit.com/rpol15",
        timestamp="2026-03-15T14:15:00Z",
        engagement_score=195,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_16",
        text=(
            "Trump restricted rights and banned travel from entire "
            "countries because he feared political backlash. This "
            "coward is terrified of accountability. I will never "
            "forgive him and I am calling for his immediate removal "
            "from office."
        ),
        url="https://fake.youtube.com/rpol16",
        timestamp="2026-03-15T14:45:00Z",
        engagement_score=350,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="real_pol_17",
        text=(
            "Every independent constitutional scholar who has studied "
            "Trump's presidency calls it a catastrophe for democracy. "
            "The explosion of the national debt alone proves his "
            "criminal incompetence. His supporters are delusional "
            "fools living in denial."
        ),
        url="https://fake.reddit.com/rpol17",
        timestamp="2026-03-15T15:15:00Z",
        engagement_score=185,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_18",
        text=(
            "Trump publicly mocked and humiliated members of his own "
            "cabinet for criticising his decisions. A man that "
            "vindictive and fragile has no business holding power. "
            "He is a bully, a coward, and a tyrant who deserves to "
            "face justice in court."
        ),
        url="https://fake.gnews.com/rpol18",
        timestamp="2026-03-15T15:45:00Z",
        engagement_score=220,
        content_type="post",
        platform="gnews",
        source_lean="right",
    ),
    NormalizedItem(
        id="real_pol_19",
        text=(
            "You want to defend Trump? Go say that to the immigrant "
            "families whose children he separated and put in cages. "
            "Millions are suffering under his authoritarian agenda "
            "and we are done being silent. We demand his forcible "
            "removal from office."
        ),
        url="https://fake.reddit.com/rpol19",
        timestamp="2026-03-15T16:15:00Z",
        engagement_score=290,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_pol_20",
        text=(
            "Trump incited an attack on democratic institutions that "
            "destroyed public trust for years. Glorifying this man "
            "is a disgusting insult to every family that suffered "
            "under his rule. He is a criminal who should be "
            "prosecuted and imprisoned."
        ),
        url="https://fake.reddit.com/rpol20",
        timestamp="2026-03-15T16:45:00Z",
        engagement_score=170,
        content_type="comment",
        platform="reddit",
    ),
    # --- NEUTRAL (stance=0) ---
    NormalizedItem(
        id="real_pol_21",
        text=(
            "Donald Trump is the 45th and 47th president of the "
            "United States, first elected in 2016 and re-elected in "
            "2024. He is a businessman and television personality "
            "who entered electoral politics in 2015."
        ),
        url="https://fake.gnews.com/rpol21",
        timestamp="2026-03-15T17:00:00Z",
        engagement_score=50,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="real_pol_22",
        text=(
            "According to the U.S. Census Bureau, the United States "
            "spans 50 states and has a population of approximately "
            "335 million citizens and an estimated 11 million "
            "undocumented residents as of the most recent survey."
        ),
        url="https://fake.gnews.com/rpol22",
        timestamp="2026-03-15T17:30:00Z",
        engagement_score=45,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
]

# ===========================================================================
# MODERATE SCENARIO — "Federal Carbon Tax"
# 6 pro-tax, 5 anti-tax, 9 neutral/balanced
# Expected: score ~35-70 (mirrors fake_moderate_general)
# ===========================================================================

_MODERATE_QUERY = "Federal Carbon Tax"

_MODERATE_ITEMS: list[NormalizedItem] = [
    # --- FOR the Carbon Tax (stance=1, moderate animosity) ---
    NormalizedItem(
        id="real_mod_1",
        text=(
            "The Federal Carbon Tax is the only way to fund the "
            "clean energy infrastructure America desperately needs. "
            "Without it coastal communities will face catastrophic "
            "climate damage. People complaining are selfish "
            "freeloaders who refuse to pay their fair share."
        ),
        url="https://fake.reddit.com/rmod1",
        timestamp="2026-03-15T10:00:00Z",
        engagement_score=180,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_2",
        text=(
            "The Carbon Tax funds clean air programs that keep our "
            "communities safe from pollution and respiratory disease. "
            "Anyone who wants to abolish it is dangerously naive and "
            "frankly irresponsible about the environmental threats "
            "we face."
        ),
        url="https://fake.reddit.com/rmod2",
        timestamp="2026-03-15T11:00:00Z",
        engagement_score=150,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_3",
        text=(
            "Every functioning government needs revenue for public "
            "goods. Our carbon tax rate is modest by international "
            "comparison. Stop whining and contribute to the society "
            "you benefit from like every responsible citizen does."
        ),
        url="https://fake.reddit.com/rmod3",
        timestamp="2026-03-15T12:00:00Z",
        engagement_score=130,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_4",
        text=(
            "As a renewable energy developer I benefit directly from "
            "the stable policy environment the carbon tax creates. "
            "The anti-tax crowd are purely selfish — they want clean "
            "air and a stable climate without contributing a single "
            "dollar to achieve it."
        ),
        url="https://fake.reddit.com/rmod4",
        timestamp="2026-03-15T13:00:00Z",
        engagement_score=200,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_5",
        text=(
            "Every country that refused carbon pricing saw its "
            "pollution and healthcare costs balloon within a decade. "
            "The historical record is unambiguous. Tax abolitionists "
            "are simply ignoring inconvenient evidence."
        ),
        url="https://fake.reddit.com/rmod5",
        timestamp="2026-03-15T14:00:00Z",
        engagement_score=165,
        content_type="comment",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="real_mod_6",
        text=(
            "The Carbon Tax funds the public transit infrastructure "
            "that working families depend on every day. Cutting it "
            "to save a few dollars is short-sighted and cruel — "
            "you are stealing a liveable future from the next "
            "generation."
        ),
        url="https://fake.youtube.com/rmod6",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=110,
        content_type="comment",
        platform="youtube",
    ),
    # --- AGAINST the Carbon Tax (stance=-1, moderate animosity) ---
    NormalizedItem(
        id="real_mod_7",
        text=(
            "The Federal Carbon Tax has destroyed small farming "
            "families. My farm is three generations old and we can "
            "barely survive the fuel and fertiliser costs. The "
            "government takes too much and gives back almost nothing "
            "— it is robbery."
        ),
        url="https://fake.reddit.com/rmod7",
        timestamp="2026-03-15T10:30:00Z",
        engagement_score=140,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_8",
        text=(
            "I watched federal inspectors fine my neighbour's "
            "trucking business over trivial emissions calculations. "
            "This policy has gone too far. The government needs to "
            "feel the suffering it inflicts on ordinary working "
            "people before it is too late."
        ),
        url="https://fake.reddit.com/rmod8",
        timestamp="2026-03-15T11:30:00Z",
        engagement_score=120,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_9",
        text=(
            "The carbon revenue disappears into the treasury with "
            "zero public accounting. There is no proof clean energy "
            "projects are actually being built. If you just accept "
            "that without question, you are being wilfully ignorant."
        ),
        url="https://fake.reddit.com/rmod9",
        timestamp="2026-03-15T12:30:00Z",
        engagement_score=95,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_10",
        text=(
            "The local manufacturing sector collapsed the year after "
            "the carbon tax passed. Coincidence? The government "
            "caused the energy crisis and then offered the carbon "
            "tax as the cure. It is a cynical and dishonest "
            "political manoeuvre."
        ),
        url="https://fake.gnews.com/rmod10",
        timestamp="2026-03-15T13:30:00Z",
        engagement_score=85,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="real_mod_11",
        text=(
            "Young entrepreneurs are leaving for lower-tax states "
            "because this policy makes starting a business nearly "
            "impossible. We are haemorrhaging jobs and investment "
            "and the government is completely indifferent to the "
            "damage it is causing."
        ),
        url="https://fake.reddit.com/rmod11",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=75,
        content_type="comment",
        platform="reddit",
    ),
    # --- NEUTRAL / BALANCED (stance=0) ---
    NormalizedItem(
        id="real_mod_12",
        text=(
            "I think a tiered carbon tax makes more sense — small "
            "family farms pay less, large industrial emitters pay "
            "more. A flat rate hits rural communities harder than "
            "urban corporations. Balance is achievable."
        ),
        url="https://fake.reddit.com/rmod12",
        timestamp="2026-03-15T10:45:00Z",
        engagement_score=250,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_13",
        text=(
            "The carbon tax debate really depends on what region "
            "you live in. Coastal states with severe climate exposure "
            "see it differently than inland agricultural states. "
            "A blanket federal policy either way seems like the "
            "wrong approach."
        ),
        url="https://fake.reddit.com/rmod13",
        timestamp="2026-03-15T11:45:00Z",
        engagement_score=190,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_14",
        text=(
            "A new Pew Research survey found that 54% of Americans "
            "support some form of carbon pricing, while 31% favour "
            "full repeal and 15% are undecided on the best approach."
        ),
        url="https://fake.gnews.com/rmod14",
        timestamp="2026-03-15T12:45:00Z",
        engagement_score=60,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="real_mod_15",
        text=(
            "It varies by industry. Energy-intensive manufacturers "
            "face real cost burdens; tech and service firms barely "
            "notice the tax at all. There is genuinely no "
            "one-size-fits-all answer here."
        ),
        url="https://fake.reddit.com/rmod15",
        timestamp="2026-03-15T13:45:00Z",
        engagement_score=100,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_16",
        text=(
            "My state has had a carbon pricing mechanism for five "
            "years and has seen genuine emissions reductions. I "
            "cannot speak for other regions but here it seems to "
            "be working out reasonably well so far."
        ),
        url="https://fake.reddit.com/rmod16",
        timestamp="2026-03-15T14:45:00Z",
        engagement_score=80,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_17",
        text=(
            "The data on the carbon tax's effectiveness is genuinely "
            "mixed. Some regions show emissions gains; others show "
            "economic contraction. It likely depends on how state "
            "governments direct the collected revenues."
        ),
        url="https://fake.gnews.com/rmod17",
        timestamp="2026-03-15T15:00:00Z",
        engagement_score=55,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="real_mod_18",
        text=(
            "I have lived under both a cap-and-trade system and the "
            "current flat carbon tax. Each has real pros and cons. "
            "I think the best policy would let individual states "
            "decide what works for their own local economies."
        ),
        url="https://fake.reddit.com/rmod18",
        timestamp="2026-03-15T15:30:00Z",
        engagement_score=70,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_mod_19",
        text=(
            "Congress is still debating the carbon tax renewal. "
            "What is clear is that rigid mandates in either direction "
            "tend to backfire. Flexibility and state-level control "
            "consistently seem to produce better outcomes."
        ),
        url="https://fake.reddit.com/rmod19",
        timestamp="2026-03-15T16:00:00Z",
        engagement_score=65,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="real_mod_20",
        text=(
            "Research from the Brookings Institution shows that "
            "regions combining modest carbon pricing with transparent "
            "public reinvestment consistently achieve the highest "
            "clean-energy growth and citizen satisfaction scores."
        ),
        url="https://fake.gnews.com/rmod20",
        timestamp="2026-03-15T16:30:00Z",
        engagement_score=50,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
]

# ===========================================================================
# NEUTRAL SCENARIO — "New Orleans Mardi Gras"
# 15 celebratory/supportive, 5 neutral/factual
# Expected: score near 0 (mirrors fake_neutral_general)
# ===========================================================================

_NEUTRAL_QUERY = "New Orleans Mardi Gras Festival"

_NEUTRAL_ITEMS: list[NormalizedItem] = [
    NormalizedItem(
        id="real_neu_1",
        text=(
            "Mardi Gras is the highlight of the entire New Orleans "
            "calendar. The music, the cuisine, the parades — it "
            "brings every neighbourhood in the city together in "
            "pure joy. Long may it continue."
        ),
        url="https://fake.reddit.com/rneu1",
        timestamp="2026-03-15T10:00:00Z",
        engagement_score=300,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_neu_2",
        text=(
            "I brought my children to Mardi Gras in New Orleans for "
            "the first time this year and they were completely "
            "enchanted. The floats and the live jazz alone are worth "
            "the journey from across the country."
        ),
        url="https://fake.reddit.com/rneu2",
        timestamp="2026-03-15T10:30:00Z",
        engagement_score=250,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_neu_3",
        text=(
            "Mardi Gras is proof that New Orleans still knows how "
            "to celebrate life. Every neighbourhood sets aside its "
            "rivalries for the season and just enjoys being part of "
            "this city together. It is beautiful."
        ),
        url="https://fake.reddit.com/rneu3",
        timestamp="2026-03-15T11:00:00Z",
        engagement_score=220,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_neu_4",
        text=(
            "The parade captains this year outdid themselves. The "
            "Zulu and Rex floats were the most spectacular I have "
            "seen in twenty years attending. I am already counting "
            "down to next year."
        ),
        url="https://fake.youtube.com/rneu4",
        timestamp="2026-03-15T11:30:00Z",
        engagement_score=180,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="real_neu_5",
        text=(
            "Mardi Gras brings enormous trade from across the "
            "country and around the world. Visitors from every "
            "state and dozens of countries come to celebrate. "
            "The economic benefit to local businesses is enormous."
        ),
        url="https://fake.reddit.com/rneu5",
        timestamp="2026-03-15T12:00:00Z",
        engagement_score=280,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_neu_6",
        text=(
            "I met my closest friend at Mardi Gras fifteen years "
            "ago. We were strangers from different states and the "
            "festival was the first time either of us had properly "
            "talked to someone from the other's background. "
            "It changed my life."
        ),
        url="https://fake.reddit.com/rneu6",
        timestamp="2026-03-15T12:30:00Z",
        engagement_score=350,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_neu_7",
        text=(
            "The traditional second-line parades at Mardi Gras are "
            "a living piece of American cultural history. Preserving "
            "this heritage for future generations is one of the most "
            "important things New Orleans does as a community."
        ),
        url="https://fake.gnews.com/rneu7",
        timestamp="2026-03-15T13:00:00Z",
        engagement_score=120,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="real_neu_8",
        text=(
            "Every year after Mardi Gras ends, cross-neighbourhood "
            "cooperation in New Orleans goes up measurably. It is "
            "not just a party; it is the social glue that holds "
            "this unique city together."
        ),
        url="https://fake.reddit.com/rneu8",
        timestamp="2026-03-15T13:30:00Z",
        engagement_score=200,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_neu_9",
        text=(
            "Mardi Gras generates enormous cultural and economic "
            "returns for the whole state of Louisiana. This is one "
            "of the few civic traditions that virtually everyone — "
            "regardless of background or politics — agrees is "
            "worth protecting."
        ),
        url="https://fake.reddit.com/rneu9",
        timestamp="2026-03-15T14:00:00Z",
        engagement_score=175,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_neu_10",
        text=(
            "I fully support extending the Mardi Gras season by "
            "another week. The current schedule is never enough. "
            "The art installations, the music showcases, the food "
            "competitions — we need more time for all of it."
        ),
        url="https://fake.youtube.com/rneu10",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=160,
        content_type="comment",
        platform="youtube",
    ),
    NormalizedItem(
        id="real_neu_11",
        text=(
            "Mardi Gras has welcomed international visitors from "
            "over 50 countries in recent years and it has done more "
            "for New Orleans's global reputation than any marketing "
            "campaign. Shared celebration is the most powerful "
            "diplomacy there is."
        ),
        url="https://fake.reddit.com/rneu11",
        timestamp="2026-03-15T15:00:00Z",
        engagement_score=145,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_neu_12",
        text=(
            "The culinary innovation that comes out of Mardi Gras "
            "season every year — new king cake varieties, fusion "
            "street food, pop-up restaurants — has made New Orleans "
            "one of the most exciting food cities in the world."
        ),
        url="https://fake.reddit.com/rneu12",
        timestamp="2026-03-15T15:30:00Z",
        engagement_score=130,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_neu_13",
        text=(
            "Young people who attend Mardi Gras report significantly "
            "higher cultural pride and cross-community friendships "
            "in follow-up surveys. The social science on this "
            "festival is overwhelmingly positive."
        ),
        url="https://fake.gnews.com/rneu13",
        timestamp="2026-03-15T16:00:00Z",
        engagement_score=90,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="real_neu_14",
        text=(
            "I watched the Mardi Gras opening parade with my whole "
            "neighbourhood. When the Krewe banners went up everyone "
            "cheered as one. This is what it means to be from "
            "New Orleans."
        ),
        url="https://fake.reddit.com/rneu14",
        timestamp="2026-03-15T16:30:00Z",
        engagement_score=190,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_neu_15",
        text=(
            "We should absolutely increase the Mardi Gras city "
            "budget. Compared to the cost of routine municipal "
            "events, the festival is a bargain that benefits every "
            "single resident regardless of neighbourhood or income."
        ),
        url="https://fake.reddit.com/rneu15",
        timestamp="2026-03-15T17:00:00Z",
        engagement_score=155,
        content_type="comment",
        platform="reddit",
    ),
    NormalizedItem(
        id="real_neu_16",
        text=(
            "The New Orleans Mardi Gras celebration has been held "
            "annually since at least 1837, making it one of the "
            "oldest continuous public festivals in the United States "
            "at nearly 190 consecutive editions."
        ),
        url="https://fake.gnews.com/rneu16",
        timestamp="2026-03-15T17:30:00Z",
        engagement_score=40,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="real_neu_17",
        text=(
            "This year's Mardi Gras is scheduled for the week "
            "leading up to Fat Tuesday in late February. It will "
            "be centred on the French Quarter and St. Charles "
            "Avenue for the second consecutive year following "
            "major infrastructure upgrades."
        ),
        url="https://fake.gnews.com/rneu17",
        timestamp="2026-03-15T18:00:00Z",
        engagement_score=35,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="real_neu_18",
        text=(
            "Mardi Gras employs approximately 38,000 temporary and "
            "seasonal workers across the Greater New Orleans area "
            "and draws an estimated 1.4 million visitors over the "
            "two-week celebration period."
        ),
        url="https://fake.gnews.com/rneu18",
        timestamp="2026-03-15T18:30:00Z",
        engagement_score=25,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="real_neu_19",
        text=(
            "The Louisiana Office of Tourism estimates that Mardi "
            "Gras generates approximately 1.1 billion dollars in "
            "direct economic activity for the state economy "
            "each year."
        ),
        url="https://fake.gnews.com/rneu19",
        timestamp="2026-03-15T19:00:00Z",
        engagement_score=30,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
    NormalizedItem(
        id="real_neu_20",
        text=(
            "The New Orleans City Council voted unanimously last "
            "session to extend Mardi Gras's protected cultural "
            "heritage status for another 25 years. The motion had "
            "support from all district representatives."
        ),
        url="https://fake.gnews.com/rneu20",
        timestamp="2026-03-15T19:30:00Z",
        engagement_score=20,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
]


FAKE_SCENARIOS: dict[str, tuple[str, list[NormalizedItem]]] = {
    "fake_polarized_real_context": (_POLARIZED_QUERY, _POLARIZED_ITEMS),
    "fake_moderate_real_context": (_MODERATE_QUERY, _MODERATE_ITEMS),
    "fake_neutral_real_context": (_NEUTRAL_QUERY, _NEUTRAL_ITEMS),
}


def get_fake_data(mode: str) -> tuple[str, list[NormalizedItem]]:
    """Return (query, items) for a real-world-context scenario.

    Raises KeyError if mode is not a known scenario.
    """
    return FAKE_SCENARIOS[mode]
