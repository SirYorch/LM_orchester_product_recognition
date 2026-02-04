from decimal import Decimal
from datetime import date

from api.graphql.types import OCRDetectedData, OCRResult


class OCRService:
    """
    Mock OCR service.
    Simulates OCR + Vision output.
    """

    async def process_image(self, image_path: str, raw_text: str | None) -> OCRResult:
        """
        Simulate OCR processing.

        Args:
            image_path: Path to image
            raw_text: Optional raw OCR text

        Returns:
            OCRResult
        """

        # 🔴 MOCK – luego tu compañero reemplaza esto
        detected = OCRDetectedData(
            product_name="Avena",
            brand="Quaker",
            presentation="Bolsa",
            weight_or_volume="400 g",
            batch_number="L12345",
            expiration_date=date(2026, 5, 10),
            base_price=Decimal("1.50"),
        )

        return OCRResult(
            detected_data=detected,
            matched_product_id="avena",
            confidence=0.92,
        )
