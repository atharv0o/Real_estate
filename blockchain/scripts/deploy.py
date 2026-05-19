from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

from algosdk import account, mnemonic, transaction
from algosdk.logic import get_application_address
from algosdk.transaction import StateSchema

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sdk.algo_client import get_algod_client  # noqa: E402
from smart_contracts.property_verification import (  # noqa: E402
    compile_approval,
    compile_clear_state,
)


def compile_source(algod_client, source: str) -> bytes:
    response = algod_client.compile(source)
    return base64.b64decode(response["result"])


def write_teal_artifacts(approval_teal: str, clear_teal: str) -> None:
    build_dir = ROOT / "build"
    build_dir.mkdir(exist_ok=True)
    (build_dir / "property_verification_approval.teal").write_text(
        approval_teal,
        encoding="utf-8",
    )
    (build_dir / "property_verification_clear.teal").write_text(
        clear_teal,
        encoding="utf-8",
    )


def deploy_contract() -> dict[str, object]:
    import os

    phrase = os.getenv("ALGORAND_MNEMONIC", "").strip()
    if not phrase:
        raise RuntimeError("ALGORAND_MNEMONIC is required to deploy the contract")

    private_key = mnemonic.to_private_key(phrase)
    sender = account.address_from_private_key(private_key)
    algod_client = get_algod_client()

    approval_teal = compile_approval()
    clear_teal = compile_clear_state()
    write_teal_artifacts(approval_teal, clear_teal)

    approval_program = compile_source(algod_client, approval_teal)
    clear_program = compile_source(algod_client, clear_teal)

    params = algod_client.suggested_params()
    txn = transaction.ApplicationCreateTxn(
        sender=sender,
        sp=params,
        on_complete=transaction.OnComplete.NoOpOC,
        approval_program=approval_program,
        clear_program=clear_program,
        global_schema=StateSchema(num_uints=0, num_byte_slices=6),
        local_schema=StateSchema(num_uints=0, num_byte_slices=0),
    )
    signed_txn = txn.sign(private_key)
    tx_id = algod_client.send_transaction(signed_txn)
    confirmation = transaction.wait_for_confirmation(algod_client, tx_id, 6)
    app_id = confirmation.get("application-index")
    if not app_id:
        raise RuntimeError(f"Contract deployment did not return an app id for tx {tx_id}")

    return {
        "network": "testnet",
        "app_id": app_id,
        "contract_address": get_application_address(app_id),
        "tx_id": tx_id,
        "approval_teal": str(ROOT / "build" / "property_verification_approval.teal"),
        "clear_teal": str(ROOT / "build" / "property_verification_clear.teal"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy property verification app to Algorand TestNet")
    parser.add_argument("network", nargs="?", default="testnet", choices=["testnet"])
    args = parser.parse_args()

    if args.network != "testnet":
        raise SystemExit("Only Algorand TestNet deployments are supported")

    result = deploy_contract()
    print(json.dumps({"APP_ID": result["app_id"], "CONTRACT_ADDRESS": result["contract_address"], **result}, indent=2))


if __name__ == "__main__":
    main()
