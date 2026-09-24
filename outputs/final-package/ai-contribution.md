# AI assistance

I used an AI coding assistant throughout this project. It helped me draft the project brief and design options, write the Python and SQL for the bridge and its tests, build the workbook, memo, reviewer packet, and demo, and argue against my own conclusions in an adversarial review.

The headline numbers ($863.8M change, $852.9M volume effect, $10.9M yield effect) do not rest on that prose. `reproduce.py` recomputes the bridge from data extracted from the frozen SEC exhibits in this repo and runs with the tests in CI on every push; `scripts/validate_final_evidence.py` checks the full package.

The evidence is the filings, the code, the workbook, and the validation output, not any prose the assistant wrote. Please judge those directly. No outside practitioner has reviewed the analysis yet, and it makes no causal, forecast, or investment claim. See `validation-report.md` for the checks and `validation-evidence.json` for hashes.
