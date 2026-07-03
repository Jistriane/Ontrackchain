# 📊 Dashboard: Sprint 7-9 Progress Tracking

**Last Updated:** 2026-07-02 23:30 UTC  
**Next Review:** 2026-07-03 09:00 (After Kick-off)

---

## 🎯 KPI Progress Tracker

### Baseline: 87% Consolidated

```
Technical Maturity       ████████████████████░  91%  (stable)
Regulatory Readiness     ███████████████░░░░░░  78%  (target: 95%)
─────────────────────────────────────────────────────
Consolidated KPI         ████████████████░░░░░  87%  (target: 95%)
```

### Sprint 7-9 Projected Path

```
TODAY (02-Jul)   SPRINT 7     SPRINT 8     SPRINT 9     FINAL (22-Jul)
   ↓              ↓            ↓             ↓             ↓
  87%      ────→ 88%    ────→ 91%   ────→ 95%    ────→ 95%+ ✅
           Validation   1st Window  OIDC+2nd     Sign-offs
           P0 Ready     P0 Proof    Recurring    Complete

Week:       1-2          3-4         5-6
Effort:     14 person-d  12 person-d 8 person-d
Status:     🟡 Planning  🔴 Blocked  ⚪ Future
```

---

## 📋 Sprint 7: Validation P0 (02-08 July)

**🟡 Status: PENDING KICK-OFF**

### Task Breakdown

```
T7.1: AML/KYT Credentials
├─ Owner: Compliance Lead
├─ Effort: 2 days
├─ Status: 🔴 PENDING (external)
├─ Blocker: Provider response
└─ Success: ✅ API test → ✅ JSON output → ✅ Runbook

T7.2: EU Feed URL
├─ Owner: Regulatory
├─ Effort: 2 days
├─ Status: 🔴 PENDING (external)
├─ Blocker: Provider response
└─ Success: ✅ URL test → ✅ JSON output → ✅ Runbook

T7.3: OIDC Setup Local
├─ Owner: Security Lead
├─ Effort: 3 days
├─ Status: 🔴 PENDING (external)
├─ Blocker: Provider credentials
└─ Success: ✅ Provider setup → ✅ E2E pass → ✅ MFA test

T7.4: Integration Tests
├─ Owner: QA
├─ Effort: 2 days
├─ Status: ⚪ BLOCKED (depends: T7.1, T7.2, T7.3)
├─ Blocker: T7.1-T7.3 completion
└─ Success: ✅ Bundle run → ✅ All JSONs valid → ✅ Coverage ≥95%

T7.5: War Room Prep
├─ Owner: Ops Manager
├─ Effort: 3 days
├─ Status: 🟡 IN PROGRESS (scheduling)
├─ Blocker: War room availability
└─ Success: ✅ Owners confirmed → ✅ Agenda set → ✅ Manual sheet ready

T7.6: Documentation & Aceites
├─ Owner: Compliance Lead
├─ Effort: 1 day
├─ Status: ⚪ BLOCKED (depends: T7.1-T7.5)
├─ Blocker: T7.1-T7.5 completion
└─ Success: ✅ Runbooks written → ✅ E-mails signed → ✅ Docs committed
```

### Parallel Workstreams

```
CRITICAL PATH (External Dependencies)
────────────────────────────────────
T7.1 ─────────────────────────────────────→ Wait for credentials (2d)
  └─ Provider response CRITICAL BLOCKER

T7.2 ─────────────────────────────────────→ Wait for credentials (2d)
  └─ Provider response CRITICAL BLOCKER

T7.3 ─────────────────────────────────────→ Wait for credentials (3d)
  └─ Provider response CRITICAL BLOCKER

SUPPORTING PATH (Can start now)
───────────────────────────────
T7.5 ──────────────────────→ War room prep (3d)
  └─ Scheduling + manual sheet

DEPENDENT PATH (Starts when T7.1-T7.5 done)
─────────────────────────────────────────
T7.4 ─────────────────────→ Integration tests (2d)
  └─ Depends: T7.1, T7.2, T7.3

T7.6 ─────────────────────→ Docs + aceites (1d)
  └─ Depends: T7.4, T7.5
```

