import asyncio
import logging
import secrets
import uuid

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRelay
from fastapi import FastAPI, Request
from fastapi.openapi.docs import HTMLResponse
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app import exception_handler
from app.my_media_transform_check import AudioTransformTrack, VideoTransformTrack
from app.settings import Settings

settings = Settings()
security = HTTPBasic()
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# 例外ハンドラの登録
exception_handler.init_app(app)

# このアプリケーションのログ設定
root_logger = logging.getLogger("app")
root_logger.addHandler(logging.StreamHandler())
root_logger.setLevel(settings.LOG_LEVEL)

pcs = set()
relay = MediaRelay()


@app.get("/", include_in_schema=False)
async def index(
    request: Request,
) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health", include_in_schema=False)
def health() -> JSONResponse:
    """ヘルスチェック"""
    return JSONResponse({"message": "It worked!!"})


@app.get("/offer", include_in_schema=False)
@app.post("/offer", include_in_schema=False)
async def offer(request: Request):
    params = await request.json()
    offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

    pc = RTCPeerConnection()
    pc_id = "PeerConnection(%s)" % uuid.uuid4()
    pcs.add(pc)

    def log_info(msg, *args):
        root_logger.info(pc_id + " " + msg, *args)

    # player = MediaPlayer("/usr/src/app/app/demo-instruct.wav")
    recorder = MediaBlackhole()

    @pc.on("datachannel")
    def on_datachannel(channel):
        @channel.on("message")
        def on_message(message):
            if isinstance(message, str) and message.startswith("ping"):
                channel.send("pong" + message[4:])

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log_info("Connection state is %s", pc.connectionState)
        if pc.connectionState == "failed":
            await pc.close()
            pcs.discard(pc)

    @pc.on("track")
    def on_track(track):
        log_info("Track {} received".format(track.kind))

        if track.kind == "audio":
            pc.addTrack(AudioTransformTrack(relay.subscribe(track)))
            # recorder.addTrack(track)
            # recorder.addTrack(player.audio)
        elif track.kind == "video":
            # pc.addTrack(relay.subscribe(track))
            pc.addTrack(VideoTransformTrack(relay.subscribe(track), transform=""))
            # recorder.addTrack(relay.subscribe(track))

        @track.on("ended")
        async def on_ended():
            log_info("Track %s ended", track.kind)
            await recorder.stop()

    # handle offer
    await pc.setRemoteDescription(offer)
    await recorder.start()

    # send answer
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return JSONResponse(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
    )


@app.on_event("shutdown")
async def on_shutdown():
    # close peer connections
    coros = [pc.close() for pc in pcs]
    await asyncio.gather(*coros)
    pcs.clear()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
