Dua bentuk sumber diterima (Kontrak #1b di docs/03_DATA_CONTRACTS.md):

  a) MENTAH   auth.txt(.gz) / redteam.txt(.gz): tanpa header, id manusia & komputer apa adanya.
              -> loader inilah yang mem-pseudonim-kan (kunci dari env TRAILGUARD_HMAC_KEY).
  b) SUBSET   hasil scripts/prefilter_lanl.py (lanl_subset_auth.csv.gz, lanl_redteam_hashed.csv.gz):
              ada header dan SEMUA id sudah ter-hash saat prefilter.
              -> loader TIDAK meng-hash ulang (kalau di-hash dua kali, hash label & event tak akan cocok).

Format mentah (https://csr.lanl.gov/data/cyber1/):
  auth.txt(.gz)    : time,src_user@dom,dst_user@dom,src_comp,dst_comp,auth_type,logon_type,orientation,success/fail
  redteam.txt(.gz) : time,user@dom,src_comp,dst_comp
`time` = detik sejak awal data. File asli ~1 miliar baris -> JANGAN dimuat penuh:
jalankan scripts/prefilter_lanl.py dulu (streaming), lalu arahkan config ke folder subset.
"""
import gzip