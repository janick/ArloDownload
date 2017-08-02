ArloDownload

Automatically download new video recordings from Arlo to local file or Dropbox.
Optionally concatenate videos that are close in time.

Video files are backed up under the following pathname:

      <rootdir>/YYYY-MM-DD/<camera>/HH:MM:SS+<duration>s.mp4

where

      rootdir       Name of the downloaded data directory, as configured, or Dropbox app folder
      YYYY-MM-DD    Date the video was created
      camera        Name of the camera, as configured
      HH:MM:SS      Time (24hr) the video was created
      duration      Total duration of the video, in seconds



Originally developped by Tobias Himstedt <himstedt@gmail.com>
Updated by Preston Lee <zettaiyukai@gmail.com>, Janick Bergeron <janick@bergeron.com>

This script is open-source; please use and distribute as you wish.
There are no warranties; please use at your own risk.
