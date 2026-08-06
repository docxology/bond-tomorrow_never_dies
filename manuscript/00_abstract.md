# Abstract

**{{CARVER_IDENTITY}}** (*{{CARVER_SUBTITLE}}*).

CARVER is a deterministic mission-software package that turns the media-warfare
playbook of Elliot Carver into {{CARVER_OBJECTIVES}} quantitative, reproducible
analyses, paired as attack and counter across media, radar, and navigation. A
disinformation model simulates how a broadcast campaign converts a social
network to a manufactured belief — {{MEDIA_BELIEF_SHARE_PCT}}% by campaign end,
{{MEDIA_CAMPAIGN_LIFT}}x the no-media baseline — and
a bounded-confidence narrative model shows how a *selective* broadcast pulls
the audience mean {{NARRATIVE_MEDIA_CAPTURE}}% toward the manufactured line while
fragmenting it into echo chambers (bimodal split {{NARRATIVE_BIMODAL_SPLIT}}; the
tipping point is a reach of just {{NARRATIVE_CRITICAL_REACH_PCT}}%). A radar model
finds that a {{STEALTH_RCS_REDUCTION_DB}} dB low-RCS reduction drops a stealth
hull's detection range to {{STEALTH_RANGE_KM}} km ({{STEALTH_SWERLING1_KM}} km
for a Rayleigh fluctuating hull), but pulse compression ({{WAVEFORM_GAIN_DB}} dB,
{{WAVEFORM_RES_M}} m resolution, {{WAVEFORM_PSLR_DB}} dB range sidelobes) restores
it to {{WAVEFORM_RANGE_KM}} km —
{{WAVEFORM_IMPROVEMENT_PCT}}% beyond an unmodulated pulse of the same range
resolution; the Barker-13 code reaches that same {{WAVEFORM_BARKER_RANGE_KM}} km
at the cost of {{WAVEFORM_BARKER_RES_M}} m range resolution in exchange for a
{{WAVEFORM_BARKER_PSLR_DB}} dB sidelobe floor. A GPS-denial model drives effective C/N0 from
{{GPS_CNO_CLEAN_DBHZ}} to {{GPS_CNO_JAMMED_DBHZ}} dB-Hz at
{{GPS_JAMMER_STANDOFF_KM}} km — below the {{GPS_LOCK_THRESHOLD_DBHZ}} dB-Hz
carrier-lock threshold, so the modelled outcome is loss of lock rather than
the {{GPS_ERROR_JAMMED_M}} m the range-error formula extrapolates past its
validity (clean-sky: {{GPS_ERROR_CLEAN_M}} m) — and fails
{{GPS_CASCADE_FRACTION}} of the maritime dependency network; its RAIM guardian
bounds the damage (HPL {{RAIM_HPL_M}} m) but catches a {{RAIM_BIAS_M}} m corrupted
navigation measurement with only {{RAIM_PD}}% probability on the worst-placed
satellite ({{RAIM_PD_BEST}}% on the best-placed) — the parity projection sees
only part of any single-satellite fault.

Keywords: {{CARVER_KEYWORDS}}.
