# StreamIQ — Plain-English Product Analytics & Experimentation Guide

A beginner-friendly, mathematically accurate guide to understanding, interpreting, and presenting the metrics and product analytics in StreamIQ.

---

## 1. Executive Headline Metrics

### 1.1 Registered Users vs. Active Viewers

* **Simple Explanation**: 
  - **Registered Users**: How many total user accounts have signed up on the platform.
  - **Active Viewers**: How many of those registered users actually opened the app or watched something during the selected time period.
* **Calculation**:
  - Registered Users: $\text{COUNT}(\text{DISTINCT user\_id})$ from account creation records within the selected date range.
  - Active Viewers: $\text{COUNT}(\text{DISTINCT user\_id})$ with at least one recorded event (`app_open`, `search`, `content_view`, `playback_start`, `playback_complete`) within the selected date window.
* **Why It Matters**:
  - Having 100,000 registered accounts means very little if only 5,000 of them are actually opening the app. The ratio of Active Viewers to Registered Users shows overall platform health and dormancy.
* **Common Interpretation Pitfalls (Interview Prep)**:
  - **Pitfall**: Assuming every registered user is active. In digital streaming, 20% to 50% of signups may become inactive within a month. Always ask: *"Over what time window is an 'active' user defined?"*

---

### 1.2 Sessions per Active Viewer

* **Simple Explanation**: On average, how many times an active viewer visited the streaming app during the selected timeframe.
* **Calculation**:
  $$\text{Sessions per Active Viewer} = \frac{\text{Total Recorded Sessions}}{\text{Number of Active Viewers}}$$
  *(Handled safely: returns `0.0` if active viewers equals 0).*
* **Why It Matters**:
  - Measures habitual engagement. If viewers visit 1.2 times a week, they are occasional browsers; if they visit 5+ times a week, streaming has become part of their daily routine.
* **Common Interpretation Pitfalls (Interview Prep)**:
  - **Pitfall**: An increase in sessions isn't always good if it's caused by user frustration (e.g. app crashes forcing users to reopen the app multiple times in an hour). Pair session counts with duration and completion metrics.

---

### 1.3 Video Completion Rate

* **Simple Explanation**: When someone presses 'Play' on a video, what percentage of the time do they watch it all the way through?
* **Calculation**:
  $$\text{Completion Rate (\%)} = \left( \frac{\text{Completed Streams}}{\text{Playback Starts}} \right) \times 100$$
* **Why It Matters**:
  - High completion rates mean viewers found content compelling and experienced no technical buffering issues. Low completion rates indicate either misleading thumbnails, poor recommendations, or streaming quality issues.
* **Common Interpretation Pitfalls (Interview Prep)**:
  - **Pitfall**: Comparing 2-hour movies against 20-minute sitcom episodes without context. Shorter content naturally has a higher completion rate than long films.

---

## 2. Chronological Funnel Metrics

StreamIQ tracks users across a strict 4-step onboarding journey:
$$\text{Registered} \longrightarrow \text{Opened App} \longrightarrow \text{Viewed Content} \longrightarrow \text{Started Playback}$$

### 2.1 Step Conversion Rate vs. Overall Conversion Rate

* **Simple Explanation**:
  - **Step Conversion Rate**: What percentage of users who reached the *previous* step made it to the *current* step? (e.g. Of users who opened the app, what percentage clicked on a show?).
  - **Overall Conversion Rate**: What percentage of users from the *initial starting cohort* (Registered) made it all the way to this step?
* **Calculation**:
  $$\text{Step Conversion Rate}_i = \left( \frac{\text{Users reaching Step } i}{\text{Users reaching Step } i-1} \right) \times 100$$
  $$\text{Overall Conversion Rate}_i = \left( \frac{\text{Users reaching Step } i}{\text{Total Users who Registered (Step 1)}} \right) \times 100$$
* **Why It Matters**:
  - Overall conversion tells you total funnel efficiency from end-to-end. Step conversion isolates exactly where the biggest leak is so you know what team to assign (e.g. UI/UX, catalog search, or player performance).
