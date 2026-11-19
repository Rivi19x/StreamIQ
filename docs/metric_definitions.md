# StreamIQ — Mathematical & Analytical Metric Definitions

This document details the mathematical formulations, SQL implementation logic, eligibility constraints, and edge-case behaviors for all analytics metrics implemented across the StreamIQ platform.

---

## 1. Executive Headline KPIs

### 1.1 Total Registered Users
* **Definition**: Cumulative count of unique user accounts registered within the platform database matching selected filter attributes (acquisition channel, subscription plan).
* **Mathematical Formula**:
  $$\text{Total Users} = \sum_{u \in \mathcal{U}} \mathbb{I}(\text{channel}(u) \in \mathcal{C} \land \text{plan}(u) \in \mathcal{P})$$
* **Edge Case Handling**: Defaults to 0 if no accounts match filtering criteria.

### 1.2 Active Users
* **Definition**: Distinct count of registered users who performed at least one qualifying platform event (`app_open`, `search`, `content_view`, `playback_start`, `playback_complete`) within the observation window.
* **Mathematical Formula**:
  $$\text{Active Users} = |\{u \in \mathcal{U} : \exists e \in \mathcal{E} \text{ where } \text{user}(e) = u \land t_{start} \le \text{timestamp}(e) \le t_{end}\}|$$

### 1.3 Sessions per Active User
* **Definition**: Average session density per active subscriber over the selected period.
* **Mathematical Formula**:
  $$\text{Sessions per Active User} = \begin{cases} \frac{\text{Total Distinct Sessions}}{\text{Active Users}}, & \text{if Active Users} > 0 \\ 0.0, & \text{otherwise} \end{cases}$$

### 1.4 Playback Completion Rate
* **Definition**: Proportion of video playback sessions that successfully reach completion status (`playback_complete`), relative to eligible stream starts (`playback_start`).
* **Mathematical Formula**:
  $$\text{Completion Rate (\%)} = \begin{cases} \left( \frac{\sum \mathbb{I}(e_{type} = \text{'playback\_complete'})}{\sum \mathbb{I}(e_{type} = \text{'playback\_start'})} \right) \times 100, & \text{if Starts} > 0 \\ 0.0, & \text{otherwise} \end{cases}$$

---

## 2. Chronological Funnel Conversion

StreamIQ tracks user progression through a strict 4-stage sequential onboarding and consumption journey:
1. **Registered**: User account created within cohort window.
2. **Opened App**: Distinct user triggered an `app_open` event at timestamp $t_{open} \ge t_{signup}$.
3. **Viewed Content**: Distinct user triggered a `content_view` event at timestamp $t_{view} \ge t_{open}$.
4. **Started Playback**: Distinct user triggered a `playback_start` event at timestamp $t_{start} \ge t_{view}$.

### Funnel Formulas
* **Step Conversion Rate ($Stage_i$)**:
  $$\text{Step Conversion}_{i} = \frac{\text{Users}(Stage_i)}{\text{Users}(Stage_{i-1})} \times 100$$
* **Overall Conversion Rate ($Stage_i$)**:
  $$\text{Overall Conversion}_{i} = \frac{\text{Users}(Stage_i)}{\text{Users}(Stage_1)} \times 100$$
* **Drop-off Volume & Rate**:
  $$\text{Users Lost}_{i} = \text{Users}(Stage_{i-1}) - \text{Users}(Stage_i)$$
  $$\text{Drop-off \%}_{i} = \left( \frac{\text{Users Lost}_i}{\text{Users}(Stage_{i-1})} \right) \times 100$$
* **Registration Window**: Boundaries $[t_{start}, t_{end}]$ defining qualifying subscriber cohorts by account signup date ($t_{start} \le t_{signup} \le t_{end}$).
* **Conversion Observation Window**: Optional duration $W$ (e.g., 7, 14, 30 days) restricting qualifying downstream events to $t_{event} \le t_{signup} + W \text{ days}$. Immature cohorts without $W$ elapsed days prior to anchor date are excluded from denominators to avoid artificial conversion deflation.
* **Deduplication**: Every user ID is deduplicated per stage; multiple session repeats do not artificially inflate stage counts.
* **Sequence Integrity**: A user who triggered `playback_start` before viewing content or opening the app is rejected from Stage 4 qualification.

