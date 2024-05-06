# -*- coding: utf-8 -*-
"""
Created on Thu Mar 14 19:04:52 2024

@author: Vitaly
"""
import numpy as np

from bokeh.plotting import  figure,show,save,output_file
from bokeh.layouts import row,column

from scipy.fft import fft, fftfreq
fName='SAMPLE/continuous.dat'
chnum=384
srate=30000
N=int(srate*30)
A = np.fromfile(fName, count=N*chnum, dtype=np.int16)

A=np.reshape(A,(chnum,N),order='F')

a1=np.squeeze(A[1,:])
a2=np.squeeze(A[140,:])
t=np.arange(N)/(srate*1.)

A1=fft(a1)
A2=fft(a2)
f = fftfreq(N, 1/srate)[:N//2]

ndisp=int(0.005*srate)
fSignal=figure(width=600,height=300,y_axis_label='AP-signal',x_axis_label='time[ms]')
fSignal.line(t[:ndisp]*1000,a1[:ndisp])
fSignal.line(t[:ndisp]*1000,a2[:ndisp],color='red')

fFourier=figure(width=600,height=300,
                y_axis_label='Power (dB)',
                x_axis_label='f(Hz)')
fFourier.line(f,np.log(2.0/N*np.abs(A1[0:N//2])),alpha=0.5)
fFourier.line(f,np.log(2.0/N*np.abs(A2[0:N//2])),color='red',alpha=0.5)

figure=column([fSignal,fFourier])
output_file('test.html')
save(figure)