### Sprint 7 Deliverables Checklist

**Due Friday EOD (12 July):**

```
□ artifacts/sprint-7/
  □ compliance-provider-check.json          ← T7.1 output
  □ eu-sanctions-preflight.json             ← T7.2 output
  □ oidc-e2e-results.json                   ← T7.3 output
  □ sprint-7-validation-bundle.md           ← T7.4 output
  □ setup-aml-provider-prod.md              ← T7.6 runbook
  □ setup-eu-sanctions-feed-prod.md         ← T7.6 runbook
  □ compliance-sign-off.txt                 ← T7.6 aceite

□ docs/
  □ governance-weekly/2026-07-09-staging-serious-window-war-room.md ← T7.5 output

□ Target KPI: 88% consolidated (minimal improvement, validation proof)
```

---

## 📋 Sprint 8: First Serious Window (09-15 July)

**⚪ Status: PENDING SPRINT 7 COMPLETION**

### Task Breakdown

```
T8.1: War Room Execution
├─ Owner: Ops Manager
├─ Effort: 2 days
├─ Status: ⚪ BLOCKED (depends: Sprint 7)
├─ Prerequisites: P0 validated, owners ready
└─ Success: ✅ Preflight passed → ✅ Run complete → ✅ Packet created

T8.2: Evidence Collection
├─ Owner: QA/Tech Lead
├─ Effort: 2 days
├─ Status: ⚪ BLOCKED (depends: T8.1)
├─ Prerequisites: War room outputs
└─ Success: ✅ Screenshots captured → ✅ JSONs persisted → ✅ Logs saved

T8.3: Ownership Formalization
├─ Owner: COO
├─ Effort: 2 days
├─ Status: ⚪ BLOCKED (depends: T8.1)
├─ Prerequisites: War room validation
└─ Success: ✅ Owners confirmed → ✅ SLAs signed → ✅ Drill passed

T8.4: Retention/Recovery Test
├─ Owner: CTO
├─ Effort: 2 days
├─ Status: ⚪ BLOCKED (depends: T8.1)
├─ Prerequisites: War room validation
└─ Success: ✅ Restore successful → ✅ RTO < 30min → ✅ Signed off

T8.5: Compliance Sign-off
├─ Owner: Compliance Lead
├─ Effort: 1 day
├─ Status: ⚪ BLOCKED (depends: T8.2-T8.4)
├─ Prerequisites: Dossier complete
└─ Success: ✅ Dossier reviewed → ✅ E-mail signed

T8.6: Retrospective & Next Window
├─ Owner: Ops Manager
├─ Effort: 1 day
├─ Status: ⚪ BLOCKED (depends: T8.5)
├─ Prerequisites: All tasks complete
└─ Success: ✅ Learnings documented → ✅ Next window scheduled
```

### Sprint 8 Deliverables Checklist

**Due Friday EOD (19 July):**

```
□ artifacts/sprint-8/
  □ serious-window-stg-2026-07-09-packet.md
  □ serious-window-stg-2026-07-09-dossier.md
  □ window-logs.txt
  □ compliance-sign-off.txt
  □ cockpits-screenshots/
    □ counterparties-history.png
    □ sanctions-history.png
    □ evidence-timeline.png
    □ reports-tracked.png
    □ blocks-historical.png
    □ ros-coaf-status.png
    □ alerts-acknowledged.png

□ docs/governance-weekly/
  □ 2026-07-09-ownership-formalized.md
  □ 2026-07-09-retention-recovery-test.md
  □ 2026-07-09-retrospective.md
  □ Next window scheduled

□ Target KPI: 91% consolidated (significant leap with P0 + P2 proof)
```

---

## 📋 Sprint 9: OIDC + Recurring (16-22 July)

**⚪ Status: PENDING SPRINT 8 COMPLETION**

### Task Breakdown

