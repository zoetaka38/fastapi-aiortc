from aiortc.contrib.media import MediaStreamTrack
from av import VideoFrame


class AudioTransformTrack(MediaStreamTrack):
    """
    An audio stream track that transforms frames from an another track.
    """

    kind = "audio"

    def __init__(self, track):
        super().__init__()  # don't forget this!
        self.track = track

    async def recv(self):
        print(self.track)
        frame = await self.track.recv()
        print(frame)
        return frame


class VideoTransformTrack(MediaStreamTrack):
    """
    A video stream track that transforms frames from an another track.
    """

    kind = "video"

    def __init__(self, track, transform):
        super().__init__()  # don't forget this!
        self.track = track
        self.transform = transform

    async def recv(self):
        print(self.track)
        frame = await self.track.recv()
        print(frame)
        return frame