* **Common Interpretation Pitfalls (Interview Prep)**:
  - **Pitfall**: Confusing Step Conversion with Overall Conversion. If Step 3 has a 50% step conversion and Step 4 has a 50% step conversion, overall conversion from Step 2 is $50\% \times 50\% = 25\%$, not 50%.

---

### 2.2 Funnel Drop-off & Users Lost

* **Simple Explanation**:
  - **Users Lost**: The raw count of individual users who abandoned the journey between the previous step and the current step.
  - **Drop-off Rate**: The percentage of viewers from the preceding step who gave up before reaching the current step.
* **Calculation**:
  $$\text{Users Lost}_i = \text{Users}_{i-1} - \text{Users}_i$$
  $$\text{Drop-off Rate}_i = 100\% - \text{Step Conversion Rate}_i = \left( \frac{\text{Users Lost}_i}{\text{Users}_{i-1}} \right) \times 100$$
* **Why It Matters**:
  - Finding the **primary bottleneck** (the step with the largest volume of lost users) directs engineering and product resources to the highest-leverage opportunity.
* **Common Interpretation Pitfalls (Interview Prep)**:
  - **Pitfall**: Looking only at percentages instead of raw user volumes. A 90% drop-off on a step with 10 users loses 9 people; a 30% drop-off on a step with 10,000 users loses 3,000 people. Prioritize by business impact and user volume.

---

### 2.3 Chronological Sequence & Observation Windows

* **Strict Chronological Sequence**:
  - In StreamIQ, a user only counts at Step 3 (`content_view`) if their `content_view` event occurred **after** their `app_open` event. We never count actions out of sequence.
* **Conversion Observation Window**:
  - If a 7-day conversion window is selected, downstream events only count if they occur within 7 days of the user's registration date.
  - Crucially, brand-new accounts created less than 7 days ago are excluded from the denominator to avoid treating pending users as churned.

---

## 3. Retention & Cohort Metrics

### 3.1 Exact-Day Retention (Day 1, Day 7, Day 30)

* **Simple Explanation**: What percentage of new subscribers came back and performed an activity on *specifically* their 1st, 7th, or 30th calendar day after creating an account?
* **Calculation**:
  $$\text{Day } N \text{ Return Rate (\%)} = \left( \frac{\text{Eligible Users who Returned on exactly Day } N}{\text{Total Eligible Users Registered } \ge N \text{ days ago}} \right) \times 100$$
* **Why It Matters**:
  - **Day 1**: Measures first-day experience and initial setup success.
  - **Day 7**: Measures early habit formation (did they return a week later?).
  - **Day 30**: Predicts recurring subscription renewal and long-term Customer Lifetime Value (LTV).
* **Common Interpretation Pitfalls (Interview Prep)**:
  - **Pitfall**: Failing to exclude immature cohorts. If a user registered 2 days ago, they *cannot* have completed Day 7 or Day 30 yet. Including them in the denominator falsely lowers retention rates. StreamIQ uses a strict **Observation Window Policy** that only evaluates mature accounts.

---

### 3.2 Exact-Day Retention vs. Rolling (Return) Retention

* **Exact-Day Retention (Strict Standard)**:
  - A user is counted as retained on Day 7 **only if** they returned on calendar Day 7.
* **Rolling Retention (Cumulative Standard)**:
  - A user is counted as retained on Day 7 if they returned on Day 7 **or any day after Day 7**.
* **Why StreamIQ uses Exact-Day**:
  - Exact-day retention catches daily engagement decay and weekly seasonality patterns that rolling retention smooths away. In an interview, explain that you understand both methods and chose exact-day to measure habituation precision.

---

### 3.3 Cohort Retention Heatmap

* **Simple Explanation**: A table where rows are groups of users who signed up in the same week or month (cohorts), and columns show how their return rate evolves in subsequent weeks (Week 0, Week 1, Week 2, etc.).
* **How to Read It**:
  - Read **left-to-right across a row** to watch a single group of users decay over time.
  - Read **top-to-bottom down a column** to see if newer product updates are improving retention for newer cohorts compared to older cohorts.
  - **Blank / Light Grey Cells**: Future periods that have not elapsed yet. We intentionally show them as blank (`NaN`) rather than `0.0%` so the chart doesn't look like a cliff.

