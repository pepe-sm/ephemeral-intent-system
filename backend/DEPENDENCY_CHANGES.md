# Dependency Version Changes

This document tracks the version changes made to `requirements.txt` to ensure compatibility with Python 3.12 and Windows environment.

## Changes Made (2026-06-19)

### IBM Cloud SDK Core
- **Original:** `ibm-cloud-sdk-core==3.18.0`
- **Updated:** `ibm-cloud-sdk-core>=3.19.0`
- **Reason:** Version 3.18.0 had build issues with Python 3.12 (missing pkg_resources module). Updated to use newer versions that are compatible.

### MediaPipe
- **Original:** `mediapipe==0.10.9`
- **Updated:** `mediapipe>=0.10.13`
- **Reason:** Version 0.10.9 is not available for Windows/Python 3.12. Minimum available version is 0.10.13.

### OpenCV Python
- **Original:** `opencv-python==4.9.0.80`
- **Updated:** `opencv-python>=4.9.0.80`
- **Reason:** Allow newer compatible versions for better stability.

### NumPy
- **Original:** `numpy==1.26.3`
- **Updated:** `numpy>=1.26.3`
- **Reason:** Allow newer compatible versions that work with TensorFlow 2.15+.

### Pillow
- **Original:** `pillow==10.2.0`
- **Updated:** `pillow>=10.2.0`
- **Reason:** Allow newer compatible versions for better security and compatibility.

### TensorFlow
- **Original:** `tensorflow==2.15.0`
- **Updated:** `tensorflow>=2.15.0`
- **Reason:** Allow newer compatible versions. System installed TensorFlow 2.21.0.

### LangChain Packages
- **Original:** 
  - `langchain==0.1.0`
  - `langchain-community==0.0.13`
  - `langchain-ibm==0.0.1`
- **Updated:** 
  - `langchain>=0.1.0`
  - `langchain-community>=0.0.13`
  - `langchain-ibm>=0.0.1`
- **Reason:** Allow newer compatible versions for better features and bug fixes.

### ChromaDB
- **Original:** `chromadb==0.4.22`
- **Updated:** `chromadb>=0.4.22`
- **Reason:** Allow newer compatible versions. System installed ChromaDB 0.5.0.

## Installation Notes

- Python Version: 3.12
- Operating System: Windows 11
- Installation Method: pip (user installation)
- All dependencies are being installed with `>=` constraints to allow compatible updates while maintaining minimum version requirements.

## Verification

After installation completes, verify with:
```bash
pip list | Select-String -Pattern "tensorflow|mediapipe|langchain|chromadb|ibm"
```

Expected major packages:
- TensorFlow 2.21.0+
- MediaPipe 0.10.13+
- ChromaDB 0.5.0+
- IBM watsonx.ai 0.2.0
- IBM Cloud SDK Core 3.19.0+
- LangChain 0.1.0+