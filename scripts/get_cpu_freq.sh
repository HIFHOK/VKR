#!/bin/bash
FREQ_MHZ=$(grep -m1 '^cpu MHz' /proc/cpuinfo 2>/dev/null | awk '{print $4}')

if [ -n "$FREQ_MHZ" ] && [ "$FREQ_MHZ" != "0" ]; then
    FREQ_GHZ=$(echo "scale=2; $FREQ_MHZ / 1000" | bc)
    echo "$FREQ_GHZ"
else
    echo "3.5"
fi
