use dep::std;

pub fn decode_field_encoded_hash(encoded_expected_hash: [Field; 2]) -> [u8; 32] {
	let mut proposed_txn_hash: [u8; 32] = [0; 32];
	let leg1 = encoded_expected_hash[0].to_be_bytes(31);
	let leg2 = encoded_expected_hash[1].to_be_bytes(1);
	for i in 0..31 {
		proposed_txn_hash[i] = leg1[i];	
	}
	proposed_txn_hash[31] = leg2[0];	
	proposed_txn_hash
}

fn arbitrary_logic(sum: u64, input: [u8; 100]) {
	let mut virtual_sum: u64 = 0;
	for i in input {
		virtual_sum += i as u64;
	}
	assert(virtual_sum == sum);
}

// pub input is just the hash variant
fn main(encoded_input_hash: pub [Field; 2], sum: u64, input: [u8; 100]) {
	let input_hash = decode_field_encoded_hash(encoded_input_hash);
	assert(std::hash::sha256(input) == input_hash);
	arbitrary_logic(sum, input);
}

