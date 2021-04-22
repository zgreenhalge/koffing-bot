from features.AbstractFeature import AbstractFeature


class BackgroundFeature(AbstractFeature):

	def __init__(self, client):
		super().__init__(client)
		self.stopping = False
		self.stopped = False