---

## 3. Retention & Cohort Dynamics

### 3.1 Exact-Day Retention ($Day\ N$)
* **Definition**: Proportion of eligible cohort users who return and execute at least one event on exactly the $N$-th calendar day following their registration date ($DATE(t_{event}) = DATE(t_{signup} + N \text{ days})$).
* **Observation Window Completeness Rule**:
  Let $t_{anchor}$ be the latest date present in the platform database (e.g., `2026-10-24`).
  A user is eligible for $Day\ N$ retention evaluation **if and only if**:
  $$t_{anchor} - t_{signup} \ge N \text{ days}$$
  *Subscribers registered within the last $N-1$ days are strictly excluded from the denominator.* They are pending observation, **not churned**.
* **Mathematical Formula**:
  $$\text{Retention Rate}_{Day\ N} = \frac{|\{u \in \mathcal{U}_{eligible} : \exists e \in \mathcal{E}, DATE(t_e) = DATE(t_{signup} + N)\}|}{|\mathcal{U}_{eligible}|} \times 100$$

### 3.2 Exact-Day vs Rolling Retention
* **Exact-Day Retention**: Strict measure of habitual day-to-day engagement (e.g. Day 1, Day 7, Day 30).
* **Rolling (Unbounded) Retention**: Measures whether a user returned on Day $N$ or anytime thereafter. StreamIQ implements exact-day retention to avoid masking acute churn inflection points.

### 3.3 Cohort Retention Matrix (Heatmap)
* Users grouped into signup cohorts by week (`YYYY-Www`) or month (`YYYY-MM`).
* **Incomplete Observation Masking Rule**: Period $p$ ($p > 0$) is deemed complete only if the latest signup in the cohort has had full exposure:
  $$t_{anchor} - \max_{u \in Cohort}(t_{signup}(u)) \ge (p + 1) \times \text{period\_days} - 1$$
  Periods violating this condition are stored as `NaN` and left unshaded in the heatmap, preventing misleading degradation cliffs.

---

## 4. Rule-Based User Segmentation

Subscribers are partitioned into 4 mutually exclusive, transparent operational segments:
1. **New Users**: Account age $\le 7$ calendar days relative to observation date.
   * *Rationale*: Protects onboarding cohorts from premature churn classification before their trial window completes.
2. **Highly Active**: Total lifetime sessions $\ge 15$.
   * *Rationale*: Core power users driving platform watch-time and organic advocacy.
3. **Moderately Active**: Total lifetime sessions between $5$ and $14$ (inclusive).
   * *Rationale*: Regular recurring subscribers with stable habituation.
4. **Low Activity**: Account age $> 7$ days with $< 5$ lifetime sessions.
   * *Rationale*: High-risk accounts vulnerable to subscription cancellation; prime candidates for win-back engagement campaigns.

---

## 5. Statistical A/B Testing Framework

### 5.1 Hypotheses & Primary Metric
* Null Hypothesis ($H_0$): $p_T = p_C$ (Treatment conversion rate equals Control conversion rate).
* Alternative Hypothesis ($H_1$): $p_T \ne p_C$ (Two-sided alternative).

### 5.2 Absolute Difference & Relative Lift
* **Absolute Difference (Percentage Points)**:
  $$\Delta = p_T - p_C = \frac{x_T}{n_T} - \frac{x_C}{n_C}$$
* **Relative Lift**:
  $$\text{Lift}_{\text{rel}} = \begin{cases} \left( \frac{p_T - p_C}{p_C} \right) \times 100, & \text{if } p_C > 0 \\ \text{N/A}, & \text{if } p_C = 0 \end{cases}$$

### 5.3 Normal Approximation & Hypothesis Testing
* **Normal Approximation Assumption Check**:
  Requires $n_C p_C \ge 5$, $n_C(1 - p_C) \ge 5$, $n_T p_T \ge 5$, and $n_T(1 - p_T) \ge 5$.
