import google_auth_oauthlib.flow
import googleapiclient.discovery
import os
import pprint

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
        credentials = flow.run_local_server(authorization_prompt_message="", redirect_uri_trailing_slash=False)
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

if __name__ == "__main__":
    get_youtube_client()