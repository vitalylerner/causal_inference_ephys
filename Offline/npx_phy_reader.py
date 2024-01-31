import os
import pandas as pd
import numpy as np

def load_rasters(pth):
	"""
	builds raster for good and multi units
	
	structure: dict, keys: good, mua
	    raster['good'] and raster['mua'] are dict
	    keys: cluster numbers,
	    values: spike times
	    Assuming 624 is a good unit
	    raster['good'][624] is list of spike times of unit 624
	"""
	spike_clusters=np.squeeze(np.load(pth+'spike_clusters.npy'))
	spike_times=np.squeeze(np.load(pth+'spike_times.npy'))
	spikes=pd.DataFrame({'cluster':spike_clusters,'time':spike_times})
	#print (spikes.head())
	cluster_group=pd.read_csv(pth+'cluster_group.tsv',sep='\t')
	clusters={}
	raster={}
	for group in ['good','mua']:
		raster[group]={}
		clusters[group]=list(cluster_group[cluster_group['group']==group]['cluster_id'])
		#print (len(clusters[group]))
		for c in clusters[group]:
			raster[group][c]=spikes[spikes['cluster']==c]['time']
	return raster

if __name__=="__main__":
    from bokeh.plotting import figure, show,output_file, save
    from bokeh.layouts import column,row
    test_pth='Z:/Data/MOOG/Dazs/OpenEphys/m42c461/output/'

    raster=read_ks_phy(test_pth)
    f=[None,None]
    for igroup,group in enumerate(['good','mua']):
    	r=raster[group]
    	units=list(r.keys())
    	nunits=len(units)
    	
    	f[igroup]=figure(width=1000,height=300,x_axis_label='time (min)',y_axis_label='unit')
    	for iunit,u in enumerate(units[:10]):
    		sp=np.array(r[u])
    		sp=sp/30000/60
    		f[igroup].scatter(sp,sp*0+iunit,marker='dot',alpha=0.1)
    output_file(filename='npx_raster.html', title='raster')
    save(column(f))

