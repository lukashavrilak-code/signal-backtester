# Methodology

> Draft. Sections marked *(to do)* are completed in later milestones.

## 1. Question and design

Would a standard disproportionality method have flagged known drug safety signals before
regulators acted, and by how many months? This is a **retrospective backtest**: for six
historical drug–event pairs ("case studies") we recompute the statistics at every
quarter-end, using only the FAERS reports that existed at that date, and compare the first
quarter that meets the signal criteria with the date of the first regulatory action.

## 2. Data *(to do – milestone 2)*

FDA Adverse Event Reporting System (FAERS) Quarterly Data Extract files, 2004 Q1 to the
latest quarter (legacy AERS format until 2012 Q3, FAERS format from 2012 Q4).
The openFDA `drug/label` endpoint provides the current US labels.

Why not the openFDA `drug/event` count endpoint: a search such as
`generic_name:X AND drugcharacterization:1` matches a report when *any* drug in it is
suspect, not necessarily drug X. In a test on 2026-10-31, montelukast had 121,071 reports
without the filter and 120,991 with it, while samples of reports showed montelukast itself
was the suspect drug in only 1–16% of them.

## 3. Case and exposure definitions

- **Unit of analysis:** a FAERS case (CASEID), deduplicated as of each cutoff.
- **Exposure:** the case lists a study substance with role `PS` (primary suspect) or
  `SS` (secondary suspect). Concomitant (`C`) and interacting (`I`) roles do not count.
- **Event:** the case lists at least one MedDRA Preferred Term (PT) of the study's event group.
- **Background:** all other cases in FAERS.

## 4. Disproportionality statistics

|                    | Event | No event |
|--------------------|-------|----------|
| Drug (PS/SS)       | a     | b        |
| All other reports  | c     | d        |

- **PRR** = [a / (a+b)] / [c / (c+d)], SE(ln PRR) = √(1/a − 1/(a+b) + 1/c − 1/(c+d))
- **ROR** = (a·d) / (b·c), SE(ln ROR) = √(1/a + 1/b + 1/c + 1/d)
- **95% CI** = exp(ln(estimate) ± 1.96 · SE)
- **χ² with Yates correction** = N (|ad − bc| − N/2)² / [(a+b)(c+d)(a+c)(b+d)];
  the uncorrected χ² is reported as well.
- If any cell is 0 the metrics are not computed ("insufficient data"); no +0.5 correction is used.

**Signal criteria** (thresholds in `config/settings.yaml`):

- *Evans criteria* (Evans, Waller & Davis, *Pharmacoepidemiol Drug Saf* 2001;10:483–486):
  PRR ≥ 2, χ² ≥ 4 and a ≥ 3. We use the Yates-corrected χ². This is our own conservative
  choice (web sources disagree on whether Evans et al. used the correction); the uncorrected χ²
  is reported as a sensitivity result.
- *ROR criterion* (EudraVigilance practice): lower bound of the 95% CI of the ROR > 1 and a ≥ 3.

Worked example (also a unit test): a = 10, b = 90, c = 40, d = 860 gives PRR 2.25
(95% CI 1.16–4.36), ROR 2.39 (1.16–4.94), χ² 4.74 with Yates correction (5.85 without),
so both criteria are met.

## 5. Time slicing and lead time *(to do – milestone 3)*

## 6. Case study definitions

Each study is defined in `config/studies/<study_id>.yaml`: substances, first US approval
dates, MedDRA PT groups, regulatory milestones with sources and verification dates, and
study-specific caveats.

**Primary regulatory date.** The earliest FDA or EMA action that is specific to the
drug–event pair (Drug Safety Communication, early communication, PRAC recommendation).
The date used is the decision date printed in the official source: for a PRAC meeting its
last day, for an FDA communication the date printed on it. When the document was published
later, that date is recorded as `published_on`. Lead time is always computed from the
decision date. This is the conservative choice, because an earlier date gives a shorter lead
time. Label changes initiated by the manufacturer and later actions are shown as secondary
markers.

**How the dates are verified.** Every primary action carries a verbatim `quote` from its
source that shows the date, and an `archive_url` (a Wayback Machine copy), so the source
stays checkable when the agency moves the page. The command `backtester check-sources`
downloads each source (HTML or PDF) and confirms that the quote appears in it. The author
reads every source once and records the date of that check as `verified_on`; the command
then confirms on every run that the cited text is still there.

**First US approval dates** come from Drugs@FDA (openFDA `drug/drugsfda`): the earliest
approval of an original NDA that contains the substance. `check-sources` compares the
dates in the study files with the database.

**Fluoroquinolone class.** The class follows the "List of FDA-approved Systemic
Fluoroquinolones" in the FDA Drug Safety Communication of 20 December 2018
(ciprofloxacin, delafloxacin, gemifloxacin, levofloxacin, moxifloxacin, ofloxacin), because
the data are US FAERS reports. Norfloxacin, which is in the scope of the EU recommendation,
is not in that list and is not included.

**Headline rule** (pre-registered in `config/settings.yaml`, block `headline`): the number
of studies in which the Evans criteria were met for the whole drug group and the primary
event group before the primary action; the median lead time uses only studies that are not
left-censored, and is replaced by the individual values when fewer than three such studies
remain. Left-censored studies are counted separately.

PT groups are our own documented groupings (MedDRA SMQs are licensed and not used).
They are locked (`definition_status: frozen`) before any results are computed.

## 7. Screening and label check *(to do – milestone 5)*

## 8. AI-drafted assessments *(to do – milestone 6)*

## 9. Limitations *(to do – completed in milestone 7)*

- Spontaneous reports: no denominator, no proof of causality, under-reporting.
- Stimulated (notoriety) and litigation-driven reporting after warnings and publications.
- Confounding by indication, masking, residual duplicates.
- Hindsight: the case studies and PT groups were chosen knowing the answer.

---

MedDRA® is a registered trademark of ICH. Research and education only; not medical advice
and not a regulatory signal.