```
T9.1: OIDC Homologation
├─ Owner: Security Lead
├─ Effort: 2 days
├─ Status: ⚪ BLOCKED (depends: Sprint 8)
├─ Prerequisites: P0-01 setup validated
└─ Success: ✅ Provider integrated → ✅ MFA verified → ✅ E2E passed

T9.2: Second Serious Window (Recurrence)
├─ Owner: Ops Manager
├─ Effort: 3 days
├─ Status: ⚪ BLOCKED (depends: T9.1, Sprint 8)
├─ Prerequisites: T9.1 ready, learnings applied
└─ Success: ✅ Window executed → ✅ Dossier signed → ✅ Recurrence proven

T9.3: Formal Sign-offs
├─ Owner: COO
├─ Effort: 2 days
├─ Status: ⚪ BLOCKED (depends: T9.2)
├─ Prerequisites: All windows complete
└─ Success: ✅ Consolidated document → ✅ All signatures → ✅ Published

T9.4: P3 Planning (Future Work)
├─ Owner: Tech Lead
├─ Effort: 1 day
├─ Status: ⚪ BLOCKED (depends: T9.3)
├─ Prerequisites: P0-P2 complete
└─ Success: ✅ Vault decision → ✅ PKI roadmap → ✅ Q3 planning
```

### Sprint 9 Deliverables Checklist

**Due Friday EOD (26 July):**

```
□ artifacts/sprint-9/
  □ serious-window-stg-2026-07-23-packet.md
  □ serious-window-stg-2026-07-23-dossier.md
  □ compliance-sign-off.txt
  □ oidc-homologation-report.md

□ docs/
  □ governance-weekly/2026-07-20-formal-sign-offs.md (consolidated)
  □ setup-oidc-production.md
  □ p3-roadmap-q3-2026.md

□ Target KPI: 95% consolidated ✅ GOAL REACHED
```

---

## 🚨 Critical Path & Blockers

### Week 1 (02-08 July) — External Dependency Window

```
CRITICAL BLOCKERS (Must resolve in 48 hours):

1. AML/KYT Provider Credentials
   └─ Action: Compliance Lead contacts provider TODAY
   └─ Deadline: 04 July 17:00 UTC
   └─ If missed: 1-2 day delay, extend Sprint 7

2. EU Feed URL
   └─ Action: Regulatory contacts provider TODAY
   └─ Deadline: 04 July 17:00 UTC
   └─ If missed: 1-2 day delay, extend Sprint 7

3. OIDC Provider Credentials
   └─ Action: Security Lead contacts provider TODAY
   └─ Deadline: 05 July 17:00 UTC
   └─ If missed: Keep Keycloak local, extend Sprint 7

MITIGATION:
├─ Have fallback mock providers ready in dev
├─ Daily follow-up calls if no response
├─ CTO escalation to provider C-level if needed
└─ Contingency: Extend Sprint 7 to 2 weeks if >2 blockers
```

### Dependency Graph

```
External Credentials (04-05 July)
    ↓
Local Setup & Validation (05-08 July)
    ├─ T7.1-T7.3 (AML/KYT, EU Feed, OIDC setup)
    └─ T7.5 (War room prep)
        ↓
Integration Tests (07-08 July)
    └─ T7.4
        ↓
Sprint 7 Closure (08 July EOD)
    └─ T7.6 (Docs + aceites)
        ↓
SPRINT 8 KICKOFF (09 July 09:00 AM)
    └─ War room execution
        ↓
Ownership + Retention (09-12 July)
    └─ T8.3, T8.4
        ↓
Compliance Sign-off (13 July)
    └─ T8.5
        ↓
SPRINT 8 CLOSURE (15 July EOD)
    └─ T8.6 (Retrospective + next window)
        ↓
SPRINT 9 KICKOFF (16 July 09:00 AM)
    └─ OIDC homologation
        ↓
2nd Serious Window (16-19 July)
    └─ T9.2
        ↓
Final Sign-offs (20-21 July)
    └─ T9.3
        ↓
🎉 95% GOAL REACHED (22 July)
```

---

## 📊 Daily Standup Template

**When:** 09:00 AM UTC (09:00-09:15)  
**Attendees:** All task owners + Tech Lead + Ops Manager  
**Format:** 30-sec per person

```
[TEMPLATE FOR EACH PERSON]

Name: ___________
Task(s): T7.X, T7.Y, ...
Status: 🟢 On track / 🟡 At risk / 🔴 Blocked
Yesterday: <what was done>
Today: <what will be done>
Blocker: <if any>
ETA fix: <by when>
```

