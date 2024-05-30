# noir-verifier-benchmark
Script to benchmark gas cost to verify a noir (w/ barratenberg) circuit with `n` public inputs.

## Results 
With noir v0.29.0 and solc v0.8.20, the gas cost to verify a circuit with `n` public inputs is as follows:

![Linear Regression of Public Input Size vs Gas Used](https://raw.githubusercontent.com/alpinevm/noir-verifier-benchmark/main/regression.png) 
<br>
```y = 369.95892089093695x + 429232.053763441```

# Run
Requires solc, anvil (foundry), and noir (nargo) to be installed. 
```
python -m pip install -r requirements.txt && python scripts/main.py
```
