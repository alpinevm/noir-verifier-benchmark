use dep::std;

global input_size = 100;

fn arbitrary_logic(sum: u64, input: [u8; input_size]) {
	let mut virtual_sum: u64 = 0;
	for i in input {
		virtual_sum += i as u64;
	}
	assert(virtual_sum == sum);
}

fn main(input: pub [u8; input_size], sum: u64) {
	arbitrary_logic(sum, input);
}


