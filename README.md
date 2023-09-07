# OrbitLink
OrbitLink is designed to provide penetration testers and students an opportunity to apply their skills against a set of (somewhat) realistic applications that simulate the activity on a satellite control network. My experience with these networks is derived from the [resources](#resources) shown below as well as participating in the [Hack-A-Sat](https://hackasat.com/) competitions at DefCon.  

The data used in each of these applications is broken down in [resources](#resources), but more specifically a "correlated time stamp update" and "science mode" packet for TT&C was derived from a [Utah State University White Paper on Satellite Telemetry](https://digitalcommons.usu.edu/cgi/viewcontent.cgi?article=8846&context=etd). The SOSI data is a random sampling taken from [SpaceTrack API](https://www.space-track.org/documentation#api-formats) using RayDay 203, 2023. For the images, the samples provided are mostly hotdog related as it is an inside joke.  

OrbitLink provides a web front end and a suite of applications to simulate transmitting Telemetry Tracking and Control (TT&C) data, receiving images, and receiving Space Object Surveillance and Identification (SOSI) data.  

Below is a visual represntation of the communications flow between the web gateway and each of the controls. For details on each control program see [controls.md](client_controls/controls.md).  

```mermaid
graph TD
a(OrbitLink Web Gateway)
b(imagery_control.py)
c(sosi_control.py)
d(ttc_control.py)

a-->d
b-->a
c-->a
```
## OrbitLink Web Gateway
Python Flask web front-end which displays information from the OrbitLink suite

### Pages
- `/` displays index.html which holds 3 iframes for `/sosi`, `/ttc`, and `/imagery`
- `/sosi` displays the .json file named `data/sosi_store.tle` which holds all received SOSI communications and sorts the output in descending order based on timestamp
- `/ttc` displays the .json file named `data/ttc.json` which holds a log of all TTC commands send to the specified host and sorts the output in descending order based on timestamps in the `[time_data]` and `[mode_data]` fields respectively
  - Note: This page does not accurately display connectivity with the remote host, only that data is being successfully sent.
- `/imagery` renders the most recently received image file in the `images` directory
  - Note: The image byte code is sent in base64 encoded strings, to generate those strings you can use the following python code:
  ```python
  #Write images to base64 string where images is a list of image byte code
    for i, image_string in enumerate(images):
        remainder = len(image_string) % 4
        if remainder != 0:
            image_string += '=' * (4 - remainder)
        image_data = base64.b64decode(image_string)
        output_path = 'resources/con_image{}.png'.format(i+1)
        with open(output_path, "wb") as binary_image:
            binary_image.write(image_data)
  ```
### Usage
`python app.py -ttc <ttc_control_ip> --headless`
- `-ttc` specifies the IP of the destination host running the ttc_control.py application  
- `--headless` runs just the flask web server without all the listeners/senders

## OrbitLink Controls
SOSI Data Forwarder (sender), TT&C Command Forwarder (receiver), and Imagery Forwarder (sender) Applications

### Usage
- OrbitLink Controls:  
`sosi.exe sosi_control -dst <orbitlink_ip>`  
`imagery.exe imagery_control -dst <orbitlink_ip>`  
`ttc.exe ttc_control`  

- All Python (in the control programs) has been written in order to be compatible with version 3.4

## Red Team
Below is a diagram which displays all the communications between the different controls, a simulated "space" (which is the control creating a network connection to itself), and the communications with the OrbitLink hub. Using this information, we'll create a list of methods to degrade or manipulate the data in order to render this application suite ineffective. 
```mermaid
sequenceDiagram

    participant Space

    %% Group for SOSI
    box "SOSI Control"
        participant SOSI_Control
    end

    %% Group for Imagery
    box "Imagery Control"
        participant Imagery_Control
    end

    %% Group for TTC
    box "TTC Control"
        participant TTC_Control
    end

    %% Group for ORBITLINK
    box "ORBITLINK"
        participant ORBITLINK_SOSI
        participant ORBITLINK_Imagery
        participant ORBITLINK_TTC
    end
    
    %% For SOSI
    Space->>SOSI_Control: TrackWrite() to Port 7073
    SOSI_Control->>SOSI_Control: TrackStore() to sosi_store.tle
    SOSI_Control->>ORBITLINK_SOSI: QueueWrite() to Port 8067
    ORBITLINK_SOSI->>ORBITLINK_SOSI: TrackStore() on Port 7074 to data/sosi_store.tle

    %% For Imagery
    Space->>Imagery_Control: ImageGen() to Port 6960
    Imagery_Control->>Imagery_Control: ImageStore()
    Imagery_Control->>Imagery_Control: ImageQueue()
    Imagery_Control->>ORBITLINK_Imagery: ImageTransport() to Port 8069
    ORBITLINK_Imagery->>ORBITLINK_Imagery: ImageStore() on Port 8069

    %% For TTC
    ORBITLINK_TTC->>TTC_Control: CommandWrite() to Port 7474
    TTC_Control->>TTC_Control: CommandRecv() on Port 7474
    TTC_Control->>Space: CommandWrite() to Port 7474 (Invalid host)
```

### Degrade
#### SOSI
- Blocking UDP port `7073` on `sosi_control` will no longer allow SOSI data to be received from "space"
- Blocking UDP port `8067` on `OrbitLink` will no longer allow the master SOSI database to be updated
- Blocking UDP port `7074` on `OrbitLink` will no longer allow SOSI data to be stored
- Deny write access to `sosi_store.tle` on `OrbitLink` will no longer allow the web front end to display SOSI data and no new data can be stored

#### Imagery
- Blocking UDP port `6960` on `imagery_control` will no longer allow images to be generated from the data received from "space"
- Deny write access to the `images` folder on `imagery_control` will no longer allow images to be generated from the data received from "space"
- Blocking TCP port `8069` on `OrbitLink` will no longer allow the master Imagery database to be updated

#### TTC
- Blocking UDP port `7474` on `OrbitLink` will no longer allow TTC commands to be queued for transfer
- Blocking UDP port `7474` on `ttc_control` will no longer allow TTC commands to be sent to "space"

### Manipulate
#### SOSI
- The SOSI data is transmitted to the `OrbitLink` database via a fairly small packet which contains most of the metadata in the header. As long as a packet crafted can match the size of the header `!4s4sBBIH` the distant end should parse and store the data correctly.


#### TTC
- The TTC commands are transmitted to the `OrbitLink` database with no header. The data is either `>BI` for a science mode packet or `>I BB BB BB BB H I` for a correlated time stamp packet. As long as the data is sent to the correct port with the correct size the `ttc_control` should properly receive the data.

#### Imagery
- The imagery portion would be difficult to manipulate as the images are generated via a base64 encoded string that is decoded, read, and used to generate the images on `imagery_control`. However the header could be edited and additional images or metadata could be sent in transit. Too many options to list, but not worth the squeeze for manipulation.


## Setup
### OrbitLink
The flask web app can be run on any Python 3.8+ client with no dependency installation required using:
`python app.py -ttc <ttc_ip>`  
To run the web app before the clients are properly configured use the `--headless` flag

If you do run into dependency issues, there is a `requirements.txt` which lists all the required modules for orbitlink web app. Install using the included dependencies with:  
`cd ./orbitlink/orbitlink`  
`pip install --no-index --find-links=dependencies -r requirements.txt`

### SOSI Site
Manual Setup:

    Install python 3.4.4
    Copy python.exe from %INSTALLROOT% to C:\SOSI\sosi.exe
    Copy sosi_control.py to C:\SOSI
    Rename sosi_control.py to sosi_control
    Run 'Site Command'
        
Site Command:  
`cd C:\SOSI`  
`sosi.exe sosi_control -dst dst_ip`

### Imagery Site
Manual Setup:

    Install python 3.4.4
    Copy python.exe from %INSTALLROOT% to C:\IMAGERY\imagery.exe
    Copy imagery_control.py to C:\IMAGERY
    Rename imagery_control.py to imagery_control
    Run 'Site Command'
        
Site Command:  
`cd C:\IMAGERY`  
`imagery.exe imagery_control -dst dst_ip`
### TTC Site
Manual Setup:

    Install python 3.4.4
    Copy python.exe from %INSTALLROOT% to C:\TTC\ttc.exe
    Copy ttc_control.py to C:\TTC
    Rename ttc_control.py to ttc_control
    Run 'Site Command'
        
Site Commands:  
`cd C:\TTC`  
`ttc.exe ttc_control`

## Deployment
### Using VMware, ESXI and PowerCLI
#### 1. Install Python on Site Hosts
Connect to the ESXI server
```powershell
Connect-VIServer -Server <ESXi_Hostname_or_IP> -User <username> -Password <password>
```
1. Upload the Python 3.4 Installer to the VM's Datastore: 
```powershell
$datastore = "your_datastore_name"
$localInstallerPath = "C:\path\to\python-3.4.msi"
$remoteInstallerPath = "/vmfs/volumes/$datastore/python-3.4.msi"

Set-VMHostDatastore -VMHost <ESXi_Hostname_or_IP> -Name $datastore | New-DatastoreItem -Path $remoteInstallerPath -ItemType File -SourcePath $localInstallerPath
```
2. Install Python on the VM using PowerCLI  
```powershell
$vmName = "Your_VM_Name"

# The path on the VM where the installer was uploaded
$vmInstallerPath = "C:\python-3.4.msi"

# Command to execute the installer
$installCmd = "msiexec.exe /i $vmInstallerPath /qb"

# Execute the command on the VM
Invoke-VMScript -VM $vmName -ScriptText $installCmd -GuestUser "windows_username" -GuestPassword "windows_password"
```
3. Clean Up (Optional)
```powershell
Remove-DatastoreItem -Item $remoteInstallerPath -Confirm:$false
```
#### 2. Prepare Site Hosts as Imagery/SOSI/TTC
Connect to the ESXI server
```powershell
Connect-VIServer -Server <ESXi_Hostname_or_IP> -User <username> -Password <password>
```
1. Create application directory on the VM (replace `APP`, `Your_VM_Name`, `windows_username` and `windows_password`)
```powershell
$vmName = "Your_VM_Name"

# Command to create directory
$mkdirCmd = "mkdir C:\APP"

# Execute the command on the VM
Invoke-VMScript -VM $vmName -ScriptText $mkdirCmd -GuestUser "windows_username" -GuestPassword "windows_password"
```
2. Copy python.exe from C:\Python34 to application directory (replace `APP`, `windows_username` and `windows_password`)
```powershell
$copyCmd = "Copy-Item -Path C:\Python34\python.exe -Destination C:\APP\APP.exe"

# Execute the copy command on the VM
Invoke-VMScript -VM $vmName -ScriptText $copyCmd -GuestUser "windows_username" -GuestPassword "windows_password"
```
3. Copy APP_control.py from Local Host to VM's C:\APP (replace `APP`, `path_on_host`, `windows_username` and `windows_password`)
```powershell
$localFilePath = "C:\path_on_host\APP_control.py"
$vmFilePath = "C:\TTC\APP_control.py"

# Copy file to the VM
Copy-VMGuestFile -Source $localFilePath -Destination $vmFilePath -VM $vmName -LocalToGuest -GuestUser "windows_username" -GuestPassword "windows_password"
```
4. Rename APP_control.py to APP_control on the VM (replace `APP`, `windows_username` and `windows_password`)
```powershell
$renameCmd = "Rename-Item -Path C:\APP\APP_control.py -NewName C:\APP\APP_control"

# Execute the rename command on the VM
Invoke-VMScript -VM $vmName -ScriptText $renameCmd -GuestUser "windows_username" -GuestPassword "windows_password"
```
#### 3. Start Orbitlink
1. On main host (replace `ttc_host`)
```shell
cd orbitlink\orbitlink
python.exe app.py -ttc ttc_host
```
#### 4. Start Site Applications
1. On site hosts (replace APP)
```shell
cd C:\APP
APP.exe APP_control
```

## Resources
### SOSI
- Included some sample data taken from [Space-Track.org](space-track.org/#recent) which shows every element (ELSET) published on the indicated Julian date, prepended by the year.  
- Also included is a list of LEO, GEO, MEO, and HEO objects indicated by filename. Note, the specific orbit data is in a "3LE" three line element which indicates the name of the space object, followed by the TLE. This data is for every object in the specified group that has received an update within the past 30 days. (CAO: 20230723)

### TTC
- TT&C Academic Resource: [White Paper](https://link.springer.com/referenceworkentry/10.1007/978-1-4419-7671-0_69)
- [SpaceTrack API](https://www.space-track.org/documentation#api-formats)
- [Utah State University White Paper on Satellite Telemetry](https://digitalcommons.usu.edu/cgi/viewcontent.cgi?article=8846&context=etd) section 2.2 has a table that shows the data used for measuring telemetry and could be used to make TT&C more realistic, section 3.1.3 shows the science packet breakdown, section 3.2.2 shows an overview of the overall TT&C packet
- [MIT Course List on Satellite Engineering](https://ocw.mit.edu/courses/16-851-satellite-engineering-fall-2003/pages/lecture-notes/)
- [MIT PDF on Satellite Communications](https://ocw.mit.edu/courses/16-851-satellite-engineering-fall-2003/resources/l21satelitecomm2_done/) has some good information on link equations
- [MIT PDF on Satellite Engineering](https://ocw.mit.edu/courses/16-851-satellite-engineering-fall-2003/resources/l20_satellitettc/) has a high level overview of the communications

### Imagery
- Included sample images (mostly hotdog related), and their base64 strings named accordingly
