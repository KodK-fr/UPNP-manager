import qrcode
from PIL import Image, ImageTk
import io

class QRCodeGenerator:
    @staticmethod
    def generate_qr_code(url, size=200):
        """Générer un code QR."""
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        return ImageTk.PhotoImage(Image.open(buffer))
