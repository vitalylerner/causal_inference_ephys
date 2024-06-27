from ephys_raster import vision_spikes
import os
plot_su=False
plot_mu=True

m={}
m['subject']=42
m['session']=551
m['recording']=2
m['sampling_rate']=30000
m['pre']=1.5
m['post']=3.5

p={}

p['kilosort']=f'Z:/DATA/MOOG/Dazs/OpenEphys/m{m["subject"]}c{m["session"]}/Record Node 139/experiment2/kilosort4'
p['tempo']='Z:/Data/MOOG/Dazs/TEMPO'
p['recording']=f'Z:/Data/MOOG/DAZS/OpenEphys/m{m["subject"]}c{m["session"]}/Record Node 139/experiment2'
p['output']=f'Z:/Data/MOOG/DAZS/OpenEphys/m{m["subject"]}c{m["session"]}/Spikes'
p['figures']=f'Z:/Data/MOOG/DAZS/Results/m{m["subject"]}c{m["session"]}'

#p['rec1dat']=f'C:/Sorting/m42c539/rec1AP.dat'

p['figures_su']=p['figures']+'/SU'
p['figures_mu']=p['figures']+'/MU'

for fld in ['output','figures','figures_su','figures_mu']:

    if not os.path.exists(p[fld]):
        os.makedirs(p[fld])
        print("The new directory is created! " + p[fld])
        
m['recording']=2
vs0=vision_spikes(m,p)        
su=vs0.singleunit_list()
mu=vs0.multiunit_list()

print (f"""m{m["subject"]}c{m["session"]}""")
print (f"{len(su)} single units")
print (f"{len(mu)} multiunits")
