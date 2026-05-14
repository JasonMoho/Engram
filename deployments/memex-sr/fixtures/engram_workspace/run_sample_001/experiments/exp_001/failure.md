# Failure Diagnosis

The admission threshold is too coarse. It treats queue depth as a
stable load signal and does not account for burst shape, so p99 latency
regressed even though average latency improved.
