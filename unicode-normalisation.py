PLUGIN_NAME = 'NFC/NFD functions'
PLUGIN_AUTHOR = ''
PLUGIN_DESCRIPTION = 'Adds $nfc(text) and $nfd(text) functions for converting strings to NFC or NFD'
PLUGIN_VERSION = "0.1"
PLUGIN_API_VERSIONS = ["1.0"]

from picard.script import register_script_function
import unicodedata

def nfc(parser, text, *prefixes):
	return unicodedata.normalize("NFC", text)

def nfd(parser, text, *prefixes):
	return unicodedata.normalize("NFD", text)

register_script_function(nfc)
register_script_function(nfd)

