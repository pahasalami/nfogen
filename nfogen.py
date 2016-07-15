#!/bin/python2.7
import sys
import logging
import os
from datetime import timedelta
from string import Template as tpl

import discogs_client
from hsaudiotag import auto as hs

logging.basicConfig(format='%(asctime)-15s %(filename)s %(levelname)s %(message)s', level=logging.INFO)

# get your developer key at https://www.discogs.com/settings/developers
# if developer key is not set the script will use the first tracks metadata as default values
discogs_token = ''

file_extensions = ['.mp3', '.flac']
bitrates = {'Lossless': 900, 'CBR': 320, 'V0 (VBR)': 245, 'V2 (VBR)': 190}

folder = sys.argv[1]
discogs = discogs_client.Client('nfogen/1.0 +https://github.com/pahasalami/nfogen', user_token=discogs_token)

if os.path.exists(folder) is False:
    raise IOError('Folder "' + folder + '" does not exist.')

_tracks = []
for filename in os.listdir(folder):
    if os.path.splitext(filename)[1] not in file_extensions:
        logging.warn('{0} is not a valid file extension, skipping.'.format(os.path.splitext(filename)[1]))
        continue

    tags = hs.File(os.path.join(folder, filename))
    _tracks.append(tags)

_bitrate = sum(f.bitrate for f in _tracks) / len(_tracks)
logging.info('Average bitrate of {0} files is {1} kbps.'.format(len(_tracks), _bitrate))

_bitrate_literal, v = min(bitrates.items(), key=lambda (_, b): abs(b - _bitrate))
logging.info('Nearest predefined bitrate quality is "{0}" at {1} kbps'.format(_bitrate_literal, v))

_tracklist = []
for track in _tracks:
    _tracklist.append('{0}. {1:<54} ({2})'.format(track.track, (track.artist + ' - ' + track.title),
                                                  str(timedelta(seconds=track.duration))))

try:
    metadata = discogs.search("{0}".format(_tracks[0].album), type='release')[0]
    artist = metadata.artists[0].name
    title = metadata.title
    genre = ', '.join(metadata.genres)
    style = ', '.join(metadata.styles)
except (IndexError, discogs_client.exceptions.HTTPError):
    logging.error('Unable to retrieve release data from discogs. Using track 0 as default values.')
    artist = _tracks[0].artist
    title = _tracks[0].album
    genre = 'Psytrance'
    style = 'Psytrance'

with file('default.tpl', 'r') as _file:
    _template = tpl(_file.read())
    _output = _template.substitute({'artist': artist or "none",
                                    'album': title or 'none',
                                    'genre': genre or 'none',
                                    'style': style or 'none',
                                    'bitrate': _bitrate or 'none',
                                    'bitrate_literal': _bitrate_literal or 'none',
                                    'tracklist': '\n'.join(_tracklist) or 'none'})

with file(os.path.basename(os.path.normpath(folder) + '.nfo'), 'w') as _file:
    _file.write(_output)

logging.info('Wrote file "{0}" to working directory.'.format(os.path.basename(os.path.normpath(folder) + '.nfo')))
