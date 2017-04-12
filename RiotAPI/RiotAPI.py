from collections import deque
import time
import requests

# Constants
BRAZIL = 'br'
EUROPE_NORDIC_EAST = 'eune'
EUROPE_WEST = 'euw'
KOREA = 'kr'
LATIN_AMERICA_NORTH = 'lan'
LATIN_AMERICA_SOUTH = 'las'
NORTH_AMERICA = 'na'
OCEANIA = 'oce'
RUSSIA = 'ru'
TURKEY = 'tr'
JAPAN = 'jp'

# Platforms
platforms = {
	BRAZIL: 'BR1',
	EUROPE_NORDIC_EAST: 'EUN1',
	EUROPE_WEST: 'EUW1',
	KOREA: 'KR',
	LATIN_AMERICA_NORTH: 'LA1',
	LATIN_AMERICA_SOUTH: 'LA2',
	NORTH_AMERICA: 'NA1',
	OCEANIA: 'OC1',
	RUSSIA: 'RU',
	TURKEY: 'TR1',
	JAPAN: 'JP1'
}

queue_types = [
	'CUSTOM',  # Custom games
	'NORMAL_5x5_BLIND',  # Normal 5v5 blind pick
	'BOT_5x5',  # Historical Summoners Rift coop vs AI games
	'BOT_5x5_INTRO',  # Summoners Rift Intro bots
	'BOT_5x5_BEGINNER',  # Summoner's Rift Coop vs AI Beginner Bot games
	'BOT_5x5_INTERMEDIATE',  # Historical Summoner's Rift Coop vs AI Intermediate Bot games
	'NORMAL_3x3',  # Normal 3v3 games
	'NORMAL_5x5_DRAFT',  # Normal 5v5 Draft Pick games
	'ODIN_5x5_BLIND',  # Dominion 5v5 Blind Pick games
	'ODIN_5x5_DRAFT',  # Dominion 5v5 Draft Pick games
	'BOT_ODIN_5x5',  # Dominion Coop vs AI games
	'RANKED_SOLO_5x5',  # Ranked Solo 5v5 games
	'RANKED_PREMADE_3x3',  # Ranked Premade 3v3 games
	'RANKED_PREMADE_5x5',  # Ranked Premade 5v5 games
	'RANKED_TEAM_3x3',  # Ranked Team 3v3 games
	'RANKED_TEAM_5x5',  # Ranked Team 5v5 games
	'BOT_TT_3x3',  # Twisted Treeline Coop vs AI games
	'GROUP_FINDER_5x5',  # Team Builder games
	'ARAM_5x5',  # ARAM games
	'ONEFORALL_5x5',  # One for All games
	'FIRSTBLOOD_1x1',  # Snowdown Showdown 1v1 games
	'FIRSTBLOOD_2x2',  # Snowdown Showdown 2v2 games
	'SR_6x6',  # Hexakill games
	'URF_5x5',  # Ultra Rapid Fire games
	'BOT_URF_5x5',  # Ultra Rapid Fire games played against AI games
	'NIGHTMARE_BOT_5x5_RANK1',  # Doom Bots Rank 1 games
	'NIGHTMARE_BOT_5x5_RANK2',  # Doom Bots Rank 2 games
	'NIGHTMARE_BOT_5x5_RANK5',  # Doom Bots Rank 5 games
	'ASCENSION_5x5',  # Ascension games
	'HEXAKILL',  # 6v6 games on twisted treeline
	'KING_PORO_5x5',  # King Poro game games
	'COUNTER_PICK',  # Nemesis games,
	'BILGEWATER_5x5',  # Black Market Brawlers games
]

game_maps = [
	{'map_id': 1, 'name': "Summoner's Rift", 'notes': "Summer Variant"},
	{'map_id': 2, 'name': "Summoner's Rift", 'notes': "Autumn Variant"},
	{'map_id': 3, 'name': "The Proving Grounds", 'notes': "Tutorial Map"},
	{'map_id': 4, 'name': "Twisted Treeline", 'notes': "Original Version"},
	{'map_id': 8, 'name': "The Crystal Scar", 'notes': "Dominion Map"},
	{'map_id': 10, 'name': "Twisted Treeline", 'notes': "Current Version"},
	{'map_id': 11, 'name': "Summoner's Rift", 'notes': "Current Version"},
	{'map_id': 12, 'name': "Howling Abyss", 'notes': "ARAM Map"},
	{'map_id': 14, 'name': "Butcher's Bridge", 'notes': "ARAM Map"},
]

