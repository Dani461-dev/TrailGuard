# Pintasan perintah. Ketik `make help`.
export PYTHONPATH := src
PY := python3

help:            ## tampilkan bantuan
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##/ -/'
check:           ## cek lingkungan LinuxONE (arsitektur, tools, paket)
	bash scripts/00_check_env.sh
setup:           ## buat venv & pasang dependensi
	bash scripts/01_setup_env.sh
toy-data:        ## buat data tiruan CERT
	$(PY) scripts/make_toy_data.py
run:             ## pipeline penuh pada data ASLI di configs/config.yaml (butuh data/raw/cert_r4.2)
	$(PY) -m trailguard.pipeline all
toy:             ## uji cepat seluruh jalur pada data tiruan (keluaran dipisah: outputs/toy_*)
	$(PY) scripts/make_toy_data.py
	$(PY) -m trailguard.pipeline all --config configs/config_toy.yaml
lanl-toy:        ## uji cepat jalur LANL pada data tiruan (keluaran dipisah: outputs/lanl_toy_*)
	$(PY) scripts/make_toy_lanl.py
	$(PY) -m trailguard.pipeline all --config configs/config_lanl_toy.yaml
prefilter-lanl:  ## buat subset LANL dari auth.txt + redteam.txt asli (streaming; kunci dari .env)
	$(PY) scripts/prefilter_lanl.py
lanl-run:        ## pipeline LANL pada subset asli (configs/config_lanl.yaml)
	$(PY) -m trailguard.pipeline all --config configs/config_lanl.yaml
shap-check:      ## uji go/no-go SHAP & pyarrow (jalankan di LinuxONE!)
	$(PY) scripts/test_shap_pyarrow.py
test:            ## jalankan tes
	$(PY) -m pytest -q tests
api:             ## jalankan dashboard di :8000
	$(PY) -m trailguard.api.app
bench:           ## ukur latensi & throughput
	$(PY) scripts/benchmark_latency.py
container:       ## build & jalankan container
	bash deploy/run_container.sh
evidence:        ## kumpulkan bukti LinuxONE untuk screenshot
	bash scripts/capture_evidence.sh
