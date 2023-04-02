# Dependencies
## WinXP Download
https://archive.org/details/WinXPProSP3x86
- Had to turn off firewall to get ol_control_receive_34.py to receive data

## Win Server 2008 R2 Download
Attempt 1: https://archive.org/details/sw-dvd-5-windows-svr-dc-ee-se-web-2008-r-2-64-bit-english-w-sp-1-mlf-x-17-22580
Attempt 2: https://archive.org/details/Windows_Server_2008_SP2_x64.iso_reupload

## Python
- Python version 3.4

# OrbitLink Data Vault (Db) Notes
- Need to install Db on a server (missing .Net framework either 2.0 or 3.5)


## SQL Server Download
https://www.microsoft.com/en-us/download/confirmation.aspx?id=30438
- used "SQLEXPR_x86_ENU.exe" on Windows Server 2008 R2
- SQLCMD located "C:\Program Files (x86)\Microsoft SQL Server\100\Tools\Binn
- SQL ServerName: WIN-ET9RUUC6B2G\SQLEXPRESS

*SQL Express was a nightmare to configure, switching to PostGRES*

## PostGres
POSTGRES Download: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- Only version 10 and below compatible with Server 2008 
- Need Visual C++ Package for v10: https://www.microsoft.com/en-us/download/details.aspx?id=48145
- Version 10.23 did not have required VCC packages (even after attempting to install, might be issue with SP1 vs. SP2), 9.3.25 worked after installing 2008 R2 SP2 (only tried the oldest possible version)
  - Left all defaults, postgres/ postgres as user

### TODO
- [ ] Create database
- [ ] Input test data
- [ ] Input test data from OL Control
- [ ] Create database backups on separate server

# OL Control (SOSI and TT&C Data Transfer)

## Setup / Dependencies
- In order to build a 32 bit version of an executable, need to use a 32-bit version of Python
  - Actually installed Python 3.4 (newest version of Python compatible with XP)
- Also tried compiling with go, but so far same issues. Might have most luck with Python.
- Python 3.4 success without executable, may not need to use one

## SOSI Data TODO
- [ ] Craft the payload in ol_control_send to look like TLE data
- [X] Write database for SOSI data (done: [TLE example](db/init.sql))
- [ ] Change ol_control_receive_34 to write to database instead of text file

## TT&C Data TODO
- [ ] Craft TT&C database schema
- [ ] Write TT&C data to database from web app
- [ ] Read data from database and send from ol_control_send
- [ ] Consider splitting ol_control to ol_ttc and ol_sosi



# OL Web Gateway (Web)

## TODO
- [ ] Create web front end to enter commands to send to space objects