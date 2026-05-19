from pyteal import (
    App,
    Approve,
    Assert,
    Bytes,
    Cond,
    Int,
    Mode,
    OnComplete,
    Reject,
    Seq,
    Txn,
    compileTeal,
)


PROPERTY_ID_KEY = Bytes("propertyId")
PROPERTY_HASH_KEY = Bytes("propertyHash")
DOCUMENT_HASH_KEY = Bytes("documentHash")
WALLET_ADDRESS_KEY = Bytes("walletAddress")
TIMESTAMP_KEY = Bytes("timestamp")
CREATOR_KEY = Bytes("creator")


def approval_program():
    is_create = Txn.application_id() == Int(0)
    is_noop = Txn.on_completion() == OnComplete.NoOp
    has_expected_args = Txn.application_args.length() == Int(5)

    initialize = Seq(
        App.globalPut(CREATOR_KEY, Txn.sender()),
        App.globalPut(PROPERTY_ID_KEY, Bytes("")),
        App.globalPut(PROPERTY_HASH_KEY, Bytes("")),
        App.globalPut(DOCUMENT_HASH_KEY, Bytes("")),
        App.globalPut(WALLET_ADDRESS_KEY, Bytes("")),
        App.globalPut(TIMESTAMP_KEY, Bytes("")),
        Approve(),
    )

    store_verification = Seq(
        App.globalPut(PROPERTY_ID_KEY, Txn.application_args[0]),
        App.globalPut(PROPERTY_HASH_KEY, Txn.application_args[1]),
        App.globalPut(DOCUMENT_HASH_KEY, Txn.application_args[2]),
        App.globalPut(WALLET_ADDRESS_KEY, Txn.application_args[3]),
        App.globalPut(TIMESTAMP_KEY, Txn.application_args[4]),
        Approve(),
    )

    return Cond(
        [is_create, initialize],
        [
            Txn.on_completion() == OnComplete.DeleteApplication,
            Seq(Assert(Txn.sender() == App.globalGet(CREATOR_KEY)), Approve()),
        ],
        [
            Txn.on_completion() == OnComplete.UpdateApplication,
            Seq(Assert(Txn.sender() == App.globalGet(CREATOR_KEY)), Approve()),
        ],
        [Txn.on_completion() == OnComplete.OptIn, Reject()],
        [Txn.on_completion() == OnComplete.CloseOut, Approve()],
        [Txn.on_completion() == OnComplete.ClearState, Approve()],
        [is_noop, Seq(Assert(has_expected_args), store_verification)],
    )


def clear_state_program():
    return Approve()


def compile_approval(version: int = 8) -> str:
    return compileTeal(approval_program(), mode=Mode.Application, version=version)


def compile_clear_state(version: int = 8) -> str:
    return compileTeal(clear_state_program(), mode=Mode.Application, version=version)
