# Cash-in-hand and other branch aggregates are computed from
# `journal.GeneralJournal` (CA / DE / WI / LO / IN / INC / EXP ledgers) — see
# `report.api`. The previous `CIHCalculation` snapshot table was removed in
# favour of querying the journal directly, which is the canonical source of
# truth.
