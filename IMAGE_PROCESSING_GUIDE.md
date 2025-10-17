# Image Processing Feature - DocZap

## Overview

The WhatsApp bot now supports **image processing** using OpenAI Vision API. When a doctor sends an image (exam results, prescriptions, etc.), the bot:

1. **Extracts text/information** from the image using AI vision
2. **Gets the last prontuário** created by that doctor
3. **Intelligently merges** the image content into the prontuário
4. **Updates the database** with the enhanced prontuário

## How It Works

### User Flow

```
Doctor sends image → Bot downloads image → OpenAI Vision extracts text →
AI merges into last prontuário → Database updated → Doctor receives confirmation
```

### What Images Can Be Processed

- ✅ Exam results (blood tests, X-rays, CT scans)
- ✅ Prescriptions from other doctors
- ✅ Medical reports
- ✅ Vital signs charts
- ✅ Handwritten medical notes
- ✅ Any medical document with text

## Architecture

### Files Created/Modified

1. **`services/image_service.py`** ✨ NEW
   - Image processing service using OpenAI Vision
   - Extracts text from images
   - Gets last prontuário from database
   - Merges content intelligently
   - Updates prontuário in database

2. **`handlers/whatsapp_handler.py`** ✏️ MODIFIED
   - Added `handle_image_message()` method
   - Added image service to `__init__()`
   - Updated message type handling

3. **`main.py`** ✏️ MODIFIED
   - Initializes `ImageProcessingService`
   - Passes image service to WhatsAppHandler

4. **`requirements.txt`** ✏️ MODIFIED
   - Added `openai>=1.12.0`

## Technical Details

### ImageProcessingService Class

```python
class ImageProcessingService:
    def __init__(self):
        # Initializes OpenAI client and Supabase client

    async def extract_text_from_image(image_data: bytes) -> Dict:
        # Uses OpenAI Vision (gpt-4o) to extract text from image

    async def get_last_prontuario(doctor_session: Dict) -> Dict:
        # Gets most recent consultation created by this doctor

    async def merge_image_content_into_prontuario(prontuario: Dict, extracted_content: str) -> Dict:
        # Uses AI to intelligently add image content to SOAP prontuário

    async def update_prontuario_in_database(consultation_id: str, updated_content: Dict) -> Dict:
        # Updates consultation in Supabase

    async def process_image_and_update_prontuario(image_data: bytes, doctor_session: Dict) -> Dict:
        # Complete flow: extract → get → merge → update
```

### OpenAI Vision Integration

**Model Used**: `gpt-4o` (supports vision)

**Prompt Strategy**:
```python
messages = [
    {
        "role": "system",
        "content": "Você é um assistente médico especializado em extrair informações de imagens médicas..."
    },
    {
        "role": "user",
        "content": [
            {"type": "text", "text": "..."},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}", "detail": "high"}}
        ]
    }
]
```

### SOAP Integration

The AI intelligently distributes extracted content across SOAP sections:

- **S (Subjetivo)**: Patient complaints/history from image
- **O (Objetivo)**: Exam results, vital signs
- **A (Avaliação)**: Diagnoses, ICD codes
- **P (Plano)**: Prescriptions, treatment plans, recommendations

## Usage

### For Doctors

1. **Create a prontuário** first (send audio to create initial consultation)
2. **Send an image** with exam results or medical documents
3. **Receive confirmation** with extracted content preview
4. **Check updated prontuário** on ProntoDoc website

### Example Workflow

```
Doctor: [Sends audio of consultation]
Bot: "Prontuario Pronto ✅"

Doctor: [Sends image of blood test results]
Bot: "📸 Imagem recebida. Processando..."
Bot: "🔍 Extraindo informações da imagem..."
Bot: "✅ Imagem Processada com Sucesso!

📝 Informações extraídas:
HEMOGRAMA COMPLETO
Hemoglobina: 14.2 g/dL (Referência: 12-16)
Leucócitos: 7.200/mm³ (Referência: 4.000-11.000)
...

✅ Prontuário atualizado com as informações da imagem!

💡 Veja o prontuário completo no site do Prontodoc"
```

## Environment Variables

### Required

```env
# OpenAI API Key for Vision
OPENAI_API_KEY=sk-...

# Supabase (already required)
SUPABASE_URL=https://...
SUPABASE_SERVICE_ROLE_KEY=...
```

## Installation & Deployment

### Local Testing

```bash
cd telegram-doczap
source venv/bin/activate

# Install new dependency
pip install -r requirements.txt

# Make sure OPENAI_API_KEY is in .env
echo "OPENAI_API_KEY=sk-..." >> .env

# Run bot
python main.py
```

### Railway Deployment

```bash
# Deploy
cd telegram-doczap
railway up

# Set OpenAI API key if not already set
railway variables set OPENAI_API_KEY=sk-...

# Monitor logs
railway logs --tail
```

