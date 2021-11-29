import google_auth_oauthlib.flow
import googleapiclient.discovery
import os
import pprint
import requests
from spotify_client_secret import client_id, client_secret
import webbrowser
import http.server
import socketserver
import sys
import socket



scopes = ["https://www.googleapis.com/auth/youtube.readonly"]


# Function for cleaning the liked song names from Youtube
def str_cleaner(str):
    start = str.find( '(' )
    end = str.find( ')' )
    if (not start == -1) and (not end == -1):
        str = str[0 : start :] + str[end+1 : -1]
    str = str.replace("-","")
    #str = str.replace(" ", "%20")
    return str


def get_youtube_client():
    # modified from YouTube Data API
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secrets.json"
    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
    try:
        credentials = flow.run_local_server(authorization_prompt_message="",
                                            redirect_uri_trailing_slash=False)
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)
        request = youtube.videos().list(
            part="snippet",
            myRating="like",
            maxResults=100
        )
        response = request.execute()
        list_of_liked_songs = []
        for item in response["items"]:
            list_of_liked_songs.append(str_cleaner(item["snippet"]["title"]))
        pprint.pprint(list_of_liked_songs)
    except OSError as err:
        print("\nPlease wait 60 seconds before running the script again. "
              "This is necessary due to the maximum packet age.")
        return 0
    return response


def get_spotify_auth(cl_id):
    host = "localhost"
    port = 9000
    auth_endpoint = "https://accounts.spotify.com/authorize"
    red_uri = "http://localhost:{}/".format(port)
    scp = "playlist-modify-public playlist-modify-private"
    payload = {'client_id': cl_id,
               'response_type': 'code',
               'redirect_uri': red_uri,
               "show_dialog": "false",
               'scope': scp
               }

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # socket reusable directly.
        s.bind((host, port))
        s.listen()
        r = requests.get(auth_endpoint, params=payload)  # make the GET request
        webbrowser.open(r.url)  # clicking on the url gives the callback
        conn, addr = s.accept()
        data = conn.recv(1024)
    code = str(data)[str(data).find('code=')+5:-1]  # extract the code from the url



if __name__ == "__main__":
    #get_youtube_client()
    get_spotify_auth(client_id)


