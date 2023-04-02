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

POSTGRES Download: https://www.enterprisedb.com/downloads/postgres-postgresql-downloads
- Only version 10 compatible with Server 2008 
- Need Visual C++ Package: https://www.microsoft.com/en-us/download/details.aspx?id=48145
- Version 10.23 did not have required VCC packages, 9.3.25 worked (only tried the oldest possible version)
  - Left all defaults, postgres/ postgres as user
  - 


# OL Control (TT&C Data Transfer)
- In order to build a 32 bit version of an executable, need to use a 32-bit version of Python
  - Actually installed Python 3.4 (newest version of Python compatible with XP)
- Also tried compiling with go, but so far same issues. Might have most luck with Python.
- Python 3.4 success without executable, may not need to use one