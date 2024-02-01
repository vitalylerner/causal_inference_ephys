""" 
		Vitaly Lerner 
		December 2023

Neuropixel Offline Analysis

Parsing OpenEphys files


Glossary:
 - oe OpenEphys
"""


import numpy as np

from bokeh.plotting import figure, show,output_file, save
from bokeh.layouts import column,row
from bokeh.transform import linear_cmap
from bokeh.models import  Plot, Text,ColumnDataSource
from bokeh.palettes import inferno, Category10
   # select a palette
import itertools# itertools handles the cycling 

import pandas as pd

#from abc import abstractmethod
#from functools import cache

from scipy.signal import decimate

import os
import struct
import json


class oe_tempo_parser():
	
	path_params={}
	oebin={}
	tempo_ttl=None
	
	def __init__(self,params):
		self.path_params=params
		self.load_oebin()
		self.load_ttl()
		self.load_analog()

	def load_oebin(self):
		# load open-ephys native JSON file with description of structure of the rest of the files
		# see https://open-ephys.github.io/gui-docs/User-Manual/Recording-data/Binary-format.html
		# Unfortunately, crucial information about start times is not in the JSON file, but in 
		# sync_messages.txt
		oe_path1=self.path_params['base_path']+f"""{self.path_params['subject_name']}/OpenEphys/"""
		oe_path2=f"""m{self.path_params['subject_id']}c{self.path_params['session']}r{self.path_params['rec']}/"""
		oe_path=oe_path1+oe_path2
		
		oebin_path=oe_path+'structure.oebin'
		sync_path=oe_path+'sync_messages.txt'
		
		with open(oebin_path) as f:
			self.oebin=json.load(f)
		
		nopening=len("Start Time for ")
		
		#Find the start positions of each device
		with open(sync_path) as f:
			S=f.readlines()
			
		self.oebin['starttime']=int(S[0].split(":")[1])
		dev={}
		dev['pname'] = self.oebin['continuous'][0]['source_processor_name']
		dev['pid']   = self.oebin['continuous'][0]['source_processor_id']
		dev['sname'] = self.oebin['continuous'][0]['stream_name']
		dev['sync_name']=f"""{dev['pname']} ({dev['pid']}) - {dev['sname']}"""
		dev['namechar']=len(dev['sync_name'])
		#print (dev['sync_name'])
		for l in S[1:]:
			devname=l[nopening:nopening+dev['namechar']]
			if devname==dev['sync_name']:
				s=l[nopening+dev['namechar']+3:]
				w=s.split(':')
				n0=int(w[1])
				self.oebin['continuous'][0]['starttime']=n0
		#print (self.oebin['continuous'][0].keys())
		
	def load_ttl(self):
		# ttl signal is sent from TEMPO to report its state
		# despite being a 8-bit bus, only its 8th bit is a ttl signal
		# messages are detected using inter-pulse-interval
		# table of messages is assigned to tempo_ttl table
		
		sample_rate=int(self.oebin['continuous'][0]['sample_rate'])
		device_folder=self.oebin['continuous'][0]['folder_name']
		iti_cutoff=5000#us

		# building a path from  the path parameters
		oe_path1=self.path_params['base_path']+f"""{self.path_params['subject_name']}/OpenEphys/"""
		oe_path2=f"""m{self.path_params['subject_id']}c{self.path_params['session']}r{self.path_params['rec']}/"""
		oe_path3=f"""events/{device_folder}/TTL/"""
		oe_path=oe_path1+oe_path2+oe_path3
		
		oe_vars=['full_words','sample_numbers']#['states','timestamps'](last two seem to be useless)
		oe_events={}
		for oe_var in oe_vars:
			fName=oe_path+oe_var+'.npy'
			oe_events[oe_var]=np.load(fName)
		# edges detection
		rising_e= np.array([ i for (i,e) in zip(oe_events['sample_numbers'],oe_events['full_words']) if e>0]).astype(int)
		falling_e=np.array([ i for (i,e) in zip(oe_events['sample_numbers'],oe_events['full_words']) if e==0]).astype(int)
		# inter-pulse-interval calculation
		iti=rising_e[1:]-rising_e[:-1]
		# cutoff by a minimal interval 
		msg_end=rising_e[np.where(iti>iti_cutoff)[0]]
		msg_beg=np.hstack( [[rising_e[0]],rising_e[np.where(iti>5000)[0][:-1]+1]] )
		# wrapping up the results to a table
		self.tempo_ttl=pd.DataFrame.from_dict({'start':msg_beg,'end':msg_end})
		
		
	def load_analog(self):
		#params=self.params
		if True:
			sampling_rate=int(self.oebin['continuous'][0]['sample_rate'])
			device_folder=self.oebin['continuous'][0]['folder_name']
			nchannels=self.oebin['continuous'][0]['num_channels']
			
			oe_path1=self.path_params['base_path']+f"""{self.path_params['subject_name']}/OpenEphys/"""
			oe_path2=f"""m{self.path_params['subject_id']}c{self.path_params['session']}r{self.path_params['rec']}"""
			oe_path3=f"""/continuous/{device_folder}"""
			oe_path=oe_path1+oe_path2+oe_path3
	
			fName=oe_path+'continuous.dat'
			with open(fName,'rb') as f:
				a = np.fromfile(f, dtype=np.int16)
			#print ('bb')
			A=np.reshape(a,(int(len(a)/nchannels),nchannels),order='F')
			np.savez_compressed('tmp.npz',A=A)
			
		else:
			with np.load('tmp.npz') as D:
				A=D['A']
			#print ('ee')
			
		self.Analog=A
		
	def plot_analog(self,bTrig=False,channels=[]):
		A=self.Analog
		sampling_rate=int(self.oebin['continuous'][0]['sample_rate'])
		
		#nchannels=A.shape[1]
		if len(channels)==0:
			nchannels=A.shape[1]
			channels=list(range(nchannels))
		else:
			nchannels=len(channels)
			
		#fSig=[figure(width=600,height=200,title=f"trial #{int(imsg/2)+1}") for imsg in range(0,len(self.tempo_ttl),2)]
		fSig=figure(width=600,height=600,x_axis_label="time(s)",y_axis_label='V(V)')

		nend=A.shape[0]
		skp=int(sampling_rate*0.001)
		npre=int(sampling_rate*2)
		npost=int(5*sampling_rate)
		bsl_start=0*int(sampling_rate/skp)
		bsl_end=int(bsl_start+0.2*sampling_rate/skp)
		
		offset=self.oebin['continuous'][0]['starttime']
		
		if self.path_params['choice']:
			stpmsg=2
		else:
			stpmsg=1
		for jch,ich in enumerate(channels):
			if bTrig:
				for i in range(0,len(self.tempo_ttl),stpmsg):
					stim_start=self.tempo_ttl.loc[i,'start']-offset
					stim_end  =self.tempo_ttl.loc[i,'end']-offset
					sig_start=stim_start-npre
					sig_end=stim_start+npost
					sig=A[sig_start:sig_end:skp,ich]
					
					bsl=np.mean(sig[bsl_start:bsl_end])
					tt=np.arange(len(sig))*skp/sampling_rate-npre/sampling_rate
					fSig.line(tt,sig-bsl)
			else:
				sig=A[::skp,ich]
				tt=np.arange(len(sig))*skp/sampling_rate
				fSig[jch].line(tt,sig)
				for i in range(0,len(self.tempo_ttl),stpmsg):
					s=(self.tempo_ttl.loc[i,'start']-offset)*1./sampling_rate
					e=(self.tempo_ttl.loc[i,  'end']-offset) *1./sampling_rate
					#print (s,e)
					fSig[isig].line([s,e],[sig.mean()]*2,color='red')
		#f=column(fSig)
		f=fSig
		save(f)
		

if __name__=="__main__":
	oe_events={}
	params={}
	
	params['base_path']=f'Z:/Data/MOOG/'
	params['subject_id']=42
	params['subject_species']='m'
	params['subject_name']='Dazs'
	params['session']=450
	params['choice']=False
	params['rec']=6
	
	output_file(filename='tmp.html', title="debugging")
	oetempo=oe_tempo_parser(params)
	print(oetempo.tempo_ttl)
	
	oetempo.plot_analog(True,[2])
	""" to be extracted from oenb file"""
	#params['device']='NI-DAQmx-110.PXIe-6341'
	#params['nchannels']=8
	#params['sampling rate']=40000 #sps
	
	
	#tempo_msgs=open_ttl(params)
	#A=open_analog(params)
	#slicebymsg(tempo_msgs,A)
	#print (tempo_msgs)
