import os
import urllib.request
import sys

WEIGHTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "weights")

SCRFD_WEIGHTS_PATH = os.path.join(WEIGHTS_DIR, "scrfd_10g_bnkps.onnx")
SCRFD_WEIGHTS_URL = "https://huggingface.co/DIAMONIK7777/antelopev2/resolve/main/scrfd_10g_bnkps.onnx"

YOLO_WEIGHTS_PATH = os.path.join(WEIGHTS_DIR, "yolov11n-face.pt")
YOLO_WEIGHTS_URL = "https://github.com/akanametov/yolo-face/releases/download/1.0.0/yolov11n-face.pt"

def download_file(url: str, dest_path: str, model_name: str) -> bool:
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000000:
        print(f"[OK] {model_name} already exists at {dest_path} ({os.path.getsize(dest_path) / 1024 / 1024:.2f} MB)")
        return True

    print(f"Downloading {model_name} from {url} ...")
    opener = urllib.request.build_opener()
    opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
    urllib.request.install_opener(opener)

    def progress(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = downloaded / total_size * 100
            sys.stdout.write(f"\rDownloading: {downloaded}/{total_size} bytes ({percent:.1f}%)")
            sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=progress)
        print(f"\n[OK] {model_name} download complete! Saved to {dest_path} ({os.path.getsize(dest_path) / 1024 / 1024:.2f} MB)")
        return True
    except Exception as e:
        print(f"\n[ERROR] Failed to download {model_name}: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False

def download_weights():
    os.makedirs(WEIGHTS_DIR, exist_ok=True)
    success_scrfd = download_file(SCRFD_WEIGHTS_URL, SCRFD_WEIGHTS_PATH, "InsightFace SCRFD-10G (ONNX)")
    success_yolo = download_file(YOLO_WEIGHTS_URL, YOLO_WEIGHTS_PATH, "YOLOv11n-face (PyTorch)")
    return success_scrfd and success_yolo

if __name__ == "__main__":
    download_weights()