**Track in:** `artifacts/sprint-7/daily-standups.md`

---

## 📞 Escalation Matrix

| Scenario | Trigger | Action | Owner |
| --- | --- | --- | --- |
| Provider no response | >12 hours | Daily follow-up | Compliance/Regulatory/Security |
| Provider delayed | >24 hours | Escalate to CFO/CTO | COO |
| War room conflict | >48 hours | Move date or split team | Ops Manager |
| Integration test fail | Any | Debug + 2-hour fix attempt | Tech Lead + QA |
| Test exceeds 2h fix | After 2 hours | CTO hands-on debug | CTO |
| Serious window delayed | >2 hours in | HOLD, post-mortem, retry next day | Ops Manager + Tech Lead |
| Stakeholder sign-off delay | >3 days | COO reminder + deadline extension | COO |

---

## 📈 Weekly Review Schedule

### Friday EOD (Every Friday)
- [ ] Verify deliverables completed
- [ ] Update KPI metrics
- [ ] Document learnings
- [ ] Plan next week

**Review meetings:**
- Sprint 7: Friday 12 July 17:00 UTC
- Sprint 8: Friday 19 July 17:00 UTC
- Sprint 9: Friday 26 July 17:00 UTC

---

## ✅ Final Checklist (Before 95% Celebration)

### Documentation
- [ ] All runbooks written (AML/KYT, EU Feed, OIDC)
- [ ] 2 serious windows completed with dossiers
- [ ] Retention/Recovery test documented with RTO/RPO
- [ ] Retrospectives captured
- [ ] P3 roadmap outlined

### Sign-offs
- [ ] Compliance Lead: P0-02, P0-03, windows, recurrence
- [ ] Security Lead: OIDC, MFA, ownership
- [ ] CTO: Retention/Recovery, RTO/RPO ✅
- [ ] COO: SLAs, owners, cadence ✅

### Metrics
- [ ] Technical: 91% (unchanged)
- [ ] Regulatory: 95% (from 78%)
- [ ] Consolidated: 95% ✅ GOAL

---

## 📁 Document Reference

| Document | Purpose | Status |
| --- | --- | --- |
| **PROJECT_ANALYSIS_AND_ROADMAP_2026_07_02.md** | Strategic analysis of all 6 sprints + gap analysis | ✅ Complete |
| **TACTICAL_ROADMAP_SPRINT_7_TO_95_PERCENT.md** | Detailed Sprint 7-9 execution plan | ✅ Complete |
| **EXECUTIVE_SUMMARY_95_PERCENT.md** | C-level summary (1 page) | ✅ Complete |
| **PRÓXIMAS_AÇÕES_IMEDIATAS.md** | This week's action items | ✅ Complete |
| **DASHBOARD (this file)** | Progress tracking & visual status | ✅ Complete |

---

**Last Updated:** 2026-07-02 23:45 UTC  
**Next Update:** 2026-07-03 17:00 (After Kick-off) or immediately if blockers arise  
**Owner:** Tech Lead / Ops Manager

---

## 🎯 ONE-PAGE SUMMARY FOR STAKEHOLDERS

```
╔════════════════════════════════════════════════════════════════════╗
║          ONTRACKCHAIN 95% MATURITY SPRINT 7-9 ROLLOUT             ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║  Current State:      87% Consolidated KPI (June 2026)            ║
║  Target State:       95% Consolidated KPI (July 22, 2026)        ║
║                                                                    ║
║  Timeline:           9 weeks (3 sprints)                          ║
║  Effort:             34 person-days (~€15-20K)                    ║
║  Critical Blockers:  3 external provider credentials (Week 1)     ║
║                                                                    ║
║  KPI Path:           87% ─→ 88% ─→ 91% ─→ 95% ✅                 ║
║                      S7    S8    S9                               ║
║                                                                    ║
║  NEXT ACTION:        Kick-off Sprint 7 Tomorrow (09:00 AM)        ║
║                      Contact 3 providers TODAY                    ║
║                      Confirm task owners                          ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

✅ **Dashboard Ready. Awaiting Kick-off & Provider Responses.**
