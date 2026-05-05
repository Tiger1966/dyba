import librosa
import numpy as np
import os
import json
from sklearn.metrics import roc_curve, auc
from sklearn.model_selection import KFold
import matplotlib.pyplot as plt

def extract_features(audio_path):
    try:
        y, sr = librosa.load(audio_path, sr=22050, duration=15)
        
        # 提取多维特征
        centroid = librosa.feature.spectral_centroid(y=y, sr=sr).mean()
        bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr).mean()
        zcr = librosa.feature.zero_crossing_rate(y).mean()
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.85).mean()
        
        return {
            "centroid": centroid,
            "bandwidth": bandwidth,
            "zcr": zcr,
            "rolloff": rolloff
        }
    except Exception as e:
        print(f"Error processing {audio_path}: {e}")
        return None

def collect_data(dataset_dir):
    """
    目录结构应为:
    dataset/
        rough/ (存放至少50个粗犷样本)
        sweet/ (存放至少50个甜美样本)
    """
    data = []
    labels = []
    
    for category in ["rough", "sweet"]:
        label = 1 if category == "rough" else 0
        folder = os.path.join(dataset_dir, category)
        
        if not os.path.exists(folder):
            continue
            
        for file in os.listdir(folder):
            if file.endswith(".wav"):
                path = os.path.join(folder, file)
                features = extract_features(path)
                if features:
                    data.append(features)
                    labels.append(label)
                    
    return data, labels

def optimize_thresholds(data, labels):
    """使用 ROC 曲线寻找最佳阈值"""
    y_true = np.array(labels)
    
    # 提取特征数组
    centroids = np.array([d["centroid"] for d in data])
    bandwidths = np.array([d["bandwidth"] for d in data])
    zcrs = np.array([d["zcr"] for d in data])
    
    # 构建多维评分 (初步权重)
    # 可以通过逻辑回归 (LogisticRegression) 自动学习这些权重
    norm_centroid = (centroids - np.mean(centroids)) / np.std(centroids)
    norm_bandwidth = (bandwidths - np.mean(bandwidths)) / np.std(bandwidths)
    norm_zcr = (zcrs - np.mean(zcrs)) / np.std(zcrs)
    
    scores = 0.4 * norm_centroid + 0.4 * norm_bandwidth + 0.2 * norm_zcr
    
    fpr, tpr, thresholds = roc_curve(y_true, scores)
    
    # 找到最佳阈值 (Youden's J statistic)
    J = tpr - fpr
    best_idx = np.argmax(J)
    best_threshold = thresholds[best_idx]
    
    print(f"最佳综合得分阈值: {best_threshold:.4f}")
    
    # 绘制 ROC 曲线
    plt.figure()
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {auc(fpr, tpr):.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.scatter(fpr[best_idx], tpr[best_idx], marker='o', color='red', label='Best Threshold')
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title('ROC Curve for Timbre Classification')
    plt.legend(loc="lower right")
    plt.savefig('roc_curve.png')
    print("ROC曲线已保存至 roc_curve.png")
    
    return best_threshold

if __name__ == "__main__":
    # 实际使用时替换为你的数据集目录
    dataset_dir = "./timbre_dataset"
    print(f"请确保样本放在 {dataset_dir}/rough 和 {dataset_dir}/sweet 目录下")
    # data, labels = collect_data(dataset_dir)
    # if len(data) > 0:
    #     best_thresh = optimize_thresholds(data, labels)
    #     print("优化完成！")
