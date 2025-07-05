import base64
import mimetypes
from langchain_core.messages import HumanMessage

from common.ai import get_llm_model
from receipt.ai.structured_output import Receipt


def recognize_receipt(image_path):
    # Convert image to base64
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    # Detect image format dynamically
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"  # fallback to jpeg if detection fails
    
    content = [
        {"type": "text", "text": """Elemezd ezt a bolti blokkot és nyerd ki belőle az összes adatot. Fontos szabályok:

1. **Dátum és idő**: A blokkon szereplő vásárlás dátumát és időpontját add meg

2. **Blokk szám**: A blokk sorszámát vagy azonosítóját add meg

4. **Bolt adatai**: 
   - Bolt neve
   - Adószám

5. **Bolt címe**:
   - Irányítószám
   - Város
   - Utcanév
   - Házszám

6. **Pontoság**: Csak azokat az adatokat add meg, amiket a képen ténylegesen látni lehet. Ha valamit nem látsz, ne találgass!

Elemezd most ezt a blokkot és add vissza a strukturált adatokat:"""},
        {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded_string}"}}
    ]

    message = HumanMessage(content=content)

    result = get_llm_model().with_structured_output(Receipt).invoke([message])
    
    return result


