"""Run: pip install -r requirements.txt && python server.py
Set OPENAI_API_KEY in your environment before starting.
"""
import base64
import io
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from PIL import Image, ImageDraw, ImageFilter
import uvicorn
import threading
_call_gate = threading.BoundedSemaphore(value=2)

ROOT = Path(__file__).resolve().parent
BASE = ROOT / 'static' / 'mountain.jpg'
if not BASE.exists():
    import re
    html = (ROOT / 'static' / 'index.html').read_text(encoding='utf-8')
    encoded = re.search(r'const NATURAL_IMAGE\s*=\s*"data:image/jpeg;base64,([^"]+)"', html)
    if encoded:
        BASE.write_bytes(base64.b64decode(encoded.group(1)))
app = FastAPI(title='AI 산지 자유 개발')

class BuildRequest(BaseModel):
    image: str | None = None
    facility: str = Field(min_length=1, max_length=60)
    x: float = Field(ge=0.06, le=0.94)
    y: float = Field(ge=0.08, le=0.92)
    radius: float = Field(default=0.13, ge=0.06, le=0.32)

@app.get('/')
def index():
    return FileResponse(ROOT / 'static' / 'index.html')

@app.get('/mountain.jpg')
def mountain():
    return FileResponse(BASE)

@app.get('/api/health')
def health():
    return {'ready': bool(os.environ.get('OPENAI_API_KEY'))}

def jpeg_to_image(data_uri: str) -> Image.Image:
    raw = base64.b64decode(data_uri.split(',', 1)[-1], validate=True)
    if len(raw) > 8_000_000:
        raise ValueError('image too large')
    return Image.open(io.BytesIO(raw)).convert('RGB')

@app.post('/api/build')
def build(request: BuildRequest):
    if not os.environ.get('OPENAI_API_KEY'):
        raise HTTPException(503, 'OPENAI_API_KEY가 설정되지 않았습니다. 실행 안내를 확인해 주세요.')
    if not _call_gate.acquire(blocking=False):
        raise HTTPException(429, '다른 이미지 생성이 진행 중입니다. 잠시 후 다시 시도하세요.')
    try:
        original = jpeg_to_image(request.image) if request.image else Image.open(BASE).convert('RGB')
        w, h = original.size
        # Edit an ellipse on the existing mountain picture, do NOT generate a new scene.
        rx = int(w * request.radius)
        ry = int(h * request.radius * 0.76)
        cx = int(w * request.x)
        cy = int(h * request.y)
        bbox = (cx-rx, cy-ry, cx+rx, cy+ry)
        # OpenAI image masks: alpha=0 editable, alpha=255 preserved.
        opaque = Image.new('RGBA', (w,h), (255,255,255,255))
        mask_draw = ImageDraw.Draw(opaque)
        mask_draw.ellipse(bbox, fill=(255,255,255,0))
        m = io.BytesIO(); opaque.save(m,format='PNG'); m.name='mask.png'; m.seek(0)
        src = io.BytesIO(); original.save(src,format='PNG'); src.name='mountain.png'; src.seek(0)
        prompt = (
            f'Edit ONLY the transparent masked part of the supplied mountain photograph-style diorama. '
            f'Build a realistic Korean-mountain-compatible {request.facility} in the marked terrain. '
            'Match exactly the perspective, original ridge/peak silhouette, mountain landform, lighting, scale and trees around it. '
            'Do NOT add peaks or alter distant mountains. Integrate infrastructure naturally with the existing slope. '
            'No labels, no writing, no UI, no new sky. The unmasked areas must stay unchanged.'
        )
        from openai import OpenAI
        response = OpenAI().images.edit(
            model='gpt-image-1.5', image=src, mask=m, prompt=prompt,
            size='1536x1024', quality='medium', output_format='png'
        )
        image_data = response.data[0].b64_json
        if not image_data:
            raise RuntimeError('API response did not include image bytes')
        edited = Image.open(io.BytesIO(base64.b64decode(image_data))).convert('RGB')
        if edited.size != original.size:
            edited = edited.resize(original.size, Image.Resampling.LANCZOS)
        # Strict output compositing: unselected pixels are EXACT original pixels.
        alpha = Image.new('L',(w,h),0)
        ImageDraw.Draw(alpha).ellipse(bbox,fill=255)
        alpha = alpha.filter(ImageFilter.GaussianBlur(radius=max(5, int(min(w,h)*0.012))))
        final = Image.composite(edited,original,alpha)
        output = io.BytesIO(); final.save(output,'JPEG',quality=91,optimize=True)
        return {'image':'data:image/jpeg;base64,' + base64.b64encode(output.getvalue()).decode('ascii')}
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(502, 'AI 이미지 편집에 실패했습니다. API 사용량과 서버 로그를 확인하세요.')
    finally:
        _call_gate.release()

if __name__ == '__main__':
    uvicorn.run(app,host='0.0.0.0',port=int(os.environ.get('PORT','8765')))