game_modes = [
	'CLASSIC',  # Classic Summoner's Rift and Twisted Treeline games
	'ODIN',  # Dominion/Crystal Scar games
	'ARAM',  # ARAM games
	'TUTORIAL',  # Tutorial games
	'ONEFORALL',  # One for All games
	'ASCENSION',  # Ascension games
	'FIRSTBLOOD',  # Snowdown Showdown games
	'KINGPORO',  # King Poro games
]

game_types = [
	'CUSTOM_GAME',  # Custom games
	'TUTORIAL_GAME',  # Tutorial games
	'MATCHED_GAME',  # All other games
]

sub_types = [
	'NONE',  # Custom games
	'NORMAL',  # Summoner's Rift unranked games
	'NORMAL_3x3',  # Twisted Treeline unranked games
	'ODIN_UNRANKED',  # Dominion/Crystal Scar games
	'ARAM_UNRANKED_5v5',  # ARAM / Howling Abyss games
	'BOT',  # Summoner's Rift and Crystal Scar games played against AI
	'BOT_3x3',  # Twisted Treeline games played against AI
	'RANKED_SOLO_5x5',  # Summoner's Rift ranked solo queue games
	'RANKED_TEAM_3x3',  # Twisted Treeline ranked team games
	'RANKED_TEAM_5x5',  # Summoner's Rift ranked team games
	'ONEFORALL_5x5',  # One for All games
	'FIRSTBLOOD_1x1',  # Snowdown Showdown 1x1 games
	'FIRSTBLOOD_2x2',  # Snowdown Showdown 2x2 games
	'SR_6x6',  # Hexakill games
	'CAP_5x5',  # Team Builder games
	'URF',  # Ultra Rapid Fire games
	'URF_BOT',  # Ultra Rapid Fire games against AI
	'NIGHTMARE_BOT',  # Nightmare bots
	'ASCENSION',  # Ascension games
	'HEXAKILL',  # Twisted Treeline 6x6 Hexakill
	'KING_PORO',  # King Poro games
	'COUNTER_PICK',  # Nemesis games
	'BILGEWATER',  # Black Market Brawlers games
]

player_stat_summary_types = [
	'Unranked',  # Summoner's Rift unranked games
	'Unranked3x3',  # Twisted Treeline unranked games
	'OdinUnranked',  # Dominion/Crystal Scar games
	'AramUnranked5x5',  # ARAM / Howling Abyss games
	'CoopVsAI',  # Summoner's Rift and Crystal Scar games played against AI
	'CoopVsAI3x3',  # Twisted Treeline games played against AI
	'RankedSolo5x5',  # Summoner's Rift ranked solo queue games
	'RankedTeams3x3',  # Twisted Treeline ranked team games
	'RankedTeams5x5',  # Summoner's Rift ranked team games
	'OneForAll5x5',  # One for All games
	'FirstBlood1x1',  # Snowdown Showdown 1x1 games
	'FirstBlood2x2',  # Snowdown Showdown 2x2 games
	'SummonersRift6x6',  # Hexakill games
	'CAP5x5',  # Team Builder games
	'URF',  # Ultra Rapid Fire games
	'URFBots',  # Ultra Rapid Fire games played against AI
	'NightmareBot',  # Summoner's Rift games played against Nightmare AI
	'Hexakill',  # Twisted Treeline 6x6 Hexakill games
	'KingPoro',  # King Poro games
	'CounterPick',  # Nemesis games
	'Bilgewater',  # Black Market Brawlers games
]

solo_queue, ranked_5s, ranked_3s = 'RANKED_SOLO_5x5', 'RANKED_TEAM_5x5', 'RANKED_TEAM_3x3'

preseason_3, season_3, preseason_2014, season_2014, preseason_2015, season_2015, preseason_2016, season_2016 = [
	'PRESEASON3', 'SEASON3',
	'PRESEASON2014', 'SEASON2014',
	'PRESEASON2015', 'SEASON2015',
	'PRESEASON2016', 'SEASON2016',
]

api_versions = {
	'champion': 1.2,
	'championmastery': 3,
	'current-game': 1.0,
	'featured-games': 1.0,
	'game': 1.3,
	'league': 2.5,
	'lol-static-data': 1.2,
	'lol-status': 1.0,
	'match': 2.2,
	'matchlist': 2.2,
	'stats': 1.3,
	'summoner': 1.4,
	'team': 2.4
}

