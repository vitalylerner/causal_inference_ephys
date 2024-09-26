"""
Created on Tue Feb 13 19:13:21 2024

@author: Vitaly  Lerner

"""


"""

TODO improve documentation

TODO: change the flow of log files. 
No need to duplicate log into repository

TODO: make a a-la-datajoint server that will produce figures as presentations

TODO: unify and structure directories, 
currently it's a mess. One place for all, at least
ephys. 

TODO: unite ci_tempo, moog_geometry and npx_tempo
to one repository
There are common funcitons, make sure to not duplicate them
"""

import pandas as pd
import numpy as np

import glob,os
import re
import multiprocessing
import os
class tempo_constants():
    CHOICE_CORRECT = 0;
    CHOICE_WRONG   = 5;
    BREAK_FIX      = 2; 

    TASK_DUAL      = 0;
    TASK_MOTION    = 1;
    TASK_DEPTH     = 2;

    PROTOCOL_NHP_CI= 154;
    PROTOCOL_HUMAN_DEPTH=-1;
    PROTOCOL_EYE_CALIBRATION=1;


class ci_tempo_parser():
    """
    Causal Inference TEMPO files Parser.
    
    Parses behaviour related variables from TEMPOW logs.
    Built primarily for CI-related tasks.
    """
    
    tempo_fields=None 
    
    H=None
    new_rows=None
    
    H=None
    D=None

    def set_folder(self,folder:str):
        """
        Set main folder of the MOOG results of the subject.

        Parameters
        ----------
        folder : str
            main folder

        Returns
        -------
        None.

        """
        self.folder=folder
            
    def __init__(self,folder:str="Z:/Data/MOOG/Dazs/"):
        self.tempo_fields=pd.read_csv('SETTINGS/TEMPO_Fields.csv')
        self.set_folder(folder)

    def header_fields(self):
        """
        List experiment fields(not trial-to-trial).

        Returns
        -------
        list of strings
            header fields

        """
        return self.tempo_fields[self.tempo_fields['trialvar']==False]

    def trial_fields(self):
        """
        List trial fields.

        Returns
        -------
        list of strings
            trial fields

        """
        return self.tempo_fields[self.tempo_fields['trialvar']==True]



    def build_headers(self):
        """
        Build Headers from directory.

        Returns
        -------
        None.

        
         Prepare the headers table
         retrieve meta data
         detect new rows
        """
        
        #first, import existing rows
        try:
            H0=self.import_headers_from_csv()
        except FileNotFoundError:
            H0=None
        print (H0)
        #existing_hfiles=list(self.H['htb'])
        
        #retrieve a list of all log files
        
        log_files=list(glob.glob(self.folder + 'TEMPO/*.log'))
        log_files=[os.path.basename(p) for p in log_files]
        
        #exclude files not in a shape of SPECIES#c#m#.htb
        log_files=[p for p in log_files if len(re.findall(r'\d+', p))==3]
        species=[p[0] for p in log_files]
        nums =np.array([ np.array([int(i) for i in re.findall(r'\d+', p)],int)  for p in log_files])
        
        if H0 is None:
            new_log_files=sorted(list(set(log_files)))
        else:
            new_log_files=sorted(list(set(log_files)-set(H0['log'])))
        
        nfiles=len(new_log_files)
        empty_int=[-1 for f in log_files]
        empty_str=["" for f in log_files]
        empty_none=[None for f in log_files]
        Hdict={         'htb':log_files,'log':log_files,
                                        'species':species,'subject':nums[:,0],
                                        'session':nums[:,1],'rec':nums[:,2],
                                        'datetime':empty_none,
                                        "protocolnum":empty_int,
                                        "protocol":empty_str,
                                        "trials_total":empty_int,
                                        "trials_correct":empty_int,
                                        "trials_wrong":empty_int,
                                        "task":empty_int
                                        }

        #Prepare the header table 
        H=pd.DataFrame(Hdict)
        

        H.sort_values(['subject','session','rec'],inplace=True)
        H.reset_index(drop=True,inplace=True)
        
        # Fill the header table with values from log
        RNG_ALL=np.arange(nfiles)
        HH=[H.iloc[n].copy() for n in RNG_ALL]
        with multiprocessing.Pool(16) as p:
           HH=list( p.map(self.retrieve_meta_from_log,HH))
           
        for i in RNG_ALL:
            H.iloc[i]=HH[i]
        #print (H)
        self.H=H
        print (self.H)
        # Detect new lines and store row numbers to new_rows
        if not H0 is None:
            S0=H0.session.to_list()
            S =H.session.to_list()
            news=sorted(list(set(S)-set(S0)))
        else:
            S=H.session.to_list()
            news=sorted(list(set(S)))
        self.new_rows=np.array([i for i in range(len(S)) if S[i] in news])

            
    def retreieve_new_data_from_log(self):
        if self.new_rows is None:
            if self.H is None:
                self.H=self.import_headers_from_csv()
            flt_ci=self.H['protocolnum']==154
            csv_files=list(glob.glob(self.folder+'/CSV/*.csv'))
            csv_files=[os.path.basename(csvf)[:-3]+'log' for csvf in csv_files]
            csv_files=sorted(csv_files)
            log_files=self.H['log'].to_list()
            new_logs=sorted(list(set(log_files)-set(csv_files)))
            flt_new=[ self.H.log.to_list()[i] in new_logs for i in range(len(self.H))]
            flt_ci_new=flt_new &flt_ci
            self.new_rows=np.where(flt_ci_new)[0]
        for irow in self.new_rows:
            self.retrieve_data_from_log(irow)

        
    def retrieve_data_from_log(self,irow:int):
        
        def cast(val:list,type_str:str):
            if type_str=='int':
                tp=int
            elif type_str=='float':
                tp=float
            elif type_str=='bool':
                tp=bool
            elif type_str=='str':
                tp=str
            if tp=='str':
                return val
            else:
                return np.array([float(v) for v in val],dtype=tp)
        def extract_values(field_,isarray:bool=False):
            tempo_str=str(field_['field_in_log'])
            
            field_type=str(field_['type'])
            field_mult=(field_['multiplier'])
            lines_field=[l.split(' ')[1:] for l in lines_trials if l.split(' ')[0]==tempo_str]
            if isarray:
                lines_field=[ [ll for ll in l if len(ll)>0] for l in lines_field]
                vals=np.array([cast(l,field_type) for l in lines_field])
            else:
                lines_field= [ [ll for ll in l if len(ll)>0][0] for l in lines_field ]
                vals=cast(lines_field,field_type)
            if (field_type=='float'):
                vals=np.round(vals*field_mult,6)
            return vals
        def extract_instructional():
            F=self.trial_fields()
            field_lum=F[F['field']=='targ_lum'].iloc[0]
            LUM=extract_values(field_lum,True)
            return np.array([  len(set( LUM[k,:]))>1  for k in range(LUM.shape[0]) ],dtype=bool)
        
        def legacy_motion_choice():
            tempo_str='CHOSEN_MOTION'
            lines_field=[l.split(' ')[1:] for l in lines_trials if l.split(' ')[0]==tempo_str]
            lines_field= [ [ll for ll in l if len(ll)>0][0] for l in lines_field ]
            vals=np.array(lines_field,int)+1
            return vals
        print("bbb")
        h=self.H.iloc[irow]
        print (h)
        fname='DATA/TEMPO/'+h['log']
        
        F=self.trial_fields()
        F=F[F['field']!='targ_lum']

        with open(fname) as f:
            lines = f.readlines()
        fields_num=len(F)
        
        trial_lines=[il for il,l in enumerate(lines) if l[:5]=='TRIAL']
        trials_num=len(trial_lines)
        trial1_line=trial_lines[0]
        lines_trials=lines[trial1_line:]
        lines_header=lines[:trial1_line]
        
        table={}
        table['species']=h['species']
        table['subject']=h['subject']
        table['session']=h['session']
        table['protocolnum']=h['protocolnum']
        table['task']=h['task']
        table['rec']	=h['rec']
        table['trial'] = np.arange(trials_num,dtype=int)+1
        
        
        # determine for each trial if it was instructional
        table['instructional']=extract_instructional()
        
        #retrieve trial-by-trial variables
        for iF in range(fields_num):
            field=F.iloc[iF]
            f_name=str(field['field'])
            f_vals=extract_values(field,False)
            table[f_name]=f_vals
            #print (f_name,f_vals) 
            
        if len(table['choice'])==0:
            #reconstruct choice using outcome and object amplitude in 
            #motion task
            #   ARGHHHH!!!! 
            print ('LEGACY! CHOSEN_MOTION instead of Chosen_Target is used')
            obj_amp=table['obj_amp']
            outcome=table['outcome']
            
            choice=(2-np.array( (((obj_amp==0.0) & (outcome==5)) |
                               ((obj_amp!=0.0) & (outcome==1)))  ,
                            dtype=int))*np.array(outcome!=2,dtype=int)
    
            table['choice']=choice
            
        #Earlier files don't have vertical disparity
        if len(table['vert_disp_flag'])==0:
            L=len(table['trial'])
            table['vert_disp_flag']=np.array([0 for l in range(L)])
            table['vert_disp_sigma']=np.array([0 for l in range(L)])
            print (L)
        try:
            table=pd.DataFrame.from_dict(table)
            table.to_csv(f'''DATA/CSV/{h['log'][:-4]}.csv''',index=False)
        except ValueError:
            #pp=pd.DataFrame.from_dict(table)
            for k in list(table.keys()):
                try:
                    print (k,len(table[k]))
                except TypeError:
                    print ('!',k,table[k])
            print ("ERROR!",irow)
 
    def unite_csv(self):
            F=glob.glob("DATA/CSV/m*c*r*.csv")
            D=pd.read_csv(F[1])
            a=D.columns[0]
            for f in F[1:]:
                    d=pd.read_csv(f)
                    D=pd.concat([D,d],ignore_index=True)
            D.to_csv("DATA/Summary/CI.csv",index=False)
            self.D=D
            #print (D[D['instructional']])
    
                            

            #return h
    def retrieve_meta_from_log(self,h):
        # Prepares the headers table: Step 2
        # Reads the log files and retrieves meta data
        # not to be called from outside, only for calling in parallel
        # from build_headers_from_dir
        F=self.header_fields()
        full_path=self.folder+'TEMPO/'+h['log']
        def loglines(field):
                return [l for  l in lines if l[0]==field]
        with open(full_path, 'r') as fp:
                # read all lines using readline()
                lines = fp.readlines()
                lines=[l.split() for l in lines]
                lines=[l for l in lines if l[0] in list(self.tempo_fields['field_in_log'])]
        line_date    =loglines("DATE")[0]
        line_protocol=loglines("PROTOCOL")[0]
        lines_outcome=loglines("OUTCOME")
        try:
                outcome=np.array([l[1] for l in lines_outcome],int)
                CORRECT=0
                WRONG  =5
                
                outcome_correct=np.sum(outcome==CORRECT)
                outcome_wrong=np.sum(outcome==WRONG)
                outcome_all  =outcome_correct+outcome_wrong
                h['trials_correct']=outcome_correct
                h['trials_wrong']=  outcome_wrong
        except ValueError:
                print ("Counting Outcome:",h['log'])
        
        h['datetime']=pd.to_datetime(line_date[3]+' '+line_date[1])
        h['protocol']=line_protocol[2][1:-1]
        h['protocolnum']=int(line_protocol[1])
        h['trials_total']=len(lines_outcome)
        if h.session==547:
            print ('AAAA@!')
        if h['protocolnum']==154:
                try:
                        line_task=loglines("OBJ_CAUSAL_TASK_TYPE")[0]
                        h['task']=int(float(line_task[1]))
                except:
                        print ("no task selector:",h['log'])
        return h
    
        
    def export_headers_to_csv(self):
        self.H.to_csv('DATA/Summary/Header.csv',index=False)

            
    def import_headers_from_csv(self):
        self.H=pd.read_csv("DATA/Summary/Header.csv")

    def print(self):
            print (self.tempo_fields)

    def find_wrong_instructional_trials(D:pd.DataFrame):
        Instr=D[D['instructional']].copy()
        Instr=Instr[['session','rec','task','Trial','choice_near','choice_moving','correct']]#.copy()
        Instr.sort_values(by=['session','Trial'],inplace=True)
        Wrong=Instr[Instr['correct']==False]

        #Wrong=Wrong[]
        Wrong_MOTION=Wrong[Wrong['task']==1]
        Wrong_DEPTH=Wrong[Wrong['task']==2]
        Wrong_DUAL=Wrong[Wrong['task']==0]
        print ('Motion',len(Wrong_MOTION),len(Instr[Instr['task']==1]),len(Wrong_MOTION)*1.0/len(Instr[Instr['task']==1]))
        print ('Depth',len(Wrong_DEPTH),len(Instr[Instr['task']==2]),len(Wrong_DEPTH)*1.0/len(Instr[Instr['task']==2]))
        print ('Dual',len(Wrong_DUAL),len(Instr[Instr['task']==0]),len(Wrong_DUAL)*1.0/len(Instr[Instr['task']==0]))

        Wrong.to_csv('DATA/WrongInstr.csv',index=False)
        Instr.to_csv('DATA/Instr.csv',index=False)

