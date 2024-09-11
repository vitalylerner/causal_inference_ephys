import pandas as pd




class pytempo_read_log:
    D=None
    protocol=-1
    log_file=None
    def __init__(self,log_file):
        self.log_file=log_file
        

    def plot(self):
        if self.protocol==142:#Human Depth discrimination
            self.plot_depth_vert_disparity()
        elif self.protocol==154: #Macaque Causal Inference
            self.print_ci_stats()
            
            self.plot_depth_vert_disparity()
    def choice_stats(self):
        D=self.D
        D=D[(D.outcome==0) | (D.outcome==5)]
        trials_correct=len(D[D.outcome==0])
        trials_total = len(D)
        correct_rate=int(trials_correct*100./trials_total)
        stats=pd.Series({'trials_total':trials_total,'trials_correct':trials_correct,'correct_rate':correct_rate})
        return stats
        
    """def print_ci_stats(self):
        D=self.D
        D=D[(D.outcome==0) | (D.outcome==5)]
        trials_correct=len(D[D.outcome==0])
        trials_total = len(D)
        correct_rate=int(trials_correct*100./trials_total)
        print (f'{trials_total} trials, {trials_correct}({correct_rate}%) correct')"""
    """def plot_motion_depth(self):
        D=self.D"""
        
    """def plot_depth_motion(self):
        D=self.D
        succ=len(D[D.outcome==0])
        print (f'ntrials={len(D)}, correct={succ}')"""
        
                    
    """def plot_depth_vert_disparity(self):
        if self.protocol==154:
            choice_field='chosen_target'
        elif self.protocol==142:
            choice_field='chosen_depth'
        D=self.D[self.D[choice_field]>0]
        #print (D)
        #print (D)
        u_sigma=sorted(list(set(D.vert_disp)))
        #print (u_sigma)
        p = figure(height=500, width=500,title='depth psychometric curves')
        clr=['black','green','red','blue']
        for isigma,sigma in enumerate(u_sigma):
            d=D[D.vert_disp==sigma]
            d2=d.groupby(['disp_incr']).mean().reset_index()
            p.scatter(x='disp_incr', y=choice_field,source=d2,color=clr[isigma]) 
            p.line(x='disp_incr', y=choice_field,source=d2,color=clr[isigma],legend_label=f'sigma={sigma:.3f}') 
        save(p)"""

    def read_params(self):
        
        def extract_var(tempovar,varclass:int=1,vartype=float):
            nchars=len(tempovar)
            if varclass==1:
                A=[vartype(l[nchars+1:-1]) for l in L if l[:nchars+1]==tempovar+' ']
            elif varclass==2:
                A=[vartype(l[nchars+1:-1].split()[0]) for l in L if l[:nchars+1]==tempovar+' ']
            if tempovar[:8]=='OBJ_VERT':
                return A[1:]
            else:
                return A
            
        def first_trial():  
            var='TRIAL# '
            return [il for il  in len(L) if L[il][:len(var)]==var][0]

            
        with open(self.log_file,'r') as f:
            L=f.readlines()
        trial    =extract_var ('TRIAL#')
        
        self.protocol=extract_var('PROTOCOL',2,int)[0]
        D={}
        if self.protocol==142: #Depth discrimination in humans
            vars_keys=['vert_disp','disp_incr','chosen_depth']
            vars_tempo=['OBJ_VERT_DISP_SIGMA','OBJ_DISP_INCR','CHOSEN_DEPTH']
            vars_class=[1,1,1]
            vars_type=[float,float,int]
        elif self.protocol==154: #Causal inference in macaques
            #print ('aaa')
            vars_keys=['vert_disp','disp_incr','chosen_target','outcome','self_amp']
            vars_tempo=['OBJ_VERT_DISP_SIGMA','OBJ_DISP_INCR','Chosen_Target','OUTCOME']
            vars_class=[1,1,1,2]
            vars_type =[float,float,int,int]
            X=extract_var('OUTCOME',2,int)
        #    print (X)
        for key,name,cl,tp in zip(vars_keys,vars_tempo,vars_class,vars_type):
            D[key]=extract_var(name,cl,tp)
        
        self.D=pd.DataFrame.from_dict(D)
        #print (self.D)
if __name__=='__main__':
    print ('pytempo v1')
    temport=tempo_simple_rt()
