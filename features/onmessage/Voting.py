from datetime import timedelta
from time import strptime

from features.onmessage.OnMessageFeature import OnMessageFeature
from util.DateTimeUtils import date_to_string, now, string_to_date, pretty_date_format
from util.MessagingUtils import respond, get_mentioned
from util.Settings import enabled, cmd_prefix, votes
from util.UserUtils import get_discriminating_name, get_pretty_name


def get_current_votes():
	"""
	Get the votes map for the current session
	"""
	current = now().date()
	for start in votes:
		if current - string_to_date(start) < timedelta(7):
			return votes[start], start
	return None, None


class Voting(OnMessageFeature):

	def __init__(self, client):
		super().__init__(client)
		self.command_str = "vote"

	async def execute(self, *args):
		message = args[0]

		if not enabled['voting']:
			await respond(message, "Voting is not enabled", emote="x")
		else:
			# check vote timeout & reset if needed
			content = message.content.replace(cmd_prefix + 'vote', '', 1).lstrip().rstrip()
			if content.startswith('leaderboard') or content.startswith('boards') or content.startswith(
					'leaders') or content.startswith('results'):
				await respond(message, self.get_vote_leaderboards(message.guild, message.author), True)
			elif content.startswith('history'):
				await respond(message, self.get_vote_history(message.guild), True)
			else:
				await self.place_vote(message)

	async def place_vote(self, message):
		"""
		Adds a vote for @member or @role or @everyone
		"""
		self.logger.info('Tallying votes...')

		if len(message.mentions) == 0 and len(message.role_mentions) == 0 and not message.mention_everyone:
			await respond(message, "Tag someone to vote for them!", emote="x")
			return

		vote_getters = get_mentioned(message)
		voted_for_self = False
		names = ''
		for member in vote_getters:
			name = get_discriminating_name(member)

			if member.id == message.author.id:
				await respond(message, cmd_prefix + "skronk {} for voting for yourself...".format(
					message.author.mention),
							  True)
				voted_for_self = True
				continue  # cannot vote for yourself

			names += member.mention + ", "
			cur_votes, start_time = get_current_votes()
			if cur_votes is None:
				cur_votes = {name: 1}
				votes[date_to_string(now().date())] = cur_votes
			else:
				if name in cur_votes:
					cur_votes[name] = cur_votes[name] + 1
				else:
					cur_votes[name] = 1
				votes[start_time] = cur_votes

		names = names.rstrip(', ')
		if len(names) > 0:
			await respond(message,
						  'Congratulations {}! You got a vote!{}'
							.format(names, self.get_vote_leaderboards(message.guild, message.author, False))
						  )
		elif not voted_for_self:
			await respond(message,
						  "You didn't tag anyone you can vote for {}"
						  	.format(message.author.mention),
						  emote="x")

	def get_vote_leaderboards(self, guild, requester, call_out=True):
		"""
		Returns a string of the current vote leaderboard
		"""
		self.logger.info('Compiling vote leaderboards...')
		guild_leaders = []
		cur_votes, start = get_current_votes()
		if cur_votes is None:
			return 'No one in {} has received any votes!'.format(guild.name)

		for user_name in cur_votes:
			member = guild.get_member_named(user_name)
			if member is not None:
				guild_leaders.append((member, cur_votes[user_name]))

		if len(guild_leaders) == 0:
			return 'No one in {} has received any votes!'.format(guild.name)

		sorted_ch_lead = sorted(guild_leaders, key=lambda tup_temp: tup_temp[1], reverse=True)

		leaders = []
		idx = 0
		score = sorted_ch_lead[idx][1]
		top_score = score

		while score == top_score:
			member = sorted_ch_lead[idx][0]
			if member is not None:
				leaders.append(member)
			idx = idx + 1
			if len(sorted_ch_lead) > idx:
				score = sorted_ch_lead[idx][1]
			else:
				score = -1

		string = ""
		if len(leaders) > 1:
			for member in leaders:
				string += member.mention + ', '
			string = string.rstrip(', ')
			string = ', and '.join(string.rsplit(', ', 1))
			leader_str = "It's a tie between {}!".format(string)
		else:
			leader_str = "{} is in the lead!".format(leaders[0].mention)

		leaderboard_str = '\n \nLeaderboard for the week starting on {}:\n\n{}```'.format(start[0:-12], leader_str)
		for tup in sorted_ch_lead:
			leaderboard_str += '{}: {}'.format(get_pretty_name(tup[0]), tup[1])
			if requester.name == tup[0].name and call_out:
				leaderboard_str += '<-- It\'s you!\n'
			else:
				leaderboard_str += '\n'
		leaderboard_str += '```'
		return leaderboard_str

	def get_vote_history(self, guild):
		"""
		Returns a string of all the winners of each recorded voting session
		"""
		self.logger.info('Compiling vote winners...')

		leaders = []
		cur_votes, start = get_current_votes()
		for date in votes:
			if string_to_date(date) < string_to_date(start) \
					and string_to_date(date) - string_to_date(start) > timedelta(-8):
				if len(votes[date]) > 0:
					sorted_users = sorted(votes[date], key=lambda tup_temp: tup_temp[1], reverse=False)
					idx = 0
					top_score = votes[date][sorted_users[idx]]
					username = sorted_users[idx]
					score = votes[date][username]

					while score == top_score:
						member = guild.get_member_named(username)
						if member is not None:
							leaders.append([date, member, score])
						idx = idx + 1
						if len(sorted_users) > idx:
							username = sorted_users[idx]
							score = votes[date][username]
						else:
							score = -1

		history_str = 'All-time voting history:```'
		current_date = None

		if len(leaders) == 0:
			history_str = "This guild has no vote winners..."
		else:
			leaders = sorted(leaders, key=lambda tup_temp: strptime(tup_temp[0], pretty_date_format))
			for tup in leaders:
				if tup[0] != current_date:
					current_date = tup[0]
					history_str += '\n{} - {}: {}'.format(tup[0], get_pretty_name(tup[1]), tup[2])
				else:
					history_str += '\n             {}: {}'.format(get_pretty_name(tup[1]), tup[2])
			history_str += '```'

		return history_str