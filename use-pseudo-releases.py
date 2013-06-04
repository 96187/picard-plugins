PLUGIN_NAME = 'Fetch latin script tracklists from pseudo-releases'
PLUGIN_AUTHOR = ''
PLUGIN_DESCRIPTION = '''Fetch latin script tracklists from pseudo-releases'''
PLUGIN_VERSION = '0.1'
PLUGIN_API_VERSIONS = ['0.12', '0.15', '0.16', '1.1']

from picard.metadata import register_album_metadata_processor, register_track_metadata_processor
from picard.album import Album
from picard.util import partial
from picard.mbxml import release_to_metadata, artist_credit_from_node
from PyQt4.QtCore import QUrl
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
			album.log.error("%r", unicode(http.errorString()))
		else:
			try:
				release_node = document.metadata[0].release[0]
				if release_node.text_representation[0].script[0].text != script:
					return

				album_latin = release_node.title[0].text
				metadata["album"] = album_latin
				tracks['album'] = album_latin

				artistcredit, tmp = artist_credit_from_node(release_node.artist_credit[0], config)
				metadata["albumartist"] = artistcredit
				tracks["artist"] = artistcredit

				mediumpos = 1
				tracks["mediums"] = {}
				for i, node in enumerate(release_node.medium_list[0].medium):
					try:
						tracks["mediums"][ mediumpos ] = release_node.medium_list[0].medium[i].title[0].text
					except: pass

					tracks[mediumpos] = {}
					trackpos = 1
					for j, node in enumerate(release_node.medium_list[0].medium[i].track_list[0].track):
						title = ""
						try:
							title = node.title[0].text
						except:
							title = node.recording[0].title[0].text

						tartist = ""
						try:
							tartist, tmp = artist_credit_from_node(node.artist_credit[0], config)
						except:
							tartist, tmp = artist_credit_from_node(node.recording[0].artist_credit[0], config)

						tracks[ mediumpos ][ trackpos ] = {};
						tracks[ mediumpos ][ trackpos ]["artist"] = tartist

						tracks[ mediumpos ][ trackpos ]["title"] = title;
						tracks[ mediumpos ][ trackpos ]["mbid"] = node.recording[0].id;

						trackpos = trackpos + 1
					mediumpos = mediumpos + 1
			except:
				error = True
				album.log.error("some error occurred :(")
	finally:
		album._requests -= 1
		album._finalize_loading(None)

def fetch_transliterations(album, metadata, release_node):
	global tracks
	tracks = {}
	tracks['has_transliteration'] = False

	if metadata['releasestatus'] != 'pseudo-release' and metadata['script'] != script:
		if release_node.children.has_key('relation_list'):
			for relation_list in release_node.relation_list:
				if relation_list.target_type == 'release':
					for relation in relation_list.relation:
						try:
							direction = relation.direction if hasattr(relation, 'direction') else ''
							if (relation.type == 'transl-tracklisting' and direction != 'backward'):
								album._requests += 1
								album.tagger.xmlws.get_release_by_id(relation.target[0].text,
									partial(_pseudo_release_downloaded, album, metadata, relation.target[0].text),
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
		if tracks[ int(metadata['discnumber']) ][ int(metadata['tracknumber']) ]["mbid"] == metadata["musicbrainz_trackid"]:
			metadata['title'] = tracks[ int(metadata['discnumber']) ][ int(metadata['tracknumber']) ]["title"]
		else:
			tagger.log.error("MBID for %s (%s) does not match MBID for %s (%s).", tracks[ int(metadata['discnumber']) ][ int(metadata['tracknumber']) ]["title"], tracks[ int(metadata['discnumber']) ][ int(metadata['tracknumber']) ]["mbid"], metadata['title'], metadata["musicbrainz_trackid"])
	except: pass

register_track_metadata_processor(set_transliterations)

