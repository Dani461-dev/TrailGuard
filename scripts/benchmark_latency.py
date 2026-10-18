=======
w = cfg["model"]["ensemble_weight_supervised"]
>>>>>>> 026a9770ca59af11198a2ac01aa4db4f20dac648

# 1) latensi skor satu baris (simulasi satu event masuk)
sample = feat.sample(min(300, len(feat)), random_state=0)
lat = []
for i in range(len(sample)):
    t = time.perf_counter()
<<<<<<< HEAD
    score_frame(bundle, sample.iloc[[i]])          # tanpa w_sup -> pakai alpha hasil tuning di bundle