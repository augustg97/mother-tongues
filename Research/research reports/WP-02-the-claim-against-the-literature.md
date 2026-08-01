# WP-02 — Our result against the published literature, and a negative result on time-depth

*Round 9, 2026-07-31. Closes register **C4** and **C8**.*

## Executive summary

Our measurement agrees with the published consensus on the thing that matters most, and the
agreement is not vague: **climate beats terrain, by roughly the same margin, in the same
direction.** One caveat runs against us and is recorded here rather than buried. Separately,
the standard third explanation — that diversity accumulates with **time since settlement** —
is tested here for the first time and **fails**.

## 1. C4 — the literature check

The most direct comparison is Hua, Greenhill, Cardillo, Schneemann & Bromham, *The ecological
drivers of variation in global language diversity*, **Nature Communications 10:2047 (2019)**.
Its finding, in its authors' words, is that **"climate has a much stronger effect on language
diversity than landscape features, such as altitudinal range and river density"**, supporting
the **ecological risk hypothesis**: areas of high year-round productivity carry more languages
because they support cultural groups with smaller distributions. They also conclude that the
well-known biodiversity–language correlation "appears to be an incidental effect of their
covariation with climate, rather than a causal link between the two."

| | published | ours |
|---|---|---|
| climate vs terrain | climate "much stronger" | growing season **+0.470**, peak NDVI **+0.347**, ruggedness **+0.155** — roughly 3:1 |
| direction of climate | more productivity → more languages | positive, both measures |
| direction of terrain | weak, positive | weak, positive, and robust to redefinition (relief/km **+0.192**) |
| mechanism | ecological risk / year-round productivity | not tested — we measure the pattern, not the mechanism |

**Where we differ, and it is our problem, not theirs.** In our data **absolute latitude is
still the strongest single predictor (−0.527)**, and growing season does not survive
controlling for it (**−0.091**). Hua et al. fit multi-predictor spatial models that account for
spatial autocorrelation; we fit rank correlations and a count model on 2° cells with no spatial
term. Neighbouring cells are not independent observations, so our intervals are optimistic even
after the negative binomial, and latitude is exactly the variable a missing spatial term would
inflate. **This is the largest known methodological gap in the project's central claim** and it
is now register item **C10**.

## 2. C8 — settlement time-depth: a negative result

**Data.** p3k14c (Bird et al., *Scientific Data* 9:27, 2022): 173,946 archaeological
radiocarbon determinations with coordinates. Per 2° cell, the oldest date is a floor on
occupation; the number of dates is a measure of how hard anyone has looked.

**Result** (1,447 cells with ≥3 dates, 20% of land cells, median oldest date 9,240 BP):

| | |
|---|---|
| oldest date vs richness, raw | **−0.092** |
| holding excavation effort constant | **−0.147** |
| holding latitude constant | **+0.027** |
| number of dates vs oldest date | **+0.449** |

**Time-depth does not explain language richness.** The raw correlation is slightly negative,
and it gets *more* negative once excavation effort is controlled. The effort confound is real
and large — the number of dates in a cell predicts its oldest date at +0.449 — which is why
the raw figure is not the answer to anything.

**What this does not show.** Radiocarbon coverage maps archaeologists, not people: western
Europe and the United States are saturated, New Guinea and central Africa nearly blank. Every
number above is conditioned on the "has been excavated at all" sample, which excludes precisely
the regions where the time-depth hypothesis would be most interesting. The honest statement is
**not** "time-depth doesn't matter" but "in the fifth of the world's land that archaeology has
sampled, time-depth carries no signal once effort is accounted for."

Status: **CLOSED, negative result.** Recorded so nobody spends another round on it without
first solving the sampling problem.

## 3. Actions

- **C4 RESOLVED** — consistent with the literature; the comparison is above.
- **C8 CLOSED, negative result.**
- **C10 NEW, P1** — no spatial autocorrelation term. Our latitude coefficient is the one most
  likely to be inflated by it. Fit a spatial model, or at minimum report Moran's I on the
  residuals, before quoting latitude against climate again.
