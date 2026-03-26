"""
작혼(Majsoul) 패보 API 클라이언트
- 하드코딩 자격증명 제거 → 환경변수 사용
- 로깅 개선 (print → logger)
"""
import asyncio
import hashlib
import hmac
import logging
import os
import random
import uuid
from datetime import datetime

import websockets
import aiohttp
import json
import re

from src.ms.base import MSRPCChannel
from src.ms.rpc import Lobby
import src.ms.protocol_pb2 as pb
from google.protobuf.json_format import MessageToJson

from src.rp.cfg import cfg
from src.rp.constants import RUNES, JPNAME
from src.rp.parser import MajsoulPaipuParser

logger = logging.getLogger(__name__)

# ============================================================
# [보안 개선] 자격증명을 환경변수에서 로드
# Cloud Run 배포 시: GCP Secret Manager → 환경변수 주입
# ============================================================
MS_HOST = os.getenv("MS_HOST", "https://game.maj-soul.com")
MS_USERNAME = os.getenv("MS_USERNAME")
MS_PASSWORD = os.getenv("MS_PASSWORD")


def _check_credentials():
    """자격증명이 설정되어 있는지 확인"""
    if not MS_USERNAME or not MS_PASSWORD:
        raise RuntimeError(
            "MS_USERNAME, MS_PASSWORD 환경변수가 설정되어야 합니다. "
            ".env.example 파일을 참고하세요."
        )


async def get_game_log(log_uuid):
    """패보 UUID로 게임 로그를 가져옴"""
    _check_credentials()
    logger.info("Fetching game log: %s", log_uuid)

    lobby, channel, version_to_force = await connect()
    try:
        await login(lobby, MS_USERNAME, MS_PASSWORD, version_to_force)
        game_log = await load_and_process_game_log(lobby, log_uuid, version_to_force)
    finally:
        await channel.close()

    if game_log and game_log.get("log") is not None:
        return game_log
    return None


async def connect():
    async with aiohttp.ClientSession() as session:
        async with session.get("{}/1/version.json".format(MS_HOST)) as res:
            version = await res.json()
            version = version["version"]
            version_to_force = version.replace(".w", "")

        async with session.get("{}/1/v{}/config.json".format(MS_HOST, version)) as res:
            config = await res.json()
            gateways = [g["url"] for g in config["ip"][0]["gateways"]]
            url = random.choice(gateways)
            server = re.sub(r'^(?:https?|wss?)://', '', url).rstrip('/')
            endpoint = "wss://{}/gateway".format(server)

    channel = MSRPCChannel(endpoint)
    lobby = Lobby(channel)
    await channel.connect(MS_HOST)
    logger.info("Majsoul Server Connection was established")

    return lobby, channel, version_to_force


async def login(lobby, username, password, version_to_force):
    uuid_key = str(uuid.uuid1())
    req = pb.ReqLogin()
    req.account = username
    req.password = hmac.new(b"lailai", password.encode(), hashlib.sha256).hexdigest()
    req.device.is_browser = True
    req.random_key = uuid_key
    req.gen_access_token = True
    req.client_version_string = f"web-{version_to_force}"
    req.currency_platforms.append(2)

    res = await lobby.login(req)
    token = res.access_token
    if not token:
        logger.error("Login Error: %s", res)
        return False

    logger.info("Majsoul Login Success")
    return True


async def load_and_process_game_log(lobby, uuid, version_to_force):
    logger.info("Loading Game Log ...")

    req = pb.ReqGameRecord()
    req.game_uuid = uuid
    req.client_version_string = f"web-{version_to_force}"
    res = await lobby.fetch_game_record(req)

    return _handle_game_record(res)


def _handle_game_record(record):
    res = {}
    ruledisp = ""
    lobby = ""
    nplayers = len(record.head.result.players)
    nakas = nplayers - 1
    tsumoloss_off = False

    res["ver"] = "2.3"
    res["ref"] = record.head.uuid

    res["ratingc"] = f"PF{nplayers}"

    if nplayers == 3:
        ruledisp += RUNES["sanma"][JPNAME]
    if record.head.config.meta.mode_id:
        ruledisp += cfg["desktop"]["matchmode"]["map_"][str(record.head.config.meta.mode_id)]["room_name_jp"]
    elif record.head.config.meta.room_id:
        lobby = f"_{record.head.config.meta.room_id}"
        ruledisp += RUNES["friendly"][JPNAME]
        nakas = record.head.config.mode.detail_rule.dora_count
        tsumoloss_off = nplayers == 3 and not record.head.config.mode.detail_rule.have_zimosun
    elif record.head.config.meta.contest_uid:
        lobby = f"_{record.head.config.meta.contest_uid}"
        ruledisp += RUNES["tournament"][JPNAME]
        nakas = record.head.config.mode.detail_rule.dora_count
        tsumoloss_off = nplayers == 3 and not record.head.config.mode.detail_rule.have_zimosun

    if record.head.config.mode.mode == 1:
        ruledisp += RUNES["tonpuu"][JPNAME]
    elif record.head.config.mode.mode == 2:
        ruledisp += RUNES["hanchan"][JPNAME]

    if record.head.config.meta.mode_id == 0 and record.head.config.mode.detail_rule.dora_count == 0:
        res["rule"] = {"disp": ruledisp, "aka53": 0, "aka52": 0, "aka51": 0}
    else:
        res["rule"] = {"disp": ruledisp, "aka53": 1, "aka52": 2 if nakas == 4 else 1,
                       "aka51": 1 if nplayers == 4 else 0}

    res["lobby"] = 0

    res["dan"] = [""] * nplayers
    for e in record.head.accounts:
        res["dan"][e.seat] = cfg["level_definition"]["level_definition"]["map_"][str(e.level.id)]["full_name_jp"]

    res["rate"] = [0] * nplayers
    for e in record.head.accounts:
        res["rate"][e.seat] = e.level.score

    res["sx"] = ['C'] * nplayers

    res["name"] = ["AI"] * nplayers
    for e in record.head.accounts:
        res["name"][e.seat] = e.nickname

    scores = [[e.seat, e.part_point_1, e.total_point / 1000] for e in record.head.result.players]
    res["sc"] = [0] * nplayers * 2
    for i, e in enumerate(scores):
        res["sc"][2 * e[0]] = e[1]
        res["sc"][2 * e[0] + 1] = e[2]

    res["title"] = [ruledisp + lobby, datetime.fromtimestamp(record.head.end_time).strftime("%Y-%m-%d")]

    wrapper = pb.Wrapper()
    wrapper.ParseFromString(record.data)

    details = pb.GameDetailRecords()
    details.ParseFromString(wrapper.data)

    converter = MajsoulPaipuParser(tsumoloss_off=tsumoloss_off)
    for act in details.actions:
        if len(act.result) != 0:
            round_record_wrapper = pb.Wrapper()
            round_record_wrapper.ParseFromString(act.result)

            log = getattr(pb, round_record_wrapper.name[len(".lq."):])()
            log.ParseFromString(round_record_wrapper.data)
            converter.feed(log)

            res["log"] = [e.dump() for e in converter.getvalue()]

    return res


def print_data_as_json(data):
    json_str = MessageToJson(data)
    logger.debug(json_str)
