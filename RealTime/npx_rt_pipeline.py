import streamlit as st

# Title
st.header("Neuropixels Visual Experiment Control Panel")
"Version 1.0 Vitaly Lerner vlerner@ur.rochester.edu"

if "rows" not in st.session_state:
    st.session_state.rows = []


#row1 = max(st.session_state.rows) + 1 if st.session_state.rows else 1
#st.session_state.rows.append(row1)
C=st.columns(3)
subject_num=C[0].number_input("Subject",value=42,step=1)
session_num=C[1].number_input("Session",value=540,step=1)

def add_checkbox(txt:str,col:int):
    global n
    C[col].checkbox(f"{n}: " + txt)
    n+=1
def add_button(txt:str,col:int):
    global n
    btn= C[col].button(f"{n}: " + txt)
    n+=1
    return btn


n=1
add_checkbox("Start TEMPO and GLDots", 0)
add_checkbox("Turn on the NI-PXIe chassis and reboot TEMPOWAVE, then open this file again",0)
add_checkbox("Turn on Sensapex uMP device",0)
cmdSensapex=add_button("Start uMP control",0)
add_checkbox("Connect the probe to the cable", 0)
cmdOE = add_button("Start OpenEphys", 0)
add_checkbox("Make sure the folder in OpenEphys matches the session number", 1)
cmdArduino = add_button("Start Arduino panel", 1)
add_checkbox("S", 1)

if cmdSensapex:
    st.write("Starting Sensapex uMP control")
    # Code for starting Sensapex uMP control
    pass

if cmdArduino:
    st.write("Starting Arduino panel")
    # Code for starting Arduino panel
    pass

