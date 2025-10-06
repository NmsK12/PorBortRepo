from PIL import Image, ImageDraw, ImageFont
import os

# Crear una imagen simple de prueba
def create_test_image():
    # Crear una imagen de 200x200 píxeles con fondo blanco
    img = Image.new('RGB', (200, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Dibujar un rectángulo azul
    draw.rectangle([50, 50, 150, 150], fill='blue', outline='black', width=2)
    
    # Agregar texto
    try:
        # Intentar usar una fuente del sistema
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        # Si no hay fuente disponible, usar la por defecto
        font = ImageFont.load_default()
    
    draw.text((60, 80), "RESPALDODOX", fill='white', font=font)
    draw.text((70, 110), "BOT", fill='white', font=font)
    
    # Guardar la imagen
    img.save('imagen.jpg', 'JPEG')
    print("Imagen de prueba creada: imagen.jpg")

if __name__ == "__main__":
    create_test_image()