def ci_preprocess_db(D:pd.DataFrame):
    TASK_DUAL=tempo_constants.TASK_DUAL
    TASK_MOTION=tempo_constants.TASK_MOTION
    TASK_DEPTH=tempo_constants.TASK_DEPTH

    
    #D=D[D['instructional']]
    task=np.array(D['task']).astype(int)
    choice=np.array(D['choice']).astype(int)
    obj_amp=np.array(D['obj_amp']).astype(float)
    disp_incr=np.array(D['disp_incr']).astype(float)
    
    moving=obj_amp!=0
    near  =disp_incr>0
    
    N=len(choice)
    
    choice_MOTION_moving= np.array(choice==1).astype(int)
    choice_MOTION_near	=np.zeros(N)
    
    choice_DEPTH_moving =np.zeros(N)
    choice_DEPTH_near	=np.array(choice==2).astype(int)
    
    choice_DUAL_moving=np.array([c in [2,4] for c in choice]).astype(bool)
    choice_DUAL_near=np.array([c in [1,2] for c in choice]).astype(bool)
    

    choice_moving=	np.array((task==TASK_DUAL)	*choice_DUAL_moving+
                                    (task==TASK_MOTION)	*choice_MOTION_moving+
                                    (task==TASK_DEPTH)	*choice_DEPTH_moving).astype(bool)
                                    
    choice_near=	np.array((task==TASK_DUAL)	*choice_DUAL_near+
                                    (task==TASK_MOTION)	*choice_MOTION_near+
                                    (task==TASK_DEPTH)	*choice_DEPTH_near).astype(bool)
                                    
    choice_correct =np.array((task==TASK_DUAL)	* (choice_near == near) * (choice_moving==moving)+
                                    (task==TASK_MOTION)	* (choice_moving == moving)+
                                    (task==TASK_DEPTH)	* (choice_near   == near)   ).astype(bool)
    D['choice_moving']=choice_moving
    D['choice_near']=choice_near
    D['correct']=choice_correct
    
                 