roles = {
	1: 'Top',
	2: 'Middle',
	3: 'Jungle',
	4: 'Bot'
}


class LoLException(Exception):
	def __init__(self, error, response):
		self.error = error
		self.headers = response.headers

	def __str__(self):
		return self.error

	def __eq__(self, other):
		if isinstance(other, "".__class__):
			return self.error == other
		elif isinstance(other, self.__class__):
			return self.error == other.error and self.headers == other.headers
		else:
			return False

	def __ne__(self, other):
		return not self.__eq__(other)

	def __hash__(self):
		return super(LoLException).__hash__()


error_400 = "Bad request"
error_401 = "Unauthorized"
error_403 = "Blacklisted key"
error_404 = "Game data not found"
error_429 = "Too many requests"
error_500 = "Internal server error"
error_503 = "Service unavailable"
error_504 = 'Gateway timeout'


def raise_status(response):
	if response.status_code == 400:
		raise LoLException(error_400, response)
	elif response.status_code == 401:
		raise LoLException(error_401, response)
	elif response.status_code == 403:
		raise LoLException(error_403, response)
	elif response.status_code == 404:
		raise LoLException(error_404, response)
	elif response.status_code == 429:
		raise LoLException(error_429, response)
	elif response.status_code == 500:
		raise LoLException(error_500, response)
	elif response.status_code == 503:
		raise LoLException(error_503, response)
	elif response.status_code == 504:
		raise LoLException(error_504, response)
	else:
		response.raise_for_status()


class RateLimit:
	def __init__(self, allowed_requests, seconds):
		self.allowed_requests = allowed_requests
		self.seconds = seconds
		self.made_requests = deque()

	def __reload(self):
		t = time.time()
		while len(self.made_requests) > 0 and self.made_requests[0] < t:
			self.made_requests.popleft()

	def add_request(self):
		self.made_requests.append(time.time() + self.seconds)

	def request_available(self):
		self.__reload()
		return len(self.made_requests) < self.allowed_requests


