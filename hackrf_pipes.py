import subprocess 
import numpy as np  
import scipy.signal as signal
from threading import Thread
from queue import Queue


F_station = int(92.7e6) 
F_offset = 250000
Fc = F_station - F_offset # Capture center frequency  
Fs = 1500000 # define sampling rate, this is close to maximum without incuring underruns

# 1. start hackrf feeding raw data samples into a stdout pipe from the linux shell	
hackout = subprocess.Popen(['hackrf_transfer', '-r', '/dev/stdout', '-f', '{}'.format(Fc), '-s', '{}'.format(Fs),"l", "40", '-a','1'], stdout=subprocess.PIPE)


aplay = subprocess.Popen([ 'aplay', '-r', '48000', '-f', 'S16_LE'], stdin=subprocess.PIPE) # audio player 16bit samples at 48k


def samples(out_q):

	for iq_samples in iter(lambda: bytearray(hackout.stdout.read(10 * 8192)), b''): #read in data from the stdout pipe from hackrf as a byte array

		out_q.put(iq_samples) # put the data in a queue

def demodulator(in_q):
		
	while True:
		
		x1 = in_q.get() # data from hackrf read in as raw samples from queue like this \xf2\x00\x01\x03\
		x1 = np.array(x1, dtype=np.int8) # create a 1D (list) numpy array with signed integers like this -2  4  7
		x1 = (x1)/127.5 # puts data betweem -1 and 1

		fc1 = np.exp(-1.0j*2.0*np.pi* F_offset/Fs*np.arange(len(x1))) # freq downshift also does the complex number conversion
	
		x2 = x1 * fc1
		
		# An FM broadcast signal has  a bandwidth of 200 kHz but 120000 seems to give the best fidelity 
		f_bw = 120000

		dec_rate = int(Fs / f_bw) # decimation rate
		x4 = signal.decimate(x2, dec_rate)  
		# Calculate the new sampling rate
		Fs_y = 240000 # sampling rate set at twice the bandwidth

		### Polar discriminator
		y5 = x4[1:] * np.conj(x4[:-1])  
		x5 = np.angle(y5) 

		# The de-emphasis filter
		# Given a signal 'x5' (in a numpy array) with sampling rate Fs_y
		d = Fs_y * 75e-6   # Calculate the # of samples to hit the -3dB point  
		x = np.exp(-1/d)   # Calculate the decay between each sample  
		b = [1-x]          # Create the filter coefficients  
		a = [1,-x]  
		x6 = signal.lfilter(b,a,x5) 

		# Find a decimation rate to achieve audio sampling rate between 44-48 kHz
		audio_freq = 48000.0  
		dec_audio = int(Fs_y/audio_freq) 
		Fs_audio = Fs_y / dec_audio 

		x7 = signal.decimate(x6, dec_audio)

		x7 *= 10000 / np.max(np.abs(x7)) # Scale audio to adjust volume
		
		#x7.astype("int16").tofile("wbfm-mono.raw")  
		aplay.stdin.write((x7).astype('int16'))
		

if __name__ == '__main__':
	q = Queue()
	t1 = Thread(target=samples, args=(q,))
	t2 = Thread(target = demodulator, args=(q,))
	t1.start()
	t2.start()
	

