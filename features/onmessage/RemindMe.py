from datetime import timedelta

from features.onmessage.OnMessageFeature import OnMessageFeature
from util.DateTimeUtils import now, pretty_date_format, prettify_seconds
from util.LoggingUtils import get_logger
from util.MessagingUtils import respond, koffing_reaction, delayed_response
from util.TaskUtils import create_task
from util.UserUtils import get_discriminating_name


logger = get_logger()


async def create_reminder(message):
	logger.info('Generating reminder for %s...', get_discriminating_name(message.author))

	# ['/remindme', 'time', 'message']
	contents = message.content.split(maxsplit=2)
	if len(contents) < 3:
		await respond(message, "Skronk!", emote="x")
		return

	remind_time = contents[1]
	# Check for units on end of string
	if not remind_time.replace(".", "", 1).isdigit():
		if remind_time.endswith('h'):
			remind_time = str(float(remind_time[:-1]) * 3600)
		if remind_time.endswith('m'):
			remind_time = str(float(remind_time[:-1]) * 60)
		elif remind_time.endswith('s'):
			remind_time = str(float(remind_time[:-1]) * 1)
		if not remind_time.replace(".", "", 1).isdigit():
			await respond(message, "Skronk!", emote="x")
			return

	current_time = now()
	wakeup = (current_time + timedelta(seconds=int(float(remind_time)))).strftime(pretty_date_format)

	# Respond based on the length of time to wait
	# TODO - should we even bother with a text response here?
	await respond(message, "Alright, reminding you at {}".format(wakeup))

	if message.guild is not None:
		await koffing_reaction(message)

	create_task(
		delayed_response(
			message,
			"This is your reminder from {}:\n\n{}".format(current_time, contents[2]),
			remind_time
		)
	)

	logger.info('Reminder generated for %s in %s (%s)',
				get_discriminating_name(message.author),
				prettify_seconds(remind_time),
				wakeup
				)


class RemindMe(OnMessageFeature):
	"""
	Basic remindme functionality, works for seconds or minutes
	"""

	def __init__(self, client):
		super().__init__(client)
		self.command_str = "remindme"

	async def execute(self, *args):
		await create_reminder(args[0])