class RiotAPI:

	def __init__(self, key, default_region=NORTH_AMERICA, limits=(RateLimit(10, 10), RateLimit(500, 600), )):
		self.key = key
		self.default_region = default_region
		self.limits = limits

	def can_make_request(self):
		for lim in self.limits:
			if not lim.request_available():
				return False
		return True

	#generic request
	def base_request(self, url, region, static=False, **kwargs):
		if region is None:
			region = self.default_region

		args = {'api_key': self.key}

		for k in kwargs:
			if kwargs[k] is not None:
				args[k] = kwargs[k]

		r = requests.get(
			'https://{proxy}.api.pvp.net/api/lol/{static}{region}/{url}'.format(
				proxy='global' if static else region,
				static='static-data/' if static else '',
				region=region,
				url=url
			),
			params=args
		)

		if not static:
			for lim in self.limits:
				lim.add_request()

		raise_status(r)
		return r.json()

	def get_champion_mastery(self, summoner_id, champion_id, region=None):
		if region is None:
			region = self.default_region

		args = {'api_key': self.key}

		url = 'https://{region}.api.riotgames.com/lol/champion-mastery/v{version}/champion-masteries/by-summoner/{summoner_id}/by-champion/{champion_id}'.format(
				region=region,
				version=api_versions['championmastery'],
				summoner_id=summoner_id,
				champion_id=champion_id
			)
		url += '?'
		for key, value in args.items():
			url += key + "=" + value + "&"

		url.strip('&')

		r = requests.get(
			url,
			params=args
		)

		for lim in self.limits:
			lim.add_request()

		raise_status(r)
		return r.json()

	def _observer_mode_request(self, url, proxy=None, **kwargs):
		if proxy is None:
			proxy = self.default_region

		args = {'api_key': self.key}

		for k in kwargs:
			if kwargs[k] is not None:
				args[k] = kwargs[k]

		r = requests.get(
			'https://{proxy}.api.pvp.net/observer-mode/rest/{url}'.format(
				proxy=proxy,
				url=url
			),
			params=args
		)

		for lim in self.limits:
			lim.add_request()

		raise_status(r)
		return r.json()

	# current-game-v1.0
	def get_current_game(self, summoner_id, platform_id=None, region=None):
		if platform_id is None:
			platform_id = platforms[self.default_region]

		return self._observer_mode_request(
			'consumer/getSpectatorGameInfo/{platform}/{summoner_id}'.format(
				platform=platform_id,
				summoner_id=summoner_id
			),
			region
		)

	# summoner-v1.4
	def _summoner_request(self, end_url, region=None, **kwargs):
		return self.base_request(
			'v{version}/summoner/{end_url}'.format(
				version=api_versions['summoner'],
				end_url=end_url
			),
			region,
			**kwargs
		)

	def get_summoner_id(self, summoner_id, region=None):
		if not summoner_id.isdigit():
			response = self._summoner_request('by-name/{}'.format(summoner_id), region)
			summoner_id = response[summoner_id.replace(' ', '').lower()]['id']
		return summoner_id

	# match-v2.2
	def _match_request(self, end_url, region, **kwargs):
		return self.base_request(
			'v{version}/match/{end_url}'.format(
				version=api_versions['match'],
				end_url=end_url
			),
			region,
			**kwargs
		)

	def get_match(self, match_id, region=None, include_timeline=False):
		return self._match_request(
			'{match_id}'.format(match_id=match_id),
			region,
			includeTimeline=include_timeline
		)

	# game-v1.3
	def _game_request(self, end_url, region=None, **kwargs):
		return self.base_request(
			'v{version}/game/{end_url}'.format(
				version=api_versions['game'],
				end_url=end_url
			),
			region,
			**kwargs
		)

	def get_recent_games(self, summoner_id, region=None):
		return self._game_request('by-summoner/{summoner_id}/recent'.format(summoner_id=summoner_id), region)

	# lol-status-v1.0
	@staticmethod
	def get_server_status(region=None):
		if region is None:
			url = 'shards'
		else:
			url = 'shards/{region}'.format(region=region)

		r = requests.get('http://status.leagueoflegends.com/{url}'.format(url=url))

		raise_status(r)
		return r.json()

	# lol-static-data-v1.2
	def _static_request(self, end_url, region=None, **kwargs):
		return self.base_request(
			'v{version}/{end_url}'.format(
				version=api_versions['lol-static-data'],
				end_url=end_url
			),
			region,
			static=True,
			**kwargs
		)

	def static_get_champion_list(self, region=None, locale=None, version=None, data_by_id=None, champ_data=None):
		return self._static_request(
			'champion',
			region,
			locale=locale,
			version=version,
			dataById=data_by_id,
			champData=champ_data
		)

	def static_get_champion(self, champ_id, region=None, locale=None, version=None, champ_data=None):
		return self._static_request(
			'champion/{id}'.format(id=champ_id),
			region,
			locale=locale,
			version=version,
			champData=champ_data
		)

	def static_get_item_list(self, region=None, locale=None, version=None, item_list_data=None):
		return self._static_request('item', region, locale=locale, version=version, itemListData=item_list_data)

	def static_get_item(self, item_id, region=None, locale=None, version=None, item_data=None):
		return self._static_request(
			'item/{id}'.format(id=item_id),
			region,
			locale=locale,
			version=version,
			itemData=item_data
		)

	def static_get_mastery_list(self, region=None, locale=None, version=None, mastery_list_data=None):
		return self._static_request(
			'mastery',
			region,
			locale=locale,
			version=version,
			masteryListData=mastery_list_data
		)

	def static_get_mastery(self, mastery_id, region=None, locale=None, version=None, mastery_data=None):
		return self._static_request(
			'mastery/{id}'.format(id=mastery_id),
			region,
			locale=locale,
			version=version,
			masteryData=mastery_data
		)

	def static_get_rune_list(self, region=None, locale=None, version=None, rune_list_data=None):
		return self._static_request('rune', region, locale=locale, version=version, runeListData=rune_list_data)

	def static_get_rune(self, rune_id, region=None, locale=None, version=None, rune_data=None):
		return self._static_request(
			'rune/{id}'.format(id=rune_id),
			region,
			locale=locale,
			version=version,
			runeData=rune_data
		)

	def static_get_summoner_spell_list(self, region=None, locale=None, version=None, data_by_id=None, spell_data=None):
		return self._static_request(
			'summoner-spell',
			region,
			locale=locale,
			version=version,
			dataById=data_by_id,
			spellData=spell_data
		)

	def static_get_summoner_spell(self, spell_id, region=None, locale=None, version=None, spell_data=None):
		return self._static_request(
			'summoner-spell/{id}'.format(id=spell_id),
			region,
			locale=locale,
			version=version,
			spellData=spell_data
		)