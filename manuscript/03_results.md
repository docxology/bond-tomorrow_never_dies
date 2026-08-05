# Results

## Disinformation propagation

Social spread alone converts {{MEDIA_BASELINE_SHARE_PCT}}% of the network. Adding
Carver's broadcast multiplies that by {{MEDIA_CAMPAIGN_LIFT}}x, ending at a
{{MEDIA_BELIEF_SHARE_PCT}}% belief share with an echo-chamber coefficient of
{{MEDIA_ECHO_CHAMBER}} and an amplification of {{MEDIA_AMPLIFICATION}} believers per
directly-exposed agent — the broadcast does not merely seed the belief, it
recruits the social channel that then carries it. @fig:disinformation shows
both trajectories.

![Believing fraction over time: media campaign vs no-media baseline](../output/figures/disinformation_propagation.png){#fig:disinformation}

## Narrative control

Bounded-confidence dynamics reveal *for whom* the message lands. Under a reach
of the media campaign, the audience mean is pulled {{NARRATIVE_MEDIA_CAPTURE}}%
toward the manufactured line ({{NARRATIVE_MEDIA_OPINION}}), reaching a consensus of
{{NARRATIVE_CONSENSUS}}, while the opinion variance stays at
{{NARRATIVE_POLARIZATION}} and the bimodal split of {{NARRATIVE_BIMODAL_SPLIT}} shows
the audience fragmenting into detached opinion clusters — echo chambers. The
tipping-point analysis finds that a broadcast reach of just
{{NARRATIVE_CRITICAL_REACH_PCT}}% is enough to drive the discrete belief model past a
majority. @fig:narrative shows the opinion trajectory under the campaign.

![Narrative control: bounded-confidence opinion dynamics under a media campaign](../output/figures/narrative_control.png){#fig:narrative}

## Stealth-vessel detection

A {{STEALTH_RCS_REDUCTION_DB}} dB RCS reduction (from a reference target to a
stealth hull) cuts the detection range from {{STEALTH_REF_RANGE_KM}} km to
{{STEALTH_RANGE_KM}} km — a range ratio of {{STEALTH_RANGE_RATIO}}, a
{{STEALTH_RANGE_LOSS_PCT}}% loss, and exactly the fourth-root radar law.
@fig:stealth shows the detection probability curves.

![Detection probability vs range: reference target and stealth hull](../output/figures/stealth_detection.png){#fig:stealth}

## Pulse compression

The radar claws the range back. An LFM waveform with {{WAVEFORM_BANDWIDTH_MHZ}} MHz
of bandwidth yields {{WAVEFORM_GAIN_DB}} dB of processing gain and
{{WAVEFORM_RES_M}} m of range resolution at a {{WAVEFORM_PSLR_DB}} dB sidelobe floor.
Treating that gain as coherent integration restores the stealth hull's
detection range from {{STEALTH_RANGE_KM}} km to {{WAVEFORM_RANGE_KM}} km — a
{{WAVEFORM_IMPROVEMENT_PCT}}% improvement, exactly the fourth-root of the gain.
@fig:waveform shows the compressed-pulse envelopes of the LFM chirp and the
Barker-13 code. The Barker code buys far less gain ({{WAVEFORM_BARKER_GAIN}}x
against the chirp's {{WAVEFORM_GAIN_DB}} dB) but pays for it with a much cleaner
range response: a measured {{WAVEFORM_BARKER_PSLR_DB}} dB sidelobe floor against
the chirp's {{WAVEFORM_PSLR_DB}} dB. That is the design trade — reach against the
risk that a sidelobe of a bright return masks a dim one beside it.

![Pulse compression: matched-filter range response for LFM and Barker-13](../output/figures/waveform_pulse_compression.png){#fig:waveform}

## GPS-denial impact

With a position dilution of precision of {{GPS_PDOP}}, a clean-sky receiver sits
at {{GPS_ERROR_CLEAN_M}} m of 1-sigma error; under a {{GPS_JNR_DB}} dB jammer-to-noise
ratio that swells to {{GPS_ERROR_JAMMED_M}} m. The jamming cascades:
{{GPS_CASCADE_FRACTION}} of the maritime systems fail over {{GPS_CASCADE_ROUNDS}}
cascade rounds. @fig:gps plots position error against jammer standoff
distance.

![Position error vs jammer standoff distance (GPS denial)](../output/figures/gps_denial.png){#fig:gps}

## GNSS integrity (RAIM)

RAIM sets the receiver's guardrails: with {{RAIM_DOF}} degrees of freedom and a
test-statistic threshold of {{RAIM_THRESHOLD}}, the horizontal and vertical
protection levels are {{RAIM_HPL_M}} m and {{RAIM_VPL_M}} m — comfortably inside the
maritime alert limit, so integrity is declared *available*. A
{{RAIM_BIAS_M}} m corrupted navigation measurement is caught with
{{RAIM_PD}}% probability. @fig:raim shows the detection probability ramp against
measurement bias.

![RAIM: detecting a corrupted navigation measurement](../output/figures/raim_detection.png){#fig:raim}
