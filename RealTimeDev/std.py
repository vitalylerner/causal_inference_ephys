import numpy as np
from matplotlib.pyplot import*
import pandas

F=30000
C=384
ms=10**-3
nummax=5
contactsdistance=5
numtraces=5
secbefore=2
secafter=3
basestart=1000 #in ms before stimuli
baseend=500 #ms before stimuli
steadystart=500 #ms after stimuli
steadyend=1500  #ms after stimuli
numtrials=5
byte=4
#import data files

stimuli=pandas.read_csv(r'C:\Users\DeAngelis Lab\Desktop\Jessie\Trials.csv')
stim=stimuli[stimuli['rec']==1]
fstim=pandas.Series.to_numpy(stim['ap in stitch']/2)
a=[np.fromfile('continuous.dat',dtype=np.int32,count=int(C*F*(secbefore+secafter)),offset=int(C*fstim[i]*byte-C*F*secbefore*byte))for i in range(len(fstim))]
b=[np.reshape(a,(int(len(a)/C),C)).T for a in a]


base=np.array([np.std(b[a][:,int(F*secbefore-F*ms*basestart):int(F*secbefore-F*ms*baseend)],axis=1)for a in range(len(b))])
steady=np.array([np.std(b[a][:,int(F*2+F*ms*steadystart):int(F*2+F*ms*steadyend)],axis=1)for a in range(len(b))])
diff=(np.mean(steady[0:numtrials],axis=0)-np.mean(base[0:numtrials],axis=0))/np.mean(base[0:numtrials],axis=0)
diffg=np.stack((diff[0::2],diff[1::2]),axis=1)

sortindexdiff=np.argsort(abs(diff))[::-1]

x=0
y=np.zeros((1,5))
for i in range(len(diff)):
    if np.all(abs(y-sortindexdiff[i])>=contactsdistance):
        y[0,x]=sortindexdiff[i]
        x=x+1
    if x==nummax:
        break

axd=matplotlib.pyplot.figure(layout='constrained').subplot_mosaic(
    """
    ABCDH
    AEFGI
    """
)
axd["B"].bar(range(np.shape(steady)[1]), diff)  
  
z=axd["A"].pcolormesh(diffg,cmap='turbo',vmin=-0.1,vmax=0.1)     
matplotlib.pyplot.colorbar(z)

c=range(-F*secbefore,F*secafter)

for i in range(numtraces):
    axd["C"].plot(c,b[i][int(y[0,0])],alpha=0.1)   

for i in range(numtraces):
    axd["D"].plot(c,b[i][int(y[0,1])],alpha=0.1)

for i in range(numtraces):
    axd["E"].plot(c,b[i][int(y[0,2])],alpha=0.1)

for i in range(numtraces):
    axd["F"].plot(c,b[i][int(y[0,3])],alpha=0.1)

for i in range(numtraces):
    axd["G"].plot(c,b[i][int(y[0,4])],alpha=0.1)


d=[b[int(y[0,2]),int(fstim[i]-F*secbefore):int(fstim[i]+F*secafter)]for i in range(numtraces)]
all_voltages=np.concatenate(d)
w=int(np.shape(d)[1]/(F*ms*50))

axd["H"].hist2d([c]*numtraces,all_voltages,bins=(w,100),cmap='turbo')
matplotlib.pyplot.show()