---

## 4. Audience Lifecycle Segmentation

StreamIQ partitions users into 4 transparent, rule-based categories:

| Segment Name | Rule Definition | Business Meaning & Strategy |
| :--- | :--- | :--- |
| **New Users** | Signed up $\le 7$ days ago | Protected from being categorized as inactive while exploring the catalog. Focus: smooth onboarding. |
| **Highly Active** | $\ge 15$ lifetime sessions | Power viewers who drive watch-time and brand advocacy. Focus: VIP content perks and early access. |
| **Moderately Active** | 5 to 14 lifetime sessions | Regular, habitual subscribers with steady engagement. Focus: personalized watchlist recommendations. |
| **Low Activity** | 1 to 4 sessions (joined $> 7$ days ago) | At-risk subscribers who stopped returning. Focus: win-back campaigns and re-engagement push notifications. |

* **Common Interpretation Pitfalls (Interview Prep)**:
  - **Pitfall**: Assuming low activity is solely caused by poor content. It could be due to billing friction, device incompatibility, or notification fatigue. Always test hypotheses before assuming the root cause.

---

## 5. Statistical A/B Testing & Experimentation

### 5.1 Absolute Lift vs. Relative Lift

* **Simple Explanation**:
  - **Absolute Lift**: The direct difference in percentage points between the treatment and control conversion rates.
  - **Relative Lift**: The percentage increase of the treatment relative to the control group's baseline.
* **Example**:
  - Control Conversion = $10.00\%$
  - Treatment Conversion = $16.00\%$
  - **Absolute Lift** = $16.00\% - 10.00\% = \mathbf{+6.00\text{ percentage points (pp)}}$
  - **Relative Lift** = $\frac{16.00 - 10.00}{10.00} \times 100 = \mathbf{+60.00\%}$
* **Common Interpretation Pitfalls (Interview Prep)**:
  - **Major Interview Red Flag**: Calling a move from 10% to 16% a "6% increase". It is a **6 percentage point** increase or a **60% relative** increase. Mixing these up is an immediate interview disqualifier.

---

### 5.2 P-Value & Statistical Significance

* **Simple Explanation**:
  - **P-Value**: The probability of observing a difference at least as large as the one seen, assuming the two versions are actually identical (the Null Hypothesis is true).
  - **Alpha ($\alpha = 0.05$)**: The accepted risk threshold (5%). If $p < 0.05$, we conclude that random variation alone is an unlikely explanation for the observed difference, calling it **statistically significant**.
* **Common Interpretation Pitfalls (Interview Prep)**:
  - **Pitfall**: Saying *"A p-value of 0.03 means there is a 97% chance the feature will succeed in production."* That is incorrect. The p-value only tells you how surprising the experimental sample data is under the assumption that the feature has zero real effect.

---

### 5.3 95% Confidence Interval

* **Simple Explanation**: A range showing the plausible uncertainty around our estimated treatment effect.
* **How to Read It**:
  - If the 95% Confidence Interval is `[+2.10 pp, +9.90 pp]`: The interval is entirely above zero, giving strong confidence that the feature improves conversion.
  - If the 95% Confidence Interval crosses zero, e.g. `[-1.50 pp, +3.20 pp]`: The true effect could be slightly negative, zero, or slightly positive. The result is inconclusive.
* **Methodology in StreamIQ**:
  - Uses the **Wald interval** for large samples where normal approximation holds.
  - Automatically switches to the **Agresti-Caffo interval** for small samples ($< 5$ conversions) and clamps the result strictly within valid probability bounds `[-100%, +100%]`.

---

### 5.4 Minimum Practical Effect Threshold (Business Hurdle)

