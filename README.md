## YouTube-Spotify-App
### Description
This app gets the liked songs on users 
YouTube account and makes a Spotify 
playlist out of these songs. The idea is 
to keep Spotify account up-to-date in sense
of music and collect the whole musical 
experience in Spotify.
### Covered Topics
The technical gains from this project are mainly:
* working with REST-APIs
* OAuth 2.0 Authorization Flow
* JSON format
### Used libraries
* google_auth_oauthlib
* googleapiclient 
* requests
### Notes
The app functions perfectly when the liked video is in "song name - artist name" format.
If the liked video is a song but not in the expected format, success rate decereases. One can 
develop a filtering function to extract only the useful information such as song & artist name. However,
it has not been done in this project since it is not the main focus.
### Credit
The idea of this project is inspired by the 
following repository: 
https://github.com/TheComeUpCode/SpotifyGeneratePlaylist