def ci_import_from_db(dbpath:str='DATA/Summary/CI.csv'):
    """
    Causal Inference: import behavioral data from database(csv).
    Caution: this function only works for causal inference experiments. 
    Log reading functionality is the same as in other protocols, but
    retinal amplitude, choice etc are specific to CI.
    
    Parameters
    ----------
    dbpath : str, optional
        path of the csv file. The default is 'DATA/CI.csv'.

    Returns
    -------
    D : pandas data frame 
        Table arranged for causal inference analysis.
    """
    D=pd.read_csv(dbpath)
    ci_preprocess_db(D)
    return D


class tempo_parser():
    folder=""
    logfile=""
    header=None
    def __init__(self,folder:str="Z:/Data/MOOG/Dazs/TEMPO/",logfile:str="params.log"):
        self.folder = folder
        self.logfile = os.path.join(self.folder, logfile)
        parent_folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.tempo_fields = pd.read_csv(os.path.join(parent_folder, 'SETTINGS/TEMPO_Fields.csv'))

    def header_fields(self):
        """
        List experiment fields(not trial-to-trial).

        Returns
        -------
        list of strings
            header fields

        """
        return self.tempo_fields[self.tempo_fields['trialvar']==False]

    def trial_fields(self):
        """
        List trial fields.

        Returns
        -------
        list of strings
            trial fields

        """
        return self.tempo_fields[self.tempo_fields['trialvar']==True]
    def retrieve_meta(self):
        # Prepares the headers table: Step 2
        # Reads the log files and retrieves meta data
        # not to be called from outside, only for calling in parallel
        # from build_headers_from_dir
        
        full_path=self.logfile
        h={}
        def loglines(field):
                return [l for  l in lines if l[0]==field]
        with open(full_path, 'r') as fp:
                # read all lines using readline()
                lines = fp.readlines()
                lines=[l.split() for l in lines]
                lines=[l for l in lines if l[0] in list(self.tempo_fields['field_in_log'])]
        line_date    =loglines("DATE")[0]
        line_protocol=loglines("PROTOCOL")[0]
        lines_outcome=loglines("OUTCOME")
        try:
                outcome=np.array([l[1] for l in lines_outcome],int)
                outcome_correct=np.sum(outcome==tempo_constants.CHOICE_CORRECT)
                outcome_wrong=np.sum(outcome==tempo_constants.CHOICE_WRONG)
                h['trials_correct']=outcome_correct
                h['trials_wrong']=  outcome_wrong
        except ValueError:
                print ("Counting Outcome:",h['log'])
        
        h['datetime']=pd.to_datetime(line_date[3]+' '+line_date[1])
        h['protocol']=line_protocol[2][1:-1]
        h['protocolnum']=int(line_protocol[1])
        h['trials_total']=len(lines_outcome)
        if h['protocolnum']==154:
                try:
                        line_task=loglines("OBJ_CAUSAL_TASK_TYPE")[0]
                        h['task']=int(float(line_task[1]))
                except:
                        print ("no task selector:",h['log'])
        self.header=h

    def retrieve_data(self):
        
        def cast(val:list,type_str:str):
            if type_str=='int':
                tp=int
            elif type_str=='float':
                tp=float
            elif type_str=='bool':
                tp=bool
            elif type_str=='str':
                tp=str
            if tp=='str':
                return val
            else:
                return np.array([float(v) for v in val],dtype=tp)
        def extract_values(field_,isarray:bool=False):
            tempo_str=str(field_['field_in_log'])
            
            field_type=str(field_['type'])
            field_mult=(field_['multiplier'])
            lines_field=[l.split(' ')[1:] for l in lines_trials if l.split(' ')[0]==tempo_str]
            if isarray:
                lines_field=[ [ll for ll in l if len(ll)>0] for l in lines_field]
                vals=np.array([cast(l,field_type) for l in lines_field])
            else:
                lines_field= [ [ll for ll in l if len(ll)>0][0] for l in lines_field ]
                vals=cast(lines_field,field_type)
            if (field_type=='float'):
                vals=np.round(vals*field_mult,6)
            return vals
        def extract_instructional():
            F=self.trial_fields()
            field_lum=F[F['field']=='targ_lum'].iloc[0]
            LUM=extract_values(field_lum,True)
            return np.array([  len(set( LUM[k,:]))>1  for k in range(LUM.shape[0]) ],dtype=bool)
        
        def legacy_motion_choice():
            tempo_str='CHOSEN_MOTION'
            lines_field=[l.split(' ')[1:] for l in lines_trials if l.split(' ')[0]==tempo_str]
            lines_field= [ [ll for ll in l if len(ll)>0][0] for l in lines_field ]
            vals=np.array(lines_field,int)+1
            return vals
        
        h=self.header
        #print (h)
        fname=self.logfile
        
        F=self.trial_fields()
        F=F[F['field']!='targ_lum']

        with open(fname) as f:
            lines = f.readlines()
        fields_num=len(F)
        
        trial_lines=[il for il,l in enumerate(lines) if l[:5]=='TRIAL']
        trials_num=len(trial_lines)
        trial1_line=trial_lines[0]
        lines_trials=lines[trial1_line:]
        lines_header=lines[:trial1_line]
        
        table={}
        #table['species']=h['species']
        #table['subject']=h['subject']
        #table['session']=h['session']
        table['protocolnum']=h['protocolnum']
        table['task']=h['task']
        #table['rec']	=h['rec']
        table['trial'] = np.arange(trials_num,dtype=int)+1
        
        
        # determine for each trial if it was instructional
        table['instructional']=extract_instructional()
        
        #retrieve trial-by-trial variables
        for iF in range(fields_num):
            field=F.iloc[iF]
            f_name=str(field['field'])
            f_vals=extract_values(field,False)
            table[f_name]=f_vals
            #print (f_name,f_vals) 
            
        if len(table['choice'])==0:
            #reconstruct choice using outcome and object amplitude in 
            #motion task
            #   ARGHHHH!!!! 
            print ('LEGACY! CHOSEN_MOTION instead of Chosen_Target is used')
            obj_amp=table['obj_amp']
            outcome=table['outcome']
            
            choice=(2-np.array( (((obj_amp==0.0) & (outcome==5)) |
                               ((obj_amp!=0.0) & (outcome==1)))  ,
                            dtype=int))*np.array(outcome!=2,dtype=int)
    
            table['choice']=choice
            
        #Earlier files don't have vertical disparity
        if len(table['vert_disp_flag'])==0:
            L=len(table['trial'])
            table['vert_disp_flag']=np.array([0 for l in range(L)])
            table['vert_disp_sigma']=np.array([0 for l in range(L)])
            print (L)
        try:
            self.table=pd.DataFrame.from_dict(table)
            #table.to_csv(f'''DATA/CSV/{h['log'][:-4]}.csv''',index=False)
        except ValueError:
            #pp=pd.DataFrame.from_dict(table)
            for k in list(table.keys()):
                try:
                    print (k,len(table[k]))
                except TypeError:
                    print ('!',k,table[k])
            print ("ERROR!",irow)

if __name__=="__main__":

    """TP=ci_tempo_parser('DATA/')
    TP.build_headers()
    TP.export_headers_to_csv()
    
    TP.import_headers_from_csv()
    TP.retreieve_new_data_from_log()
    TP.unite_csv()"""

    tp=tempo_parser('C:/TEMPO/MoogProtocol_VL/','params.log')
    tp.retrieve_meta()
    tp.retrieve_data()
    print (tp.table)
  