#!/usr/bin/env bash
# Reproduce the numbers in docs/results.md.
#   ./scripts/benchmark.sh [runs]
# Runs both mechanisms over input.txt and prints the per-run totals in
# microseconds, plus the mean of each. Requires the repo to be built (`make`).
set -u
RUNS="${1:-5}"
cd "$(dirname "$0")/.."
[ -x ./sender ] && [ -x ./receiver ] || { echo "run 'make' first"; exit 1; }

printf '%-18s %10s %10s\n' mechanism send_us recv_us
for MODE in 1 2; do
    name=$([ "$MODE" = 1 ] && echo "message passing" || echo "shared memory")
    st=0; rt=0
    for _ in $(seq "$RUNS"); do
        ./receiver "$MODE" >/tmp/osipc_r.log 2>&1 & rp=$!
        sleep 0.3
        ./sender "$MODE" input.txt >/tmp/osipc_s.log 2>&1
        wait $rp 2>/dev/null
        s=$(grep -o 'sending messages: [0-9.]*'   /tmp/osipc_s.log | awk '{print $NF}')
        r=$(grep -o 'receiving messages: [0-9.]*' /tmp/osipc_r.log | awk '{print $NF}')
        printf '%-18s %10.1f %10.1f\n' "$name" "$(echo "$s*1000000" | bc -l)" \
                                               "$(echo "$r*1000000" | bc -l)"
        st=$(echo "$st + $s" | bc -l); rt=$(echo "$rt + $r" | bc -l)
        ipcrm -a >/dev/null 2>&1 || true
    done
    printf '%-18s %10.1f %10.1f   <- mean of %s runs\n\n' "$name" \
        "$(echo "$st/$RUNS*1000000" | bc -l)" "$(echo "$rt/$RUNS*1000000" | bc -l)" "$RUNS"
done
