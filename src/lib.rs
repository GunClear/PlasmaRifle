extern crate web3;

use web3::futures::Future;
use web3::contract::{Contract, Options};
use web3::types::{Address, U256};

pub fn test() {
    let (_eloop, transport) = web3::transports::Http::new("http://localhost:7545").unwrap();
    let web3 = web3::Web3::new(transport);
    let accounts = web3.eth().accounts().wait().unwrap();
    
    let contract = Contract::from_json(
        web3.eth(),
        contract_address,
        include_bytes!("../src/contract/res/token.json"),
    ).unwrap();
}

#[cfg(test)]
mod tests {
    use test;
    #[test]
    fn it_works() {
        self::test();
    }
}
