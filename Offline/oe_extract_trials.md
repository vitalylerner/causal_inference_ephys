# Offline Open Ephys Trial Extraction

This script extracts trial information from Open Ephys recordings and saves it to a CSV file.

## Author
Vitaly Lerner

## Email
vlerner@ur.rochester.edu

## Date
2024-05-01

## Scope
Offline analysis of neural data recorded using Neuropixels probes and OpenEphys.

## Description
A part of the processing pipeline for the visual experiments using Neuropixels probes and OpeEphys.
The purpose of this script is to align kilosort-generated spike times with the visual stimulus events 
for further generation of raster plots and PSTHs.

## Field Names and Descriptions
| Field Name   | Description                                                                                      |
|--------------|--------------------------------------------------------------------------------------------------|
| rec          | Recording number                                                                                |
| trial        | Trial number within the recording                                                                |
| broke_fix    | Indicates if a fixation break occurred during the trial (True/False)                            |
| success      | Indicates if the trial was successful (True/False), meaningless for passive viewing, but useful for choice tasks |
| ap in acq    | Sample number of the Neuropixels (AP) signal in the acquisition as assigned by OpenEphys       |
| lfp in acq   | Sample number of the Neuropixels (LFP) signal in the acquisition as assigned by OpenEphys      |
| ap in stitch | Sample number of the AP signal in the stitched file as processed by Kilosort                   |
| lfp in stitch| Sample number of the LFP signal in the stitched file as processed by Kilosort                  |

## Steps
1. Imports necessary libraries and modules.
2. Defines the directory where the Open Ephys recordings are located.
3. Initializes a session object with the specified directory.
4. Retrieves the number of recordings in the session.
5. Defines the mapping of event lines and device names.
6. Calculates the sample number shifts for each device and recording.
7. Processes the triggers for each recording.
8. Extracts the timestamps and sample numbers for each event of interest.
9. Validates the events using Arduino-generated signals.
10. Stores the trial information in a list of dictionaries.
11. Converts the list of dictionaries to a pandas DataFrame.
12. Saves the DataFrame to a CSV file.

## Dependencies
- open-ephys-python-tools

## Usage
1. Install the required dependencies by running `pip install open-ephys-python-tools`.
2. Update the `directory` variable with the path to the directory containing the Open Ephys recordings.
3. Run the script.

## Output
A CSV file named "Trials.csv" will be saved in the specified directory, containing the extracted trial information.

