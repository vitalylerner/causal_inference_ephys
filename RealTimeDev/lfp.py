import numpy as np
from matplotlib.pyplot import*
import pandas

#initialize variables
F=2500
C=384
secbefore=2
secafter=3
sep=10

#load files
a=np.fromfile("C:\\Users\\DeAngelis Lab\\Desktop\\Jessie\\LFP.dat",dtype=np.int16)
b=np.reshape(a,(int(len(a)/C),C)).T
stimuli=pandas.read_csv(r'C:\Users\DeAngelis Lab\Desktop\Jessie\Trials.csv')
stim=stimuli[stimuli['rec']==1]
fstim=pandas.Series.to_numpy(stim['lfp in stitch'])
pos=pandas.DataFrame.to_numpy(pandas.read_csv("C:\\Users\\DeAngelis Lab\\Desktop\\Jessie\\m42c539r1_trial_conditions.csv"))

#sort stimuli by position
_,unique=np.unique(pos,axis=0,return_index=True)
unique1=np.sort(unique)
pos1=[]
for i in unique1:
     mask=np.where((pos==pos[i]).all(axis=1))
     pos1.append(mask)

#create plotting x axis so stimuli occurs at 0
c=range(-F*secbefore,F*secafter)

#take average trace across all stimuli in same position, normalize with mean across all contacts, contact mean and std, and plot with label of position
r=np.zeros((C,len(c)))
for i in range(len(pos1)):
        for j in range(C):
                r[j,:]=np.mean([b[j,int(fstim[i]-F*secbefore):int(fstim[i]+F*secafter)]for i in pos1[i][0]],axis=0)
        q=np.mean(r,axis=0)
        r=r-q
        matplotlib.pyplot.figure(i)
        r_adjusted=r-q
        r_normalized=np.zeros(r_adjusted.shape)
        for j in range(C):
               row_mean=np.mean(r_adjusted[j,:])
               row_std=np.std(r_adjusted[j,:])
               r_normalized[j,:]= (r_adjusted[j,:]-row_mean) / row_std if row_std>0 else r_adjusted[j,:]
               matplotlib.pyplot.plot(c,r[j,:]+sep*j,alpha=0.3,color='k')
               matplotlib.pyplot.xlabel(str(pos[pos1[i][0][0]]))

#take average trace across all stimuli, normalize as above, and plot
y=np.zeros((C,len(c)))
fig,ax=matplotlib.pyplot.subplots()
for j in range(C):
        y[j,:]=np.mean([b[j,int(fstim[i]-F*secbefore):int(fstim[i]+F*secafter)]for i in range(len(fstim))],axis=0)
z=np.mean(y,axis=0)
y_adjusted=y-z
y_normalized=np.zeros(y_adjusted.shape)
for j in range(C):  
        row_mean=np.mean(y_adjusted[j,:])
        row_std=np.std(y_adjusted[j,:])
        y_normalized[j,:]= (y_adjusted[j,:]-row_mean) / row_std if row_std>0 else y_adjusted[j,:]
        ax.plot(c,y_normalized[j,:]+sep*j,alpha=0.3,color='k')
matplotlib.pyplot.show()

