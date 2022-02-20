PLUGIN_NAME = 'Fetch latin script tracklists using translation/transliteration relationships'
PLUGIN_AUTHOR = ''
PLUGIN_DESCRIPTION = '''Fetch latin script tracklists using translation/transliteration relationships'''
PLUGIN_VERSION = '0.2'
PLUGIN_API_VERSIONS = ['2.0', '2.1', '2.2', '2.3', '2.4', '2.5', '2.6', '2.7']

from functools import partial
from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
from picard.mbjson import artist_credit_from_node
from picard.config import Config

script = "Latn"
tracks = {}
config = Config()

def _pseudo_release_downloaded(album, metadata, original_id, document, http, error):
	global tracks
	tracks = {}
	tracks['has_transliteration'] = True

	try:
		if error:
			album.log.error("%r", http.errorString())
		else:
			try:
				if document["text-representation"]["script"] != script:
					return

				album_latin = document["title"]
				metadata["album"] = album_latin
				tracks['album'] = album_latin

				artistcredit, _, _, _ = artist_credit_from_node(document['artist-credit'])
				metadata["albumartist"] = artistcredit
				tracks["artist"] = artistcredit

				mediumpos = 1
				tracks["mediums"] = {}
				for medium in document["media"]:
					mediumpos = medium["position"]
					try:
						tracks["media"][mediumpos] = medium["title"]
					except: pass

					tracks[mediumpos] = {}
					for track in medium["tracks"]:
						trackpos = track["position"]
						title = ""
						try:
							title = track["title"]
						except:
							title = track["recording"]["title"]

						tartist = ""
						try:
							tartist, _, _, _ = artist_credit_from_node(track["artist-credit"])
						except:
							tartist, _, _, _ = artist_credit_from_node(track["recording"]["artist-credit"])

						tracks[mediumpos][trackpos] = {}
						tracks[mediumpos][trackpos]["artist"] = tartist

						tracks[mediumpos][trackpos]["title"] = title
						tracks[mediumpos][trackpos]["mbid"] = track["recording"]["id"]
			except Exception as e:
				error = True
				album.log.error("some error occurred: %s", e)
	finally:
		album._requests -= 1
		album._finalize_loading(None)

def fetch_transliterations(album, metadata, release):
	global tracks
	tracks = {}
	tracks['has_transliteration'] = False

	if metadata['releasestatus'] != 'pseudo-release' and metadata['script'] != script:
		for relation in release['relations']:
			if relation['target-type'] == 'release':
				try:
					direction = relation.get('direction', '')
					if (relation["type"] == 'transl-tracklisting' and direction != 'backward'):
						album._requests += 1
						album.tagger.mb_api.get_release_by_id(relation['release']['id'],
							partial(_pseudo_release_downloaded, album, metadata, relation['release']['id']),
							['recordings', 'artist-credits'])
				except AttributeError: pass

register_album_metadata_processor(fetch_transliterations)

def set_transliterations(tagger, metadata, track, release):
	global tracks
	if tracks['has_transliteration'] == False:
		return

	try:
		metadata['discsubtitle'] = tracks["mediums"][ int(metadata['discnumber']) ]
	except: pass

	try:
		metadata["artist"] = tracks[ int(metadata['discnumber']) ][ int(metadata['tracknumber']) ]["artist"]
	except: pass
	metadata["albumartist"] = tracks["artist"]
	try:
		if tracks[ int(metadata['discnumber']) ][ int(metadata['tracknumber']) ]["mbid"] == metadata["musicbrainz_recordingid"]:
			metadata['title'] = tracks[ int(metadata['discnumber']) ][ int(metadata['tracknumber']) ]["title"]
		else:
			tagger.log.error("MBID for %s (%s) does not match MBID for %s (%s).", tracks[ int(metadata['discnumber']) ][ int(metadata['tracknumber']) ]["title"], tracks[ int(metadata['discnumber']) ][ int(metadata['tracknumber']) ]["mbid"], metadata['title'], metadata["musicbrainz_trackid"])
	except: pass

register_track_metadata_processor(set_transliterations)

