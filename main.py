import datetime
import re
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from bs4 import BeautifulSoup

scope = "user-library-read,playlist-modify-private,playlist-modify-public,user-top-read"

spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
queryUrl = "https://www.setlist.fm/search?query="

artistName = input("Enter a band name: ")
playlistName = input("Enter playlist name (new or not): ")

# Form artist setlist search URL
artistNameSplit = re.split('\s+', artistName)
for word in artistNameSplit:
    if word is artistNameSplit[0]:
        queryUrl += word
    else:
        queryUrl += "+" + word

# Execute GET-Request
response = requests.get(queryUrl)
# Get HTML
html = BeautifulSoup(response.text, 'html.parser')
# Get Artist ID
artistSetlistFullId = html.find_all('ul', class_="list-unstyled")[0].contents[1].contents[1].attrs['href']
artistSetlistFullId = re.split("setlists/", artistSetlistFullId)[1]

# Get the latest year average setlist
year = datetime.date.today().year
year_str = str(year)

try:
    averageSetlistCurrentYearURL = "https://www.setlist.fm/stats/average-setlist/" + artistSetlistFullId + "?year=" + year_str
    averageSetlistResponse = requests.get(averageSetlistCurrentYearURL)
    averageSetlistHTML = BeautifulSoup(averageSetlistResponse.text, 'html.parser')
    averageSetlistSongsHTML = averageSetlistHTML.find_all('div', class_="setlistList")[0].contents[1].contents
except IndexError:
    # In case no average list for current year is available, try with the previous one (should be available)
    year_str = str(year-1)
    averageSetlistCurrentYearURL = "https://www.setlist.fm/stats/average-setlist/" + artistSetlistFullId + "?year=" + year_str
    averageSetlistResponse = requests.get(averageSetlistCurrentYearURL)
    averageSetlistHTML = BeautifulSoup(averageSetlistResponse.text, 'html.parser')
    averageSetlistSongsHTML = averageSetlistHTML.find_all('div', class_="setlistList")[0].contents[1].contents

# Add song names to setlist
averageSetlist = []
for song in averageSetlistSongsHTML:
    if song != "\n":
        try:
            if 'song' in song.attrs['class']:
                averageSetlist.append(song.contents[1].contents[1].contents[0])
        except IndexError:
            print("Warning adding song")

# Check if playlist already exists
currentUserPlaylists = spotify.current_user_playlists()
livePlaylist = ""
for userPlaylist in currentUserPlaylists['items']:
    if userPlaylist['name'] == playlistName:
        livePlaylist = userPlaylist['id']
        break

# Create playlist if it does not exist
if not livePlaylist:
    userResults = spotify.current_user()
    user_id = userResults['id']
    livePlaylist = spotify.user_playlist_create(user=f"{user_id}", name=playlistName)['id']

# Add average setlist tracks to playlist
for track in averageSetlist:
    track = track.replace("'", "")
    # Search for the track in spotify
    trackResults = spotify.search(q=f"artist:{artistName} track:{track}", type="track")

    livePlaylistsUris = []
    # Select the proper song in the search result
    for trackResult in trackResults['tracks']['items']:
        if trackResult['name'] == track:
            livePlaylistsUris = [trackResult['uri']]
            break

    if not livePlaylistsUris:
        try:
            livePlaylistsUris = [trackResults['tracks']['items'][0]['uri']]
        except IndexError:
            print(f"Could not add song {track}")

    # Add the track in the playlist
    if livePlaylistsUris:
        spotify.playlist_add_items(livePlaylist, livePlaylistsUris)

print("Tracks added succesfully")