* **Two-Proportion Pooled Z-Test (When Normal Assumption Holds)**:
  $$\hat{p} = \frac{x_C + x_T}{n_C + n_T}, \quad SE_{pool} = \sqrt{\hat{p}(1 - \hat{p}) \left( \frac{1}{n_C} + \frac{1}{n_T} \right)}, \quad z = \frac{\Delta}{SE_{pool}}$$
  $$p = 2 \times \left(1 - \Phi(|z|)\right)$$
* **Fisher's Exact Test Fallback (When Normal Assumption Fails)**:
  Calculates exact hypergeometric probability over the $2 \times 2$ contingency table $[[x_T, n_T - x_T], [x_C, n_C - x_C]]$, preventing severe Type I error distortion in small samples.

### 5.4 Confidence Intervals
* **Standard Wald CI (Large Samples)**:
  $$SE_{diff} = \sqrt{\frac{p_C (1 - p_C)}{n_C} + \frac{p_T (1 - p_T)}{n_T}}$$
  $$CI_{95\%} = \left[ \max(-1, \Delta - z_{0.025} SE_{diff}), \; \min(1, \Delta + z_{0.025} SE_{diff}) \right]$$
* **Agresti-Caffo Adjusted CI (Small Samples / Extreme Proportions)**:
  Applies "+1 success, +1 failure" adjustment to each group ($\tilde{n}_i = n_i + 2$, $\tilde{x}_i = x_i + 1$, $\tilde{p}_i = \tilde{x}_i / \tilde{n}_i$), guaranteeing robust coverage probability without boundary anomalies:
  $$\widetilde{SE} = \sqrt{\frac{\tilde{p}_C (1 - \tilde{p}_C)}{\tilde{n}_C} + \frac{\tilde{p}_T (1 - \tilde{p}_T)}{\tilde{n}_T}}$$
  $$CI_{95\%} = \left[ \max(-1, \tilde{\Delta} - z_{0.025} \widetilde{SE}), \; \min(1, \tilde{\Delta} + z_{0.025} \widetilde{SE}) \right]$$

### 5.5 Sample Ratio Mismatch (SRM) & Telemetry Checks
* **SRM Test**: Pearson Chi-Square goodness-of-fit comparing observed variant sizes against expected traffic proportions derived from `expected_control_share` (e.g. 50/50, or custom splits such as 10/90 canary tests):
  $$E_{\text{control}} = N_{\text{total}} \times r_{\text{ctrl}}, \quad E_{\text{treatment}} = N_{\text{total}} \times (1 - r_{\text{ctrl}})$$
  $$\chi^2 = \sum \frac{(O_i - E_i)^2}{E_i}, \quad p_{\text{SRM}} = P(\chi^2_1 \ge \chi^2)$$
  A conservative threshold of $p_{SRM} < 0.01$ indicates severe allocation bias or telemetry corruption.
* **Telemetry Integrity**: Automated audits check for duplicate variant assignments per user and unassigned outcome records.

### 5.6 Decision Engine Rules & Generalization Caveats
1. **SHIP**:
   - Statistically significant ($p < 0.05$) AND positive lift ($\Delta > 0$).
   - **Practical Significance**: Absolute lift meets or exceeds the **Minimum Practical Effect Threshold** ($\Delta \ge 0.50$ percentage points by default, configurable via `min_practical_effect_pp`). Note: This is an operational business hurdle to justify software rollout and maintenance costs, not a pre-experiment statistical power calculation.
   - Guardrail metrics healthy: Playback error delta $\le +0.50$ pp, Completion delta $\ge -3.00$ pp.
   - Telemetry clean: No SRM, zero duplicate assignments, zero unassigned outcomes.
   - **Generalization Caveats**: Shipped features must be monitored post-launch for novelty wear-off, cohort shifts, and catalog cannibalization.
2. **DO NOT SHIP**:
   - Statistically significant negative lift ($\Delta < 0$, $p < 0.05$), OR
   - Guardrail degradation (Error delta $> +0.50$ pp or Completion delta $< -3.00$ pp).
3. **CONTINUE TESTING / INVESTIGATE**:
   - Inconclusive results ($p \ge 0.05$), OR
   - Statistically significant but below practical threshold ($\Delta < 0.50$ pp), OR
   - SRM detected ($p_{SRM} < 0.01$) or assignment telemetry anomalies detected.
