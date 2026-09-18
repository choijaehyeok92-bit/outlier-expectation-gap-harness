# Provider calibration smoke tests

Run:
    python harness.py selftest

The command verifies:
1. self-reported confidence / prose unknown count do not move modern rubric scores;
2. a single model's wide Bull/Bear range raises a review flag but does not haircut the score;
3. EV DCF arithmetic uses the locked valuation policy.
