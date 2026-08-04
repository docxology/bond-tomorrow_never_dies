# Results

## Disinformation propagation

Under the canonical scenario, the media campaign more than doubles the
believing population relative to a no-media baseline, ending at a {{MEDIA_BELIEF_SHARE_PCT}}%
belief share. The audience closes ranks: the echo-chamber coefficient is
{{MEDIA_ECHO_CHAMBER}} and every directly-exposed agent is amplified into
{{MEDIA_AMPLIFICATION}} believers through social spread. @fig:disinformation shows the
trajectory.

![Believing fraction over time: media campaign vs no-media baseline](../output/figures/disinformation_propagation.png){#fig:disinformation}

## Stealth-vessel detection

A {{STEALTH_RCS_REDUCTION_DB}} dB RCS reduction (from a reference target to a
stealth hull) cuts the detection range from {{STEALTH_REF_RANGE_KM}} km to
{{STEALTH_RANGE_KM}} km — a range ratio of {{STEALTH_RANGE_RATIO}}, consistent with the
fourth-root radar law. @fig:stealth shows the detection probability curves.

![Detection probability vs range: reference target and stealth hull](../output/figures/stealth_detection.png){#fig:stealth}

## GPS-denial impact

With a position dilution of precision of {{GPS_PDOP}}, a clean-sky receiver
sits at {{GPS_ERROR_CLEAN_M}} m of 1-sigma error. Under a {{GPS_JNR_DB}} dB
jammer-to-noise ratio the position error swells to {{GPS_ERROR_JAMMED_M}} m.
The jamming then cascades: {{GPS_CASCADE_FRACTION}} of the maritime
systems fail over {{GPS_CASCADE_ROUNDS}} cascade rounds. @fig:gps plots position
error against jammer standoff distance.

![Position error vs jammer standoff distance (GPS denial)](../output/figures/gps_denial.png){#fig:gps}
