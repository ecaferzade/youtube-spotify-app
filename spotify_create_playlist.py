import google_auth_oauthlib.flow
import googleapiclient.discovery
import os
import pprint
import requests
from spotify_client_secret import client_id, client_secret, user_id
import webbrowser
import socket
import json


scope_youtube = ["https://www.googleapis.com/auth/youtube.readonly"]
scope_spotify = "playlist-modify-public playlist-modify-private user-read-email"


def get_liked_vids_youtube(n):
    """
    Get permission of the user and collect the last n liked videos from YouTube.
    :param n: Number of liked songs to collect
    :return: list of last n liked videos
    """
    # modified from YouTube Data API
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    api_service_name = "youtube"
    api_version = "v3"
    client_secrets_file = "client_secrets.json"
    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scope_youtube)
    try:
        credentials = flow.run_local_server(authorization_prompt_message="",
                                            redirect_uri_trailing_slash=False)
        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)
        request = youtube.videos().list(
            part="snippet",
            myRating="like",
            maxResults=n
        )
        response = request.execute()
        list_of_liked_videos = []
        for item in response["items"]:
            list_of_liked_videos.append(item["snippet"]["title"])
    except OSError:
        print("\nPlease wait 60 seconds before running the script again. "
              "This is necessary due to the maximum packet age.")
        return 0
    return list_of_liked_videos


def get_spotify_auth(cl_id):  # Chosen method: Authorization Code
    """
    Complete the authorization process following authorization code method.
    :param cl_id: This string is the apps client id, stored in a secrets file. (str)
    :return: Access token, necessary for future operations like creating a playlist. (str)
    """
    # Request User Authorization
    # Prepare the first GET request to take users permission
    host = "localhost"
    port = 9000
    auth_endpoint = "https://accounts.spotify.com/authorize"
    red_uri = "http://localhost:{}/".format(port)
    payload_get = {'client_id': cl_id,
                   'response_type': 'code',
                   'redirect_uri': red_uri,
                   'show_dialog': 'false',
                   'scope': scope_spotify
                   }
    # After permission, a code will be sent.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)  # socket reusable directly.
        s.bind((host, port))
        s.listen()
        r = requests.get(auth_endpoint, params=payload_get)  # make the GET request
        webbrowser.open(r.url)  # clicking on the url gives the callback
        conn, addr = s.accept()
        data = str(conn.recv(1024))
    # extract the code from the url
    start = data.find('code=')+5
    stop = data.find('HTTP/1.1')-1
    code = data[start: stop]

    # Request Access Token
    # Exchange auth code for an access token
    token_endpoint = "https://accounts.spotify.com/api/token"  # make a POST request to here.
    payload_post = {"grant_type": "authorization_code",
                    "code": "{}".format(code),
                    "redirect_uri": "{}".format(red_uri),
                    "client_id": "{}".format(cl_id),
                    "client_secret": "{}".format(client_secret)
                    }
    headers_post = {"Content-Type": "application/x-www-form-urlencoded"}
    token_r = requests.post(token_endpoint,
                            data=payload_post,
                            headers=headers_post
                            )
    acs_token = token_r.json()['access_token']
    print("Status code for token: ", token_r.status_code)
    return acs_token


def create_spotify_playlist(playlist_name, acs_token, usr_id):
    """
    Create a new playlist on Spotify.
    :param playlist_name: Name of the new playlist (str)
    :param acs_token: Access token for the permission (str)
    :param usr_id: Id of the user (str)
    :return: Id of the newly created playlist
    """
    create_playlist_endpoint = "https://api.spotify.com/v1/users/{}/playlists".format(usr_id)
    payload_post = json.dumps({"name": "{}".format(playlist_name),
                               "description": "This playlist is generated automatically by my youtube-spotify-app"
                               })
    headers_post = {"Accept": "application/json",
                    "Content-Type": "application/json",
                    "Authorization": "Bearer {}".format(acs_token)
                    }
    create_playlist_r = requests.post(create_playlist_endpoint,
                                      data=payload_post,
                                      headers=headers_post
                                      )
    print("Status code for playlist creation: ", create_playlist_r.status_code)
    return create_playlist_r.json()['id']  # playlist id


def search_on_spotify(liked_videos, acs_token):
    """
    Search liked videos on Spotify. Print which liked songs could be found on Spotify as
    songs and which ones couldn't be found.
    :param liked_videos: Liked videos on YouTube (list of strings)
    :param acs_token: Access token for the permission (str)
    :return: list of found songs uri's.
    """
    # An undeniable part of the liked videos
    # are not going to be found since they are basically not songs.
    # Unfound videos should be returned.
    spotify_song_uri = []
    unfound_songs = []
    search_endpoint = "https://api.spotify.com/v1/search"
    for video in liked_videos:
        headers_get = {"Authorization": "Bearer {}".format(acs_token)}
        params_get = {"q": "{}".format(video),
                      "type": "track",
                      "limit": "1"}
        song_search_r = requests.get(
            search_endpoint,
            params=params_get,
            headers=headers_get)
        if not json.loads(song_search_r.text)["tracks"]["items"] == []:  # track returned a result
            spotify_song_uri.append(json.loads(song_search_r.text)["tracks"]["items"][0]["uri"])
        else:
            unfound_songs.append(video)
    print("FOUND SONGS: ")
    pprint.pprint(spotify_song_uri)
    print("UNFOUND SONGS: ")
    pprint.pprint(unfound_songs)
    return spotify_song_uri


def add_songs_to_playlist(acs_token, uris, plylist_id):
    """
    Add found songs in the created playlist.
    :param acs_token: Access token for the permission (str)
    :param uris: List of uri's of the found songs.
    :param plylist_id: Id of the created playlist to add the songs.
    :return: 0
    """
    add_songs_endpoint = "https://api.spotify.com/v1/playlists/{}/tracks".format(plylist_id)
    headers_post = {"Content-Type": "application/json",
                    "Authorization": "Bearer {}".format(acs_token)}
    payload_post = json.dumps({"uris": uris})
    add_songs_r = requests.post(add_songs_endpoint,
                                data=payload_post,
                                headers=headers_post)
    print("Status code for adding the songs: ", add_songs_r.status_code)
    return 0


if __name__ == "__main__":
    liked_vids_on_youtube = get_liked_vids_youtube(10)  # Get permission and liked vids from YouTube
    access_token = get_spotify_auth(client_id)
    playlist_id = create_spotify_playlist("auto-gen-playlist", access_token, user_id)
    found_songs = search_on_spotify(liked_vids_on_youtube, access_token)
    add_songs_to_playlist(access_token, found_songs, playlist_id)
