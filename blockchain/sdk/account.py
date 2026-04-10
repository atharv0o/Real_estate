from algosdk import mnemonic

def get_account_private_key(mnemonic_phrase):
    return mnemonic.to_private_key(mnemonic_phrase)