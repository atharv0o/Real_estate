from __future__ import annotations

import os

from pathlib import Path

from dotenv import load_dotenv
from algosdk.v2client import algod, indexer


ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT.parent / ".env")
load_dotenv(ROOT / ".env")

DEFAULT_ALGOD_ADDRESS = "https://testnet-api.algonode.cloud"
DEFAULT_INDEXER_ADDRESS = "https://testnet-idx.algonode.cloud"


def _env(name: str, fallback: str = "") -> str:
    return os.getenv(name, fallback).strip()


def get_algod_address() -> str:
    return (
        _env("ALGOD_ADDRESS")
        or _env("ALGOD_SERVER")
        or _env("ALGORAND_NODE_URL", DEFAULT_ALGOD_ADDRESS)
    )


def get_algod_token() -> str:
    return _env("ALGOD_TOKEN") or _env("ALGORAND_NODE_TOKEN")


def get_indexer_address() -> str:
    return _env("INDEXER_ADDRESS") or _env("INDEXER_SERVER", DEFAULT_INDEXER_ADDRESS)


def get_indexer_token() -> str:
    return _env("INDEXER_TOKEN")


def get_app_id() -> int | None:
    app_id = _env("APP_ID")
    return int(app_id) if app_id.isdigit() else None


def get_algod_client() -> algod.AlgodClient:
    return algod.AlgodClient(get_algod_token(), get_algod_address())


def get_indexer_client() -> indexer.IndexerClient:
    return indexer.IndexerClient(get_indexer_token(), get_indexer_address())
