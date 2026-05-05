import numpy as np
import librosa

f0_1 = np.full(100, 200.0)
f0_2 = np.full(100, 250.0)

f0_1_2d = f0_1.reshape(-1, 1)
f0_2_2d = f0_2.reshape(-1, 1)

D, _ = librosa.sequence.dtw(X=f0_1_2d.T, Y=f0_2_2d.T, metric='euclidean')
distance = D[-1, -1] / max(len(f0_1), len(f0_2))
print("Distance:", distance)
