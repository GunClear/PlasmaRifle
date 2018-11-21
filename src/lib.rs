extern crate web3;
extern crate serde;
extern crate serde_json;

#[macro_use]
extern crate serde_derive;

use std::fs::File;
use std::io::Read;

use serde_json::{Value, Map};

//use web3::futures::Future;
//use web3::contract::{Contract, Options};
//use web3::types::{Address, U256, Bytes};

pub struct ContractInterface {
    abi: Value,
    bytecode: String,
    bytecode_runtime: String,
}

#[derive(Serialize, Deserialize)]
struct Package {
    contracts: Map<String, ContractInterface>
}

pub fn contracts(contracts_jsonfile: String) -> Map<String, ContractInterface> {
    // Get ABI, Bin and Runtime
    let mut file = File::open(contracts_jsonfile).expect("File not found!");
    let mut data = String::new();
    file.read_to_string(&mut data).expect("File contents corrupted");

    let p: Package = serde_json::from_str(&data);
    return p.contracts;
}

pub fn trial() {
    let (_eloop, transport) = web3::transports::Http::new("http://localhost:7545").unwrap();
    let web3 = web3::Web3::new(transport);
    //let accounts = web3.eth().accounts().wait().unwrap();

    //let txn_receipt = C;

    /*let contract = Contract::from_json(
        web3.eth(),
        contract_address,
        abi,
    ).unwrap();*/
}

#[cfg(test)]
mod tests {
    use test;
    #[test]
    fn it_works() {
        self::contracts("../contracts.json");
    }
}
