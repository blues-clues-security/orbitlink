# OrbitLink
Suite of applications to simulate a satellite control network

## OrbitLink Control
SOSI Data Receiver and TT&C Command Transfer Application

### Usage
python ol_control_send.py 192.168.0.47 192.168.0.47 12345 SOSI

## OrbitLink Data Vault
SOSI and TT&C Data Storage Application

## OrbitLink Web Gateway
Web Front-End Application

## Resources
Included some sample data taken from [Space-Track.org](space-track.org/#recent) which shows every element (ELSET) published on the indicated Julian date, prepended by the year.  
Also included is a list of LEO, GEO, MEO, and HEO objects indicated by filename. Note, the specific orbit data is in a "3LE" three line element which indicates the name of the space object, followed by the TLE. This data is for every object in the specified group that has received an update within the past 30 days. (CAO: 20230723)