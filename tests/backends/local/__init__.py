from mopidy.utils.path import path_to_uri

from tests import data_folder

song = data_folder('song%s.wav')
generate_song = lambda i: path_to_uri(song % i)
