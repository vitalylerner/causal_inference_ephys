# -*- coding: utf-8 -*-
"""
Created on Thu May 16 11:36:17 2024

@author: Vitaly Lerner

python 3.11.7
numpy scipy pandas bokeh selenium xlrd
for exporting svg:
conda install -c conda-forge firefox geckodriver


"""


"""
TODO: unify and structure directories, 
currently it's a mess. One place for all, at least
ephys. 

TODO: unite ci_tempo, moog_geometry and npx_tempo
to one repository
There are common funcitons, make sure to not duplicate them
"""

import numpy as np
import os

from ci_functions.ci_graphics import ci_graphics
from ci_functions.ci_analysis import ci_analysis,context

from bokeh.plotting import figure, output_file, save, show
from bokeh.layouts import column,row
from bokeh.io import export_svgs
from bokeh.models import Label

from selenium import webdriver

import socket
MACHINE=socket.gethostname()
MACHINE_OFFICE='Beaujolais'
MACHINE_TEMPOWAVE='TEMPO1WAVE'

Dazs=context()
Dazs.name="Dazs"
Dazs.VIEW_DIST=36.3
Dazs.EYE_Z    =3.5
Dazs.IO       =3.2
cia=ci_analysis(Dazs)
cig=ci_graphics()

    
def figure_vert_disp():
    from bokeh.models import Range1d

    
    g_params=ci_graphics.g_params_default
    flt=cia.defaultfilter()
    flt &= cia.rowfilter('task',2)
    
    VD=cia.vert_disp_psychometric(flt)
    fVD=cig.plot_psychometric_curves(VD)
    F=fVD
    return F

def figure_dual_full(flt)->column:

    
    Header=cia.header(flt)
    MP=cia.motion_psychometric(flt)
    DP=cia.depth_psychometric(flt)
    RMP=cia.retinal_motion_psychometric(flt)
    WR = cia.D[flt][['obj_amp','ret_amp']]
    XY=  cia.D[flt][['start_x','y']]

    f_motion    = cig.plot_psychometric_curves(MP)
    f_ret_motion= cig.plot_psychometric_curves(RMP)
    f_depth     = cig.plot_psychometric_curves(DP)
    
    f_world_retinal  = cig.scatter(WR)
    f_xy             = cig.scatter(XY)
    psy=column([f_motion,f_ret_motion,f_depth])
    
    xy=row([f_world_retinal,f_xy])

    fSummary=cig.header(Header)
    fCond=figure_dual_conditioned(flt,ct=0.3,depth=True,motion=False,retinal=False)
 
    F=column([fSummary,fCond,psy,xy])
    return F




def figure_dual_conditioned(flt,ct:float=0.3,depth:bool=True,motion:bool=True,retinal:bool=False)->column:


    F=[]
    if motion:
        CondMP =cia.conditional_motion(flt,confidence_threshold=ct)
        fCondMP=cig.plot_psychometric_curves(CondMP)
        F+=[fCondMP]
    if retinal:
        CondMPR=cia.conditional_motion_retinal(flt,confidence_threshold=ct)
        fCondMPR=cig.plot_psychometric_curves(CondMPR)
        F+=[fCondMPR]
    if depth:
        CondD  =cia.conditional_depth(flt,confidence_threshold=ct)
        fCondD = cig.plot_psychometric_curves(CondD)
        F+= [fCondD]
  
    F=column(F)

    return F



def output(F,export_flags,name):
    if export_flags['svg']:
        export_flags['html']=True
    if export_flags['browser']:
        export_flags['html']=True
    if export_flags['html']:
        figpath=f"Figures/{name}.html"
        output_file(figpath,title=name)
        save(F)
    
    
    if export_flags['png']:
        pass
    
    if export_flags['justshow']:
        figpath=f"Figures/{name}.html"
        #figpath=os.path.abspath(figpath)
        output_file(figpath,title=name)
        show(F)
    if export_flags['browser']:
        
       
        figpath=os.path.abspath(figpath)
        
        if MACHINE==MACHINE_OFFICE:
            driver=webdriver.Firefox()
            driver.set_window_position(10, 10)
        elif MACHINE==MACHINE_TEMPOWAVE:
            driver=webdriver.Chrome()
            driver.set_window_position(-1400, 10)
        else:
            driver=webdriver.Firefox()
            driver.set_window_position(10, 10)
        driver.set_window_size(1400,900)
        driver.get(figpath)
    if export_flags['svg']:
        dirname=f'Figures/{name}_SVG/'
        if not os.path.exists(dirname):
            os.makedirs(dirname)
        figpath_svg='Figures/{name}_SVG/{name}.svg'
        export_svgs(F,filename=figpath_svg)