* **Simple Explanation**: The minimum improvement required to justify the operational complexity, engineering maintenance, and server costs of releasing a new feature.
* **Why It Matters**:
  - With a huge sample size (e.g. 500,000 users), a tiny lift of $+0.05\text{ pp}$ might be *statistically significant* ($p < 0.001$). But is a $+0.05\text{ pp}$ lift worth maintaining hundreds of lines of code and confusing users?
  - StreamIQ enforces a default practical significance threshold ($\Delta \ge 0.50\text{ pp}$). If a feature wins with $p < 0.05$ but lifts conversion by only $+0.20\text{ pp}$, the recommendation is **CONTINUE TESTING / INVESTIGATE**, not Ship.
* **Distinction from Power Calculation**:
  - In experiment design, "Minimum Detectable Effect" (MDE) can refer to the sample size calculation needed before launching a test. Here in StreamIQ, it is explicitly evaluated as a post-test **launch hurdle**.

---

### 5.5 Traffic Split Check (Sample Ratio Mismatch - SRM)

* **Simple Explanation**: Checks whether viewers were divided between the test groups in the proportions planned (e.g. 50/50, or 10/90 for a canary test).
* **Calculation**:
  - Pearson's Chi-Square Goodness-of-Fit test comparing observed counts against expected counts based on `expected_control_share`.
  - A threshold of $p_{SRM} < 0.01$ indicates a critical mismatch.
* **Why It Matters**:
  - If an experiment was supposed to allocate users 50/50, but ends up at 40/60, **do not trust the results**! It usually indicates that users in one variant experienced crashes that prevented their assignment from logging, or that the randomization algorithm was biased.
  - StreamIQ automatically blocks a **SHIP** recommendation whenever an SRM is detected.

---

### 5.6 Guardrail Metrics (Quality Safeguards)

* **Simple Explanation**: Secondary metrics that measure user experience quality and platform reliability. They ensure a win on the primary target metric doesn't come at the cost of breaking the product.
* **StreamIQ Guardrails**:
  1. **Playback Error Rate**: Must not increase by more than $+0.50\text{ pp}$.
  2. **Playback Completion Rate**: Must not drop by more than $-3.00\text{ pp}$.
* **Why It Matters**:
  - If an aggressive autoplay feature increases clicks by $+10\%$, but video buffer errors skyrocket by $+3\%$, shipping it would damage subscriber trust and cause long-term churn. StreamIQ enforces a **DO NOT SHIP** decision if guardrails are breached.

---

## 6. Decision Framework Summary

StreamIQ synthesizes statistical significance, practical effect, traffic integrity, and guardrail health into a clear 3-tier verdict:

```
                                  [ Experiment Results ]
                                            │
                             Is SRM or Telemetry Corrupted?
                                     /             \
                                   YES              NO
                                   /                 \
                  [ CONTINUE TESTING / INVESTIGATE ]   Did Guardrails Breach?
                                                            /         \
                                                          YES          NO
                                                          /             \
                                                  [ DO NOT SHIP ]     Is p < 0.05 & Lift > 0?
                                                                           /         \
                                                                         YES          NO
                                                                         /             \
                                                      Is Lift >= Practical Hurdle?   [ Inconclusive / Negative ]
                                                              /             \
                                                            YES              NO
                                                            /                 \
                                                       [ SHIP ]     [ CONTINUE TESTING ]
```

---

## 7. Quick Reference: Interview Talking Points

When presenting StreamIQ in Data Analyst or Product Management interviews, highlight these engineering practices:

1. **"I enforced strict chronological funnels"**: Explain how CTE joins ensure users only qualify at Step 3 if Step 2 occurred before Step 3.
2. **"I protected against artificial churn bias in cohorts"**: Explain why recent signups are excluded from Day 30 denominators, and why incomplete heatmap periods are masked with `NaN`.
3. **"I separated statistical significance from practical business impact"**: Explain how high sample sizes can produce meaningless tiny wins, and why a minimum practical hurdle (0.50 pp) is required to ship.
4. **"I verified sample integrity with automated SRM checks"**: Mention Pearson's Chi-Square goodness-of-fit testing and how telemetry checks catch duplicate variant assignments.
5. **"I treated data as simulated and hypothesis-driven"**: Explain that correlation is not causation, and that recommendations provide actionable next steps and guardrails rather than claiming unproven certainty.
