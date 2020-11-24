#--------------------------------------INPUT INFORMATION-------------------------
###################################################################################


experiment_name = '24_November_2020'
path_to_file = 'contraction.csv'
duration = 110 # mins


substances = {
			'KCL': (30, 37), 
			'Carbachol': (56, 62)
			 }


#################################################################################


#------------------------------------- GENERAL SETTINGS--------------------------
vals = list(substances.values())
vals.sort(key=lambda x: x[0])
substances['control'] = (0, vals[0][0])
print(substances)
# Create directory for storing the results
import os
if not os.path.exists(experiment_name):
	os.mkdir(experiment_name)

	
#---------------------------- ANALYSIS PART-----------------------------------

import numpy as np
import matplotlib.pyplot as plt
from itertools import cycle
import peakutils
from scipy.signal import find_peaks, peak_widths
from scipy.integrate import simps
from BaselineRemoval import BaselineRemoval
plt.style.use('dark_background')

color=iter(cycle(plt.cm.rainbow(np.linspace(0,1,len(substances)))))

# loading the data
contrac = np.loadtxt(path_to_file, delimiter=',')

# Determine time vector
Δt = duration / len(contrac)
time = np.arange(0, duration, Δt)

# Find baseline and remove it from contraction trace
base = peakutils.baseline(contrac, 5)
contrac_aligned = contrac - base

# General view after alignment
fig, axs = plt.subplots(2, 1, figsize=(20, 8), dpi=130)

axs[0].plot(time, contrac)
for substance, times in substances.items():
	axs[0].axvspan(*times, facecolor=next(color), edgecolor='None', alpha=0.5, label=substance)
	
axs[0].legend(title='Application')
axs[0].set_title('Before the alignment procedure')

axs[1].plot(time, contrac_aligned)
for substance, times in substances.items():
	axs[1].axvspan(*times, facecolor=next(color), edgecolor='None', alpha=0.5, label=substance)

axs[1].legend(title='Application')
axs[1].set_title('After the alignment procedure')

axs[1].set(xlabel = 'time [min]')

fig.savefig(experiment_name + '/General_traces.pdf')

# Finding variables required for calculating amplitude, areas under peaks, half-widths

aligned = BaselineRemoval(contrac_aligned)
zhang = aligned.ZhangFit()

peaks, peak_values = find_peaks(zhang, height=0.5, distance=200)
widths, widths_heights, left, right = peak_widths(zhang, peaks, rel_height=0.98)
left = left.astype(int)
right = right.astype(int)
left_full = left * Δt
right_full = right * Δt
half_widths, widths_heights_half, left_half, right_half  = peak_widths(zhang, peaks, rel_height=0.5)
half_widths *= Δt

fig, axs = plt.subplots(2, 1, figsize=(20, 8), dpi=130)
axs[0].plot(time, contrac_aligned)
axs[0].plot(time[peaks], contrac_aligned[peaks], 'x')

axs[1].plot(time, contrac_aligned)
axs[1].hlines(widths_heights_half, left_half*Δt, right_half*Δt, color='red')
axs[1].set(xlabel='time [min]')
axs[1].set_xlim([0, 30])

fig.savefig(experiment_name + '/Peaks_half_widths_amplitude.pdf')
			
# plotting limits of integratiobn
fig, axs = plt.subplots(len(substances), 1, 
						figsize=(20, 4*len(substances)), dpi=130);

for ax, substance, times in zip(axs, list(substances.keys()), list(substances.values())): 
	ax.plot(time, contrac_aligned, label=substance)
	ax.legend()
	ax.hlines(widths_heights, left_full, right_full, color='red')
	ax.set_xlim(list(times))

axs[-1].set(xlabel='time [min]')

fig.savefig(experiment_name + '/Limits_of_integration.pdf')

# find areas and amplitudes
amps = []
areas = []
for idx, peak in enumerate(peaks):
    neibs = np.diff( contrac_aligned[peak-300:peak+300] ) 
    amp = contrac_aligned[peak] 
    amps.append(amp)
    area = simps(
				contrac_aligned[np.where( (time > left_full[idx]) & (time < right_full[idx]))],
                time[np.where( (time > left_full[idx]) & (time < right_full[idx]))] * 60
				) 
    areas.append(area)
	
# Separating amplitudes, areas, half_widths
amplitudes_sep = {key: [] for key in substances.keys()} 
areas_sep = {key: [] for key in substances.keys()} 
half_widths_sep = {key: [] for key in substances.keys()} 

for key, times in substances.items():
	amplitudes_sep[key] = amps[np.argmax(time[peaks] > times[0]) : np.argmax(time[peaks] > times[1])]
	areas_sep[key] = areas[np.argmax(time[peaks] > times[0]) : np.argmax(time[peaks] > times[1])]
	half_widths_sep[key] = half_widths[np.argmax(time[peaks] > times[0]) : np.argmax(time[peaks] > times[1])]
	
#------------------------------ PLOTTING ERRORBARS----------------------------------
# calculating means and standart errors
labels = [key for key in substances.keys()]
x = np.arange(len(labels))

for d in [amplitudes_sep, areas_sep, half_widths_sep]:
	for k, v in d.items():
		d[k] = (np.mean(v), np.std(v)/np.sqrt(len(v)))
	
fig, axs = plt.subplots(1, 3, dpi=150, figsize=(16, 4))
for idx, d in enumerate([amplitudes_sep, areas_sep, half_widths_sep]):
	y = [ d[ labels[i] ][0] for i in range(len(labels))]
	error = [ d[ labels[i] ][1] for i in range(len(labels))] 
	axs[idx].bar(x, y, yerr=error, align='center', 
				 alpha=0.8, ecolor='red', capsize=10, facecolor='silver')
	axs[idx].set_xticks(x)
	axs[idx].set_xticklabels(labels)
	
axs[0].set_title('Contraction amplitude, g')
axs[2].set_title('Contraction half_widths, min')
axs[1].set_title('Contraction areas, $g \cdot s$')

fig.savefig(experiment_name + '/Errorbars.pdf')
	
	
	
	
	