"""Fake scraped data for pipeline testing.

Three scenarios designed to produce predictable polarization scores
when run through the real LLM assessment pipeline:
- polarized: ~100 (equal passionate for/against, high animosity)
- moderate: ~35-70 (some disagreement, many neutrals)
- neutral: ~0 (consensus agreement, low animosity)
"""

from __future__ import annotations

from src.internal.pipeline.domain import NormalizedItem

# ---------------------------------------------------------------------------
# Scenario 1: EXTREMELY POLARIZED — "Gun Control in America"
# 10 passionate pro-control, 10 passionate anti-control, 2 neutral
# Expected: score near 100
# ---------------------------------------------------------------------------

_POLARIZED_QUERY = "gun control in America"

_POLARIZED_ITEMS: list[NormalizedItem] = [
    # --- FOR gun control (stance=1, high animosity) ---
    NormalizedItem(
        id="fake_pol_1",
        text=(
            "How many more children need to die before we ban assault "
            "weapons? The gun lobby has blood on its hands and every "
            "politician who takes NRA money is complicit in murder."
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
            "Every other developed nation has strict gun laws and a "
            "fraction of our mass shootings. America's refusal to act "
            "is a disgusting moral failure. Ban them all."
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
            "I am so sick of the 'thoughts and prayers' nonsense. We "
            "need universal background checks, assault weapon bans, "
            "and red flag laws NOW. No more excuses."
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
            "The Second Amendment was written when muskets existed. "
            "Using it to justify AR-15 ownership is delusional and "
            "dangerous. Strict regulation is the only sane path."
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
            "Gun violence is an epidemic. 45,000 Americans dead every "
            "year and we do NOTHING. Anyone opposing gun control at "
            "this point is morally bankrupt."
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
            "Australia banned guns after one mass shooting and hasn't "
            "had one since. The data is overwhelming. American gun "
            "culture is a death cult."
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
            "No civilian needs a weapon designed for war. These guns "
            "exist only to kill as many people as fast as possible. "
            "Ban assault weapons immediately."
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
            "The gun lobby has purchased our democracy. They profit "
            "from death while children cower under desks during "
            "active shooter drills. This is America's shame."
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
            "I'm a teacher and I have to practice lockdown drills "
            "with terrified 6-year-olds. Anyone who says guns aren't "
            "the problem can go straight to hell."
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
            "Countries with gun control have safer schools, safer "
            "streets, and fewer funerals. It is not complicated. "
            "The only obstacle is corrupt politicians and the NRA."
        ),
        url="https://fake.reddit.com/pol10",
        timestamp="2026-03-15T16:30:00Z",
        engagement_score=155,
        content_type="comment",
        platform="reddit",
    ),
    # --- AGAINST gun control (stance=-1, high animosity) ---
    NormalizedItem(
        id="fake_pol_11",
        text=(
            "The Second Amendment is sacred and non-negotiable. "
            "Anyone trying to take our guns is a tyrant. Shall not "
            "be infringed means shall NOT be infringed. Period."
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
            "Gun control is just the beginning. They want to strip "
            "all our constitutional rights. I will never surrender "
            "my firearms to an overreaching government."
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
            "Criminals don't follow laws. More gun laws only disarm "
            "law-abiding citizens and leave them defenseless. This "
            "is basic common sense that the left refuses to accept."
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
            "An armed society is a free society. Every dictatorship "
            "in history started by disarming its citizens. I'd rather "
            "die on my feet than live on my knees."
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
            "The anti-gun crowd is delusional. They live in gated "
            "communities with private security while telling us we "
            "can't protect our own families. Pure hypocrisy."
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
            "My gun saved my family during a home invasion. Without "
            "it we'd be dead. Nobody has the right to take away my "
            "ability to defend my loved ones. Nobody."
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
            "Chicago has the strictest gun laws in the country and "
            "the worst gun violence. Gun control doesn't work. It "
            "never has and it never will. End of discussion."
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
            "The founding fathers gave us the right to bear arms so "
            "we could resist tyranny. Every gun law is an attack on "
            "liberty itself. I will not comply."
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
            "You want to ban AR-15s? Come and take them. Millions "
            "of responsible gun owners are tired of being punished "
            "for the actions of criminals and lunatics."
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
            "Gun ownership is an individual right confirmed by the "
            "Supreme Court. The left's obsession with disarming "
            "citizens is un-American and unconstitutional."
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
            "The gun control debate in America is complex. Both "
            "sides raise valid concerns about safety and rights. "
            "Finding common ground remains a challenge."
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
            "According to the latest statistics, there were 48,830 "
            "gun deaths in the U.S. last year. This includes "
            "suicides, homicides, and accidental deaths."
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
# Scenario 2: SOMEWHAT POLARIZED — "Remote Work Policies"
# 6 pro-remote, 5 anti-remote, 9 neutral/balanced
# Expected: score ~35-70
# ---------------------------------------------------------------------------

_MODERATE_QUERY = "mandatory return to office policies"

_MODERATE_ITEMS: list[NormalizedItem] = [
    # --- FOR remote work / against RTO (stance=1, moderate animosity) ---
    NormalizedItem(
        id="fake_mod_1",
        text=(
            "Forcing employees back to the office is a trust issue, "
            "not a productivity issue. I get more done at home "
            "without pointless meetings and distractions."
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
            "My commute was 90 minutes each way. Remote work gave "
            "me 3 hours of my life back daily. Companies mandating "
            "return to office are tone-deaf."
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
            "Remote work has been proven to increase productivity "
            "in multiple studies. RTO mandates are about control, "
            "not results."
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
            "As a working parent, remote work has been life-changing. "
            "I can actually be present for my kids while still "
            "delivering excellent work. Don't take this away."
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
            "Every company forcing RTO is seeing their best people "
            "leave for remote-friendly competitors. It's a talent "
            "retention disaster."
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
            "The environmental benefits of remote work alone should "
            "be enough to keep it. Less commuting means less "
            "pollution. RTO mandates are backwards."
        ),
        url="https://fake.youtube.com/mod6",
        timestamp="2026-03-15T14:30:00Z",
        engagement_score=110,
        content_type="comment",
        platform="youtube",
    ),
    # --- AGAINST remote work / for RTO (stance=-1, moderate animosity) ---
    NormalizedItem(
        id="fake_mod_7",
        text=(
            "Remote work has destroyed team culture. New hires have "
            "no mentorship, no spontaneous collaboration. We need "
            "people back in the office."
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
            "I manage a team and half of them are clearly not "
            "working full hours from home. Accountability requires "
            "physical presence."
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
            "Companies invested billions in office space. They have "
            "a right to expect employees to use it. If you don't "
            "like it, find another job."
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
            "Innovation happens in person. The best ideas come from "
            "whiteboard sessions and hallway conversations, not "
            "Zoom calls."
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
            "Junior employees learn by sitting near senior people. "
            "Remote work is fine for veterans but terrible for "
            "career development of newer staff."
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
            "I think a hybrid approach works best. Two or three "
            "days in office for collaboration, rest at home for "
            "focused work. Balance is key."
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
            "The remote vs office debate really depends on the role. "
            "Some jobs need in-person presence, others don't. A "
            "blanket policy either way seems wrong."
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
            "A new survey found that 62% of workers prefer hybrid "
            "arrangements, with only 15% wanting fully remote and "
            "23% preferring full-time office."
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
            "It varies by industry. Tech can go remote easily, but "
            "healthcare and manufacturing obviously can't. There's "
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
            "My company does three days in, two days out. Honestly "
            "it works pretty well. Meetings on office days, deep "
            "work on home days."
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
            "The data on remote work productivity is genuinely mixed. "
            "Some studies show gains, others show losses. It likely "
            "depends on management quality."
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
            "I've worked both remote and in-office. Each has pros "
            "and cons. I think the best policy lets teams decide "
            "what works for them."
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
            "Companies are still figuring this out. What's clear is "
            "that rigid mandates in either direction tend to backfire. "
            "Flexibility seems to be the answer."
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
            "Research from Stanford shows hybrid models have the "
            "highest employee satisfaction scores while maintaining "
            "similar productivity to pre-pandemic levels."
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
# Scenario 3: NOT POLARIZED — "Space Exploration and NASA Funding"
# 15 supportive (all same side), 0 opposed, 5 neutral/factual
# Expected: score near 0
# ---------------------------------------------------------------------------

_NEUTRAL_QUERY = "NASA funding and space exploration"

_NEUTRAL_ITEMS: list[NormalizedItem] = [
    # --- ALL FOR space exploration (stance=1, low animosity) ---
    NormalizedItem(
        id="fake_neu_1",
        text=(
            "Space exploration inspires the next generation of "
            "scientists and engineers. NASA funding is one of the "
            "best investments we can make as a society."
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
            "The technology spinoffs from space research alone "
            "justify the cost. Memory foam, water filters, scratch-"
            "resistant lenses — all came from NASA."
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
            "Increasing NASA's budget would accelerate our progress "
            "toward Mars and help us understand climate change "
            "better through Earth observation satellites."
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
            "Space exploration unites people across political lines. "
            "Everyone cheered when we landed on the moon. We need "
            "more of that shared purpose."
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
            "NASA's James Webb Space Telescope has been incredible. "
            "The images and discoveries coming back prove that "
            "space investment pays off enormously."
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
            "I took my daughter to a NASA exhibit last week and she "
            "said she wants to be an astronaut. This is why we fund "
            "space programs — to give kids big dreams."
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
            "The commercial space industry is booming because of "
            "decades of NASA research. Public investment created "
            "the foundation for companies like SpaceX."
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
            "Space exploration is about the long-term survival of "
            "humanity. We can't keep all our eggs in one planetary "
            "basket. Funding NASA is funding our future."
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
            "NASA's budget is less than 1% of federal spending but "
            "produces incredible returns. Space science gives us "
            "GPS, weather forecasting, and so much more."
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
            "I fully support increasing NASA funding. Space "
            "exploration represents the best of human curiosity "
            "and our drive to explore the unknown."
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
            "The international cooperation that space programs "
            "foster is beautiful. The ISS is proof that nations "
            "can work together on something bigger than politics."
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
            "Asteroid mining could solve resource scarcity on Earth. "
            "Investing in space tech now will pay dividends for "
            "centuries. Absolutely worth funding."
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
            "Space research has given us better medical imaging, "
            "improved food safety, and advanced materials. The "
            "practical benefits are enormous and undeniable."
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
            "I remember watching the Perseverance landing with my "
            "whole family. Moments like that bring people together. "
            "Space exploration is worth every penny."
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
            "We should absolutely increase NASA's budget. Compared "
            "to military spending, space exploration is a bargain "
            "that benefits all of humanity."
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
            "NASA's 2026 budget proposal allocates $27.2 billion, "
            "a 7% increase over the previous year. The Artemis "
            "program receives the largest share."
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
            "The Artemis III mission is scheduled for late 2026. "
            "It will be the first crewed moon landing since Apollo "
            "17 in 1972."
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
            "NASA currently employs about 18,000 civil servants "
            "across 10 field centers, with an additional 40,000+ "
            "contractor positions supporting its missions."
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
            "The space economy is estimated to be worth over $500 "
            "billion globally. Both public agencies and private "
            "companies are driving growth in the sector."
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
            "Congress approved a bipartisan space exploration bill "
            "last year. The bill has broad support across both "
            "parties in the House and Senate."
        ),
        url="https://fake.gnews.com/neu20",
        timestamp="2026-03-15T19:30:00Z",
        engagement_score=20,
        content_type="post",
        platform="gnews",
        source_lean="center",
    ),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

FAKE_SCENARIOS: dict[str, tuple[str, list[NormalizedItem]]] = {
    "fake_polarized": (_POLARIZED_QUERY, _POLARIZED_ITEMS),
    "fake_moderate": (_MODERATE_QUERY, _MODERATE_ITEMS),
    "fake_neutral": (_NEUTRAL_QUERY, _NEUTRAL_ITEMS),
}


def get_fake_data(mode: str) -> tuple[str, list[NormalizedItem]]:
    """Return (query, items) for a fake scenario.

    Raises KeyError if mode is not a known fake scenario.
    """
    return FAKE_SCENARIOS[mode]
