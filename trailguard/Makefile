# Pintasan perintah. Ketik `make help`.
export PYTHONPATH := src
PY := python3

help:            ## tampilkan bantuan
	@grep -E '^[a-z-]+:.*##' Makefile | sed 's/:.*##/ -/'
check:           ## cek lingkungan LinuxONE (arsitektur, tools, paket)
	bash scripts/00_check_env.sh
setup:           ## buat venv & pasang dependensi
	bash scripts/01_setup_env.sh
toy-data:        ## buat data tiruan
	$(PY) scripts/make_toy_data.py
run:             ## jalankan seluruh pipeline pada data di configs/config.yaml
	$(PY) -m trailguard.pipeline all
toy:             ## data tiruan + pipeline penuh (uji cepat, <1 menit)
	$(MAKE) toy-data && $(MAKE) run
lanl-toy:        ## data tiruan LANL + pipeline LANL
	$(PY) scripts/make_toy_lanl.py && $(PY) -m trailguard.pipeline all --config configs/config_lanl.yaml
lanl-run:        ## pipeline LANL pada data di configs/config_lanl.yaml (mis. subset hasil prefilter)
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
