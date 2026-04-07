from algosdk import account, mnemonic

# Generate account
private_key, address = account.generate_account()

# Convert to mnemonic (25 words)
mn = mnemonic.from_private_key(private_key)

print("Address:", address)
print("Mnemonic:", mn)