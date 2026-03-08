import fitz
from PIL import Image
import os
import io

def compress_pdf_aggressive(input_path, output_path):
    # PyMuPDF doesn't natively downsample images easily during save.
    # We can use fitz along with PIL to downsample images and replace them.
    # But wait, does fitz allow easy image replacement?
    # Yes, doc[page].replace_image()
    
    doc = fitz.open(input_path)
    
    for page in doc:
        image_list = page.get_images(full=True)
        for img in image_list:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]
            
            try:
                pil_img = Image.open(io.BytesIO(image_bytes))
                
                # Compress logic
                # Max dimension 1200, JPEG quality 50
                max_dim = 1200
                if pil_img.width > max_dim or pil_img.height > max_dim:
                    pil_img.thumbnail((max_dim, max_dim), Image.LANCZOS)
                
                if pil_img.mode in ('RGBA', 'P', 'LA'):
                    pil_img = pil_img.convert('RGB')
                
                buf = io.BytesIO()
                pil_img.save(buf, format="JPEG", quality=50, optimize=True)
                new_image_bytes = buf.getvalue()
                
                # Replace image
                page.replace_image(xref, stream=new_image_bytes)
            except Exception as e:
                print("Error on image:", e)
                continue
                
    doc.save(output_path, garbage=4, deflate=True, clean=True)
    doc.close()

# Test it
pdf_path = 'test_compress.pdf'

doc = fitz.open()
page = doc.new_page()

# create a large dummy image
img = Image.new('RGB', (2000, 2000), color='blue')
img.save('dummy.jpg')
page.insert_image(page.rect, filename='dummy.jpg')
doc.save(pdf_path)
doc.close()

print('Original', os.path.getsize(pdf_path))
compress_pdf_aggressive(pdf_path, 'compressed_test.pdf')
print('Compressed', os.path.getsize('compressed_test.pdf'))
