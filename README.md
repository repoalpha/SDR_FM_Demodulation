# HackRF SDR stand alone FM Demodulation

The purpose of this project is to create an experimental piped Python framework for the HackRF SDR transceiver to whip up quick tests and experiments. 
Many would be aware of GNU radio and the block approach to building and testing SDR systems like HackRF. I wanted to create a simple experimental framework for HackRF that escapes the GNU radio approach and can be used in your own code and projects. Users can see what they are doing and what is being manipulated in code. Much of the code will look familar to HackRF owners as it uses sections of the command line tool already in place. In particular the use of Linux Shell 'pipes' and the HackRF_transfer command and flag options.

The hackRF_transfer shell command does not do any form of demodulation or decimation compared to for instance the RTL-SDR reciever. For example using shell pipes in the RTL-SDR case you can have a reciever playing audio as simply as copying this to a linux shell.

rtl_fm -f 92.7e6 -M wbfm -s 240000 -r 48000 - | aplay -r 48k -f S16_LE

As you can see the command invokes a Wide Band FM demodulator and signal decimation process reducing the signal to a rate which can be piped into the 'aplay' program. What we don't have in HackRf is the WBFN demodulation block and the decimation block written in C to bring the signal down to baseband audio. These two sections need to be constructed in this case using Python, and in partiuclar the scipy.signal library functions. It also gets tricky getting linux shell pipes into and out of a Python script. To do that I have used the subprocess functions to call these shell commands. This allows us to execute the hackrf_transfer command in a shell and pipe  the output using standard-out back into a python function and back out again into a shell using standard-in to 'aplay'. 

Hackrf_transfer shell program --> Python program --> aplay shell program

You will note the use of two threads and the use of queues inside the Python functions. Using threads and queues are not essential but I believe the performance is slightly improved with less skips as doing DSP in python and the process of reading in data is very CPU intensive. The 'samples' function is a byte-array iterator that reads in the raw IQ data in this form \xf2\x00\x01\x03\. The IQ data is two bytes the data is then placed into a numpy array converted to integers, reduced to values between 1- and 1 and then converted to complex numbers. Some might wonder why there is no complex number conversion. It turns out it is not needed as the process of downshifting the signal is performed does this by multiplying by complex values. But if you need to do the conversion here is a quick way in python.

x1 = x1.astype(np.int8).view(np.complex64)

Everything you do with the sampling rate is doubled becuase there are two bytes involved. A sampling rate of 1.5 Mhz is below the recommended rate of the HackRF. However the issue is using a sampling rate much above 1.5 Mhz means you will encounter under-run errors as the processing rate is 3MB/s. Most of the data manipulation is done with numpy and scipy.signal to do the digital signal processing. Much of the signal processing code was borrowed from https://witestlab.poly.edu/blog/capture-and-decode-fm-radio/ .One side 'feature' is that this simple program can be run in Python 3, something as of this date GNU radio cannot do.

## Dependencies

HackRF
aplay
numpy
scipy
