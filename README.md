# FtpTiny
A simple ftp server that runs in Micropython in a thread. 

Modified from https://github.com/cpopp/MicroFTPServer/tree/master/uftp
## Installation
To use this, import the library (ftptiny), create one, then use start and stop.
```python
import ftptiny
ftp = ftptiny.FtpTiny() # create one
ftp.start() # start an ftp thread
# do whatever you want to do here
ftp.stop() # stop the ftp thread
```
## Notes
This only supports changing folders, reading, and writing. No rename, delete, ...