## Testing

### Test Locally

```bash
# 1. Start bot
python main.py

# 2. Use ngrok
ngrok http 8000

# 3. Set WhatsApp webhook to ngrok URL
# 4. Send test images in WhatsApp
# 5. Check logs and database
```

### Test Images to Try

- Blood test results (PDF screenshot)
- Prescription from pharmacy
- X-ray report
- Handwritten doctor's notes
- Vital signs chart

## Error Handling

### Common Errors

**"Nenhum prontuário encontrado"**
- Solution: Create a prontuário first by sending audio

**"Erro ao processar imagem"**
- Check OPENAI_API_KEY is set
- Check image is valid (not corrupted)
- Check OpenAI API quota/credits

**"Serviço de processamento de imagens não disponível"**
- Image service failed to initialize
- Check OPENAI_API_KEY environment variable

## Limitations

1. **Requires existing prontuário**: Must create a consultation first (via audio)
2. **Updates last prontuário only**: Always updates the most recent consultation
3. **Image size**: WhatsApp limits apply (typically 5MB max)
4. **Processing time**: Takes 10-30 seconds depending on image complexity
5. **Cost**: Uses OpenAI API (gpt-4o vision tokens)

## Cost Considerations

**OpenAI Vision Pricing** (as of 2024):
- gpt-4o vision: ~$0.01-0.03 per image (depending on detail level)
- We use "high" detail for medical accuracy

**Estimated costs**:
- 100 images/month: ~$2-3
- 1000 images/month: ~$20-30

## Database Schema

### Consultations Table

The image content is added to existing consultation fields:

```sql
consultations (
    consultation_id uuid PRIMARY KEY,
    doctor_id uuid,
    subjective text,      -- ← Image content added here
    objective text,       -- ← Exam results added here
    assessment text,      -- ← Diagnoses added here
    plan text,            -- ← Prescriptions added here
    notes text,           -- ← General notes added here
    created_at timestamp,
    updated_at timestamp  -- ← Updated when image processed
)
```

## Security

✅ **Authentication required**: Only logged-in doctors can send images
✅ **Doctor ownership**: Only updates prontuários created by that doctor
✅ **No image storage**: Images are processed and discarded (not stored permanently)
✅ **Encrypted transmission**: All data encrypted in transit to OpenAI
✅ **LGPD compliant**: Medical data handling follows best practices

## Future Enhancements

Potential improvements:

- [ ] Support multiple images per prontuário
- [ ] Allow selection of which prontuário to update
- [ ] Image OCR preview before processing
- [ ] Support for Telegram image messages (not just WhatsApp)
- [ ] Batch processing multiple images
- [ ] Extract structured data (tables, charts) from images
- [ ] Save processed images to Supabase Storage

## Troubleshooting

### Image not processing

```bash
# Check logs
railway logs --tail | grep "image"

# Test OpenAI connection
python -c "
import openai
client = openai.OpenAI(api_key='your_key')
print('OpenAI connected')
"

# Check database
# Verify last consultation exists for doctor
```

### Extracted content not accurate

- Try higher quality images
- Ensure text is clear and readable
- Check image orientation is correct
- Verify language is Portuguese (system prompt is in PT-BR)

## Support

**Documentation**:
- Image Service: `services/image_service.py`
- WhatsApp Handler: `handlers/whatsapp_handler.py`
- This guide: `IMAGE_PROCESSING_GUIDE.md`

**Testing Guide**: See `DEVELOPMENT_TESTING.md`

**Deployment Guide**: See `TEST_AND_DEPLOY.md`

## Examples

### Success Case

```
Input Image: Blood test PDF
Extracted Text:
  "HEMOGRAMA COMPLETO
   Hemoglobina: 14.2 g/dL (Normal: 12-16)
   Leucócitos: 7.200/mm³ (Normal: 4.000-11.000)
   ..."

Updated Prontuário (Objective section):
  "...

   EXAMES RECEBIDOS (via imagem):
   📊 Hemograma Completo:
   - Hemoglobina: 14.2 g/dL (Referência: 12-16) ✓
   - Leucócitos: 7.200/mm³ (Referência: 4.000-11.000) ✓
   - Resultados dentro da normalidade"
```

### Error Case

```
Error: "Nenhum prontuário encontrado. Crie um prontuário primeiro enviando um áudio."

Reason: Doctor hasn't created any consultations yet
Solution: Send audio to create initial prontuário, then send image
```

---

## Quick Reference

**Send Image**: Just send an image in WhatsApp after logging in
**Check Result**: Visit ProntoDoc website to see updated prontuário
**Cost**: ~$0.01-0.03 per image processed
**Processing Time**: 10-30 seconds
**Supported Formats**: JPG, PNG, PDF screenshots

---

**Feature Status**: ✅ READY FOR PRODUCTION
**Created**: 2025-10-15
**Version**: 1.0.0
