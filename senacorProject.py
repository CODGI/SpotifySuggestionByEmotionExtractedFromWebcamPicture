import spotipy
from spotipy import util
from spotipy.oauth2 import SpotifyClientCredentials
from json.decoder import JSONDecodeError
from google.cloud.vision import types
from google.cloud import vision
import io
import os
import random
import webbrowser
import cv2
from tkinter import *
import re

username = None


# Get Unsername by TKinter-prompt
def set_username():
    global username
    username = entry.get()
    master.quit()


master = Tk()
Label(master, text="Username").grid(row=0)
entry = Entry(master)
entry.grid(row=0, column=1)
Button(master, text='Submit', command=set_username).grid(row=3, column=1, sticky=W, pady=4)
mainloop()

# Get picture
cam = cv2.VideoCapture(0)
cv2.namedWindow("Look into the camera")
ret, frame = cam.read()
cv2.imwrite("picture.jpg", frame)

# Use Google Cloud Vision API to get most dominant emotion
image_file_name = 'picture.jpg'
client = vision.ImageAnnotatorClient()

with io.open(image_file_name, 'rb') as image_file:
    content = image_file.read()

image = types.Image(content=content)
response = client.face_detection(image=image)

faces = response.face_annotations

likelihood_name = ('UNKNOWN', 'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE',
                   'LIKELY', 'VERY_LIKELY')

for face in faces:
    dominant_emotion = sorted([(face.sorrow_likelihood, 'sorrow'), (face.joy_likelihood, 'joy'),
                               (face.anger_likelihood, 'anger')], key=lambda x: x[0])[2]

# Connect to Spotify API
scope = 'user-top-read'
clientCredentialsFile = open("spotifyClientCredentials.txt", "r")
for line in clientCredentialsFile:
    matchClientId = re.match(r'client_id: (.*)', line)
    matchClientSecret = re.match(r'client_secret: (.*)', line)
    if matchClientId:
        client_id = matchClientId.group(1)
    if matchClientSecret:
        client_secret = matchClientSecret.group(1)

try:
    token = util.prompt_for_user_token(username=username, client_id=str(client_id),
                                       client_secret=str(client_secret),
                                       redirect_uri="http://localhost/", scope=scope)
except (AttributeError, JSONDecodeError):
    os.remove(f".cache-{username}")
    token = util.prompt_for_user_token(username=username, client_id=str(client_id),
                                       client_secret=str(client_secret),
                                       redirect_uri="http://localhost/", scope=scope)

client_credentials_manager = SpotifyClientCredentials(client_id=str(client_id),
                                                      client_secret=str(client_secret))
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth=token)
sp.trace = False
moody_playlists = sp.category_playlists(category_id='mood', limit=50)
metal = sp.category_playlists(category_id='metal')

# Get playlist matching mood and open in browser

playlists = list()

mappings = {'joy': ['Sommergefühle', 'Happy Dance'],
            'anger': ['Kickass Metal', 'New Blood', 'Deathcore'],
            'sorrow': ['Life Sucks', 'Acoustic Covers', 'Alone Again']}


def print_playlist(name, emotion):
    if emotion == 'anger':
        categories = metal['playlists']['items']
    else:
        categories = moody_playlists['playlists']['items']

    for playlist in categories:
        if playlist['name'] != name:
            continue
        print()
        print(playlist['name'])
        print('  total tracks', playlist['tracks']['total'])
        results = sp.user_playlist(username, playlist['id'], fields="tracks,next")
        tracks = results['tracks']
        randomTrack = random.choice(tracks['items'])['track']
        url = randomTrack['preview_url']
        playlist_url = playlist['external_urls']['spotify']
        webbrowser.open(playlist_url)
        webbrowser.open(url)


selected_playlist = random.sample(mappings[dominant_emotion[1]], 1)
print_playlist(selected_playlist[0], dominant_emotion[1])
