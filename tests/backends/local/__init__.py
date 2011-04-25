from mopidy.utils.path import path_to_uri

from tests import path_to_data_dir

song = path_to_data_dir('song%s.wav')
generate_song = lambda i: path_to_uri(song % i)
