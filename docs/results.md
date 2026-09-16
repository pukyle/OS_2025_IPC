# Measured results

Produced by [`scripts/benchmark.sh`](../scripts/benchmark.sh), which runs both
mechanisms over the committed `input.txt` and reports the totals the programs
print themselves. Re-run it to reproduce the table on your own machine.

## Workload

| | |
| --- | --- |
| Messages | 100 lines of `input.txt` |
| Mean message length | 19.1 bytes |
| Message buffer | `char msgText[1024]` |
| Runs averaged | 5 |

## Environment

| | |
| --- | --- |
| Kernel | Linux 6.18 x86-64 |
| Compiler | gcc 13.3.0, `-O3 -Wall` |
| CPUs | 2 |

These numbers are specific to this machine; the ratio between the two
mechanisms is the portable part of the result, not the absolute microseconds.

## Totals over 100 messages (microseconds)

| Mechanism | send | receive |
| --- | ---: | ---: |
| Message passing (System V message queue) | 172.4 | 178.4 |
| Shared memory (System V shared memory) | **13.4** | **14.6** |
| **Ratio** | **12.9×** | **12.2×** |

Per message that is 1.72 µs versus 0.13 µs on the sending side.

Raw output of one run:

```
mechanism             send_us    recv_us
message passing         171.0      166.0
message passing         167.0      167.0
message passing         201.0      189.0
message passing         162.0      175.0
message passing         161.0      195.0
message passing         172.4      178.4   <- mean of 5 runs

shared memory            12.0       14.0
shared memory            12.0       15.0
shared memory            15.0       16.0
shared memory            14.0       15.0
shared memory            14.0       13.0
shared memory            13.4       14.6   <- mean of 5 runs
```

## A caveat that matters

`msgsnd` is called with `sizeof(message.msgText)`, so message passing transfers
the **full 1024-byte buffer** on every call. Shared memory uses `strcpy`, which
copies only up to the terminating NUL — about 20 bytes for this input. The two
mechanisms are therefore not moving the same number of bytes, and roughly 51×
more data goes through the message queue than through shared memory.

The measured gap of ~13× is nevertheless real and in the expected direction:
even at 51× the payload, message passing is only 13× slower, which says the
cost is dominated by the two system calls and the two kernel copies rather than
by the bytes. Sending `strlen(msgText) + 1` instead of the whole buffer would
isolate the mechanism from the payload and is the right way to tighten this
experiment.
