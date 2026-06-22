from __future__ import annotations
import sys
print('Python:', sys.version.replace('\n',' '))
try:
    import torch
    print('torch:', torch.__version__)
    print('torch.version.cuda:', torch.version.cuda)
    ok = torch.cuda.is_available()
    print('torch.cuda.is_available():', ok)
    if ok:
        print('GPU:', torch.cuda.get_device_name(0))
    else:
        print('GPU: not available; project will run on CPU or hash/rule fallback.')
except Exception as e:
    print('torch import failed:', e)
try:
    import transformers
    print('transformers:', transformers.__version__)
except Exception as e:
    print('transformers import failed:', e)
try:
    import chromadb
    print('chromadb:', chromadb.__version__)
except Exception as e:
    print('chromadb import failed:', e)
try:
    import gradio
    print('gradio:', gradio.__version__)
except Exception as e:
    print('gradio import failed:', e)
