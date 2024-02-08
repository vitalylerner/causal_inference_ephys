load('MAT\m42c454r6.htb.mat')
a=squeeze(good_data.event_data);

code_trial_start=1;
code_stim_start=4;
code_stim_end=5;
code_trial_end=15;
code_success=12;


for iTr=1:98
    itrstart=find(a(:,iTr)==code_trial_start);
    if numel(itrstart)<1
        itrstart=-1
    end
    tr_start(iTr)=itrstart;
    
    stim_start(iTr)=find(a(:,iTr)==code_stim_start);
    stim_end(iTr)=find(a(:,iTr)==code_trial_end);
    plot(tr_start(iTr)*[1 1],[iTr+0.1 iTr+0.9],'k');hold on
    plot(stim_start(iTr)*[1 1],[iTr+0.1 iTr+0.9],'m')
    plot(stim_end(iTr)*[1 1],[iTr+0.1 iTr+0.9],'m')
    %plot(stim_start(iTr)*[1 1],[iTr+0.1 iTr+0.9],'m')
    %plot(a(:,1:))
end
tr_start;
xlim([-1,5000])