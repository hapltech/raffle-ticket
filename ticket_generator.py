from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import lightgrey
import os
import math

# Constants
FONT_SIZE = 32
MARGIN = 20
SPACING = 10
BORDER_COLOR = lightgrey
TEXT_COLOR = "#002f79"
TEXT_PADDING = 50  # Distance from edges for numbers


class TicketGenerator:
    def __init__(self, template_path):
        self.template_path = template_path
        self.vertical_font = self._load_font()

    def _load_font(self):
        """Load font with fallbacks"""
        try:
            return ImageFont.truetype("arialbd.ttf", FONT_SIZE)
        except:
            try:
                return ImageFont.truetype("arial.ttf", FONT_SIZE)
            except:
                return ImageFont.load_default()

    def _create_vertical_text(self, text, img_height, img_width, color):
        # Create an image with height based on text length
        text_width = FONT_SIZE * len(text)
        txt_img = Image.new("RGBA", (text_width, FONT_SIZE), (255, 255, 255, 0))
        txt_draw = ImageDraw.Draw(txt_img)

        # Draw text horizontally
        txt_draw.text((0, 0), text, fill=color, font=self.vertical_font)

        # Rotate counter-clockwise for left side, clockwise for right side
        rotated = txt_img.rotate(90, expand=True)

        return rotated

    def add_numbers_to_ticket(self, ticket_number, output_folder):
        img = Image.open(self.template_path)
        img_width, img_height = img.size
        
        # Add border
        draw = ImageDraw.Draw(img)
        draw.rectangle([(0, 0), (img_width - 1, img_height - 1)], outline="lightgray", width=2)
        
        formatted_number = f"NO: {ticket_number:06d}"
        
        # Left number
        left_text = self._create_vertical_text(formatted_number, img_height, img_width, TEXT_COLOR)
        left_x = TEXT_PADDING
        left_y = int((img_height - left_text.size[1]) // 2.7)
        img.paste(left_text, (left_x, left_y), left_text)
        
        # Right number - mirror position of left number
        right_text = self._create_vertical_text(formatted_number, img_height, img_width, TEXT_COLOR)
        right_x = img_width - TEXT_PADDING - right_text.size[0]
        right_y = left_y  # Use same vertical position as left text
        img.paste(right_text, (right_x, right_y), right_text)
        
        output_path = os.path.join(output_folder, f"ticket_{ticket_number:06d}.png")
        img.save(output_path)
        return output_path


class PDFGenerator:
    def __init__(self, page_size=landscape(A4)):
        self.page_width, self.page_height = page_size
        self.tickets_per_page = 8  # 2x4 layout

    def create_pdf(self, ticket_generator, start_number, num_tickets):
        """Create PDF with tickets in 2x4 layout"""
        pdf_path = os.path.join("output_pdf", "raffle_tickets.pdf")
        c = canvas.Canvas(pdf_path, pagesize=(self.page_width, self.page_height))

        # Calculate dimensions
        usable_width = self.page_width - (2 * MARGIN)
        usable_height = self.page_height - (2 * MARGIN)

        # Get template aspect ratio
        with Image.open(ticket_generator.template_path) as img:
            template_ratio = img.size[0] / img.size[1]

        ticket_width = (usable_width - SPACING) / 2
        ticket_height = (usable_height - SPACING) / 2

        # Maintain aspect ratio
        if ticket_width / ticket_height > template_ratio:
            ticket_width = ticket_height * template_ratio
        else:
            ticket_height = ticket_width / template_ratio

        for i in range(num_tickets):
            ticket_number = start_number + i
            ticket_path = ticket_generator.add_numbers_to_ticket(
                ticket_number, "generated_tickets"
            )

            # Calculate position
            page_position = i % self.tickets_per_page
            row = page_position // 2
            col = page_position % 2

            if page_position == 0 and i != 0:
                c.showPage()

            x = MARGIN + col * (ticket_width + SPACING)
            y = self.page_height - MARGIN - (row + 1) * ticket_height - row * SPACING

            c.drawImage(ticket_path, x, y, ticket_width, ticket_height)

        c.save()


def create_folders():
    """Create necessary folders if they don't exist"""
    folders = ["generated_tickets", "output_pdf"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
    return folders


def main():
    folders = create_folders()
    template_path = "Humana Raffle Ticket Template.png"

    ticket_generator = TicketGenerator(template_path)
    pdf_generator = PDFGenerator()

    pdf_generator.create_pdf(ticket_generator, start_number=1, num_tickets=8)

    print(f"Generated tickets saved in: {folders[0]}")
    print(f"PDF file saved in: {folders[1]}")


if __name__ == "__main__":
    main()