def figure_SfN24_1():

    flt=cia.defaultfilter()
    flt &= cia.rowfilter('task',0)
    
    #flt &= cia.rowfilter('session',[480,533])
    flt &= cia.rowfilter('session',[264,277])
    """DP=cia.depth_psychometric(flt)
    fDP=cig.plot_psychometric_curves(DP)
    """
    MP=cia.motion_psychometric(flt)
    f_world_motion=cig.plot_psychometric_curves(MP)
    RMP=cia.retinal_motion_psychometric(flt)
    f_ret_motion= cig.plot_psychometric_curves(RMP)
    

    #F=fDP
    F=column([f_world_motion,f_ret_motion])
    return F
def figure_retinal_demo():

    
    ff={}
    
    #flt_near=cia.rowfilter('chosen_near',True)
    DI=[ [-0.6,-0.0],[0.0,0.6]]
    for idi in range(2):
        
        #flt_depth=cia.rowfilter('chosen_near',idi==0)
        #flt_depth=cia.rowfilter('disp_incr',[-0.5,0.5])   
        flt_depth=cia.rowfilter('disp_incr',DI[idi])
        
        flt=cia.defaultfilter()
        #flt_legacy= cia.rowfilter('task',0) & cia.rowfilter('session',[0,260])
        #flt_new =   ~cia.rowfilter('task',2) & cia.rowfilter('session',[300,600])
        #flt1=flt_legacy | flt_new
        flt &= cia.rowfilter('task',0)
        
        #flt &= cia.rowfilter('disp_incr',disp_incr)
        flt &= (cia.rowfilter('self_amp_sign',1.0) | cia.rowfilter('self_amp_sign',-1.0))
        flt &= flt_depth
        
        flt1 =flt & cia.rowfilter('session',[ 200,330]) 
        flt2 =flt & cia.rowfilter ('session',[360,600]) 
        
        world_psy1=cia.motion_psychometric(flt1,False)
        world_psy2=cia.motion_psychometric(flt2,False)
        
        ret_psy1=cia.retinal_motion_psychometric(flt1,False)
        ret_psy2=cia.retinal_motion_psychometric(flt2,False)
        
        f_world1=cig.plot_psychometric_curves(world_psy1)
        f_ret1=cig.plot_psychometric_curves(ret_psy1)
        f_world2=cig.plot_psychometric_curves(world_psy2)
        f_ret2=cig.plot_psychometric_curves(ret_psy2)
        
        ff[idi]=row(column([f_world1,f_world2]),column([f_ret1,f_ret2]))
    F=column(ff[0],ff[1])
    return F
if __name__=="__main__":
    flt=cia.defaultfilter()
    flt &= cia.rowfilter('task',0)
    fltS = cia.rowfilter('session',-1)
    for isession in  [542,543,544,549]:
        fltS_=cia.rowfilter('session',isession)
        fltS |= fltS_
    fltS =cia.rowfilter('session',549)
    
    #fltS = cia.rowfilter('session',549)
    flt &= fltS
    #fCond=figure_dual_conditioned(flt=flt,ct=0.25,depth=True,motion=True,retinal=False)
    fFull=figure_dual_full(flt)
    
    export_flags={}
    export_flags['justshow']=True
    export_flags['html']=False
    export_flags['browser']=False
    export_flags['png']=False
    export_flags['svg']=False
    
    #output(fCond,export_flags,'CI_Dual_Conditional')
    output(fFull,export_flags,'CI_Dual_Full')
    #figpath="Figures/CI_Dual_May.html"
    
    #F=figure_dual_full()

    #F=figure_SfN24_1()
    #F=figure_retinal_demo()
    #output(F,export_flags,"Sfn_panel2")
    #figpath="Figures/CI_Vert_Disp.html"
    #F=figure_vert_disp()
    
    #output(F,export_flags,'VerticalDisparity')

    