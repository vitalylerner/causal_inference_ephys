import streamlit as st

def main():
    
    st.header("Neuropixels Data Processing Pipeline")
    openephys_folder = st.sidebar.file_uploader("Browse for a folder with OpenEphys recording")
    
    # Controls for data processing pipeline
    if st.sidebar.button("Stitch OpenEphys recordings"):
        from Stitch.npx_tempo_stitch import npx_oe_stitch
        #path = filedialog.askdirectory(title="Experiment path",initialdir='D:/DATA/IMEC_DATA/')+'/'#, filetypes=(("text    files","*.txt"), ("all files","*.*")))
        
        path=openephys_folder
        
        npx_oe_stitch(path)
        

    if st.sidebar.button("Run kilosort on stitched file"):
        # Code for running kilosort
        pass

    if st.sidebar.button("Run phy"):
        # Code for running phy
        pass

    if st.sidebar.button("Run autoclustering on kilosort results"):
        # Code for running autoclustering
        pass

    if st.sidebar.button("Extract trial data from OpenEphys recording"):
        # Code for extracting trial data
        pass

    if st.sidebar.button("Build trial-based rasters for each unit"):
        # Code for building trial-based rasters
        pass

    if st.sidebar.button("Filter the units based on post-hoc criteria"):
        # Code for filtering units
        pass

    if st.sidebar.button("Export the rasters to NEVx format"):
        # Code for exporting rasters
        pass

    if st.sidebar.button("Build units gallery for browsing"):
        # Code for building units gallery
        pass

if __name__ == "__main__":
    main()


