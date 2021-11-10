# code/testing

* `cfd.ino`: Code for the Teensy 3.6 microcontroller.
* `dac.py`: Measurement and processing on-chip DAC voltages.
* `gpib.py`: GPIB control functions for boxes in the lab.
* `scan.py`: For programming and reading from the on-chip analog scan chain.
* `signal_chains.py`: Low level functions for prompting and measuring the full signal chains on the chip.
* `test_structs.py`: Low level functions for prompting and measuring the test structures (bandgap voltage source, peak detector).
* `testing.py`: Functions incorporating control over potentially multiple boxes and the Teensy microcontroller for more nicely packaged automation for testing.
* `run_me.py`: The file for people to _locally_ modify, intended to be run when performing actual measurements. Doubles as a location for working use examples of the code.
