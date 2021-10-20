# Board
Altium files for the test board. Note that this is the board used for testing the chip in isolation.

## Respin Changes
* Connect `TIME_SMALL_OUT` and `TIME_MAIN_OUT` to the Teensy for an event trigger
* Add larger vias to prompt `/TIME_SMALL` and `/TIME_MAIN`
* Connect on-chip DAC outputs to an analog-read pin on the Teensy (there are headers, but no on-board connections)