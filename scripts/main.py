# run from root of repo

import hashlib
import os
import asyncio
import json
from eth_typing import ChecksumAddress
import solc
from typing import cast

from web3 import Web3, HTTPProvider
from anvil_web3 import AnvilWeb3, AnvilInstance

from noir_lib import (
    create_solidity_proof,
    initialize_noir_project_folder,
    compile_project,
    create_witness,
    generate_solidity_verifier,
)


async def create_default_witness(input: list, sum: int, compilation_dir: str):
    # data_hash = hashlib.sha256(bytes.fromhex(input)).hexdigest()
    # input_hash_encoded = split_hex_into_31_byte_chunks(data_hash)
    output = f"input={json.dumps(input)}\nsum={sum}"
    await create_witness(output, compilation_dir)


async def build_and_verify_simple_demo_proof(
    input: list[int],
    default_input_size_in_circuit=100,
    bb_binary: str = "~/.nargo/backends/acvm-backend-barretenberg/backend_binary",
):
    project_name = "default_test"
    build_folder = await initialize_noir_project_folder(
        circuit_filesystem={
            "src/main.nr": open("src/main.nr", "r")
            .read()
            .replace(str(default_input_size_in_circuit), str(len(input)))
        },
        name=project_name,
    )
    #print("Compiling circuit...")
    await compile_project(build_folder.name)
    #print("done")
    await create_default_witness(input, sum(input), build_folder.name)
    #print("Creating solidity proof...")
    proof_hex = await create_solidity_proof(
        project_name=project_name, compilation_dir=build_folder.name
    )
    #print("done")
    #print("Verifying final proof...")
    #await verify_proof(vkey_fn, build_folder.name, bb_binary)
    #print("success!")

    await generate_solidity_verifier(build_folder.name)

    # now, use the generated solidity verifier to test the gas usage

    #  compile it
    compilation_output = solc.compile_standard(
        {
            "language": "Solidity",
            "sources": {
                "Verifier.sol": {
                    "content": open(
                        os.path.join(
                            build_folder.name, "contract", project_name, "plonk_vk.sol"
                        ),
                        "r",
                    ).read()
                }
            },

            "settings": {
                "viaIR": False,
                "optimizer": {
                    "enabled": True,
                    "runs": 200,
                },
                "outputSelection": {
                    "*": {
                        "*": ["evm.bytecode", "abi"],
                    },
                },
            },
        }
    )

    abi = compilation_output["contracts"]["Verifier.sol"]["UltraVerifier"]["abi"]
    bytecode = compilation_output["contracts"]["Verifier.sol"]["UltraVerifier"]["evm"]["bytecode"]["object"]

    instance = AnvilInstance(chain_id=42)
    w3 = AnvilWeb3(HTTPProvider(instance.http_url))
    deployer = w3.eth.account.from_key(w3.keccak(text="random seed :)"))
    w3.anvil.set_balance(deployer.address, w3.to_wei(100, "ether"))

    # Deploy 
    deploy_tx = w3.eth.contract(abi=abi, bytecode=bytecode).constructor().build_transaction({
        "from": deployer.address,
        "gas": w3.eth.estimate_gas({
            "from": deployer.address,
            "data":  w3.eth.contract(abi=abi, bytecode=bytecode).constructor().data_in_transaction
        }) + 10000,
        "maxFeePerGas": w3.to_wei(2, "gwei"),
        "nonce": w3.eth.get_transaction_count(deployer.address)
    })
    signed_tx = deployer.sign_transaction(deploy_tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    #print("Deployed contract at", receipt["contractAddress"])

    contract = w3.eth.contract(address=receipt["contractAddress"], abi=abi)
    # call verify on contract 
    # function verify(bytes calldata _proof, bytes32[] calldata _publicInputs) external view returns (bool) {
    public_input = [Web3.to_bytes(i).rjust(32, b'\x00') for i in input]
    verify_txn = contract.functions.verify(
        bytes.fromhex(proof_hex),
        public_input
    ).build_transaction({
        "from": deployer.address,
        "gas": 10_000_000,
        "maxFeePerGas": w3.to_wei(2, "gwei"),
        "nonce": w3.eth.get_transaction_count(deployer.address)
    })
    signed_tx = deployer.sign_transaction(verify_txn)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    #print(f"[{len(input)}] Public Inputs Verification:", "\n\tSUCCESS:", receipt['status'] == 1, "\n\tGAS USED:", receipt['gasUsed'], )
    if receipt['status'] != 1:
        raise Exception("Failed to verify proof")
    print(f"{len(input)},{str(receipt['gasUsed'])}") 
    instance.kill()

async def main():
    # this is the public input that will actually be passed
    # for example, if i want my public input to be mostly non zero byte arrays
    # then would be a larger number
    INNER_PUB_INPUT = 1000
    print("[# PUBLIC INPUTS],[GAS USED TO VERIFY]")
     
    for i in [i*25 for i in range(1, 60)]:
        input = [INNER_PUB_INPUT for i in range(i)]
        await build_and_verify_simple_demo_proof(input)

if __name__ == "__main__":
    asyncio.run(main())
