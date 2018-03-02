# FtpTiny
## Summary
A simple ftp server that runs in Micropython in a thread. To use this with FileZilla, set it to PASV mode and maximum of 1 connection at a time.

Modified from https://github.com/cpopp/MicroFTPServer/tree/master/uftp
## Usage
To use this, import the library (ftptiny), create one, then use start and stop.
```python
import ftptiny
ftp = ftptiny.FtpTiny() # create one
ftp.start() # start an ftp thread
# do whatever you want to do here
ftp.stop() # stop the ftp thread
```
## Supported
This supports:
* `Folders`: create, delete, rename
* `Files`: send, receive, delete, rename
* `Path`: change directory, list contents
