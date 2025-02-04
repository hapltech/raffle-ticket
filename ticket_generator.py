from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.colors import lightgrey
from reportlab.lib.utils import ImageReader
import sys
import os
import math
import time
import io

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
        draw.rectangle(
            [(0, 0), (img_width - 1, img_height - 1)], outline="lightgray", width=2
        )

        formatted_number = f"NO: {ticket_number:06d}"

        # Left number
        left_text = self._create_vertical_text(
            formatted_number, img_height, img_width, TEXT_COLOR
        )
        left_x = TEXT_PADDING
        left_y = int((img_height - left_text.size[1]) // 2.7)
        img.paste(left_text, (left_x, left_y), left_text)

        # Right number - mirror position of left number
        right_text = self._create_vertical_text(
            formatted_number, img_height, img_width, TEXT_COLOR
        )
        right_x = img_width - TEXT_PADDING - right_text.size[0]
        right_y = left_y  # Use same vertical position as left text
        img.paste(right_text, (right_x, right_y), right_text)

        output_path = os.path.join(output_folder, f"ticket_{ticket_number:06d}.png")
        img.save(output_path)
        return output_path

    def add_numbers_to_ticket_memory(self, ticket_number, template):
        """Generate ticket in memory without saving to disk"""
        img = template.copy()
        img_width, img_height = img.size

        draw = ImageDraw.Draw(img)
        draw.rectangle(
            [(0, 0), (img_width - 1, img_height - 1)], outline="lightgray", width=2
        )

        formatted_number = f"NO: {ticket_number:06d}"

        left_text = self._create_vertical_text(
            formatted_number, img_height, img_width, TEXT_COLOR
        )
        left_x = TEXT_PADDING
        left_y = int((img_height - left_text.size[1]) // 2.7)
        img.paste(left_text, (left_x, left_y), left_text)

        right_text = self._create_vertical_text(
            formatted_number, img_height, img_width, TEXT_COLOR
        )
        right_x = img_width - TEXT_PADDING - right_text.size[0]
        right_y = left_y
        img.paste(right_text, (right_x, right_y), right_text)

        return img


class PDFGenerator:
    def __init__(self, page_size=landscape(A4)):
        self.page_width, self.page_height = page_size
        self.tickets_per_page = 8  # 2x4 layout
        self.dpi = 150  # Reduced DPI for smaller file size

    def create_pdf(self, ticket_generator, start_number, num_tickets, generate_images=False):
        pdf_path = os.path.join("output_pdf", "raffle_tickets.pdf")
        c = canvas.Canvas(pdf_path, pagesize=(self.page_width, self.page_height))
        

        # Calculate dimensions once
        usable_width = self.page_width - (2 * MARGIN)
        usable_height = self.page_height - (2 * MARGIN)

        with Image.open(ticket_generator.template_path) as img:
            template_ratio = img.size[0] / img.size[1]
            # Resize template to optimal size
            optimal_width = int(1000 * template_ratio)
            optimal_height = 1000
            img = img.resize((optimal_width, optimal_height), Image.Resampling.LANCZOS)

        ticket_width = (usable_width - SPACING) / 2
        ticket_height = (usable_height - SPACING) / 2

        if ticket_width / ticket_height > template_ratio:
            ticket_width = ticket_height * template_ratio
        else:
            ticket_height = ticket_width / template_ratio

        total_pages = math.ceil(num_tickets / self.tickets_per_page)

        print(f"\nGenerating PDF with {total_pages} pages...")
        start_time = time.time()

        for i in range(num_tickets):
            if i % 10 == 0:
                progress = (i / num_tickets) * 100
                print(f"Progress: {progress:.1f}%")

            ticket_number = start_number + i

            # Save individual images if requested
            if generate_images:
                ticket_generator.add_numbers_to_ticket(ticket_number, "generated_tickets")
            
            # Generate ticket for PDF
            img_buffer = io.BytesIO()
            ticket_img = ticket_generator.add_numbers_to_ticket_memory(ticket_number, img)
            ticket_img.save(img_buffer, format="PNG", optimize=True)
            img_buffer.seek(0)

            page_position = i % self.tickets_per_page
            row = page_position // 2
            col = page_position % 2

            if page_position == 0 and i != 0:
                c.showPage()

            x = MARGIN + col * (ticket_width + SPACING)
            y = self.page_height - MARGIN - (row + 1) * ticket_height - row * SPACING

            c.drawImage(ImageReader(img_buffer), x, y, ticket_width, ticket_height)

        c.save()
        print(f"\nPDF generation completed in {time.time() - start_time:.1f} seconds")


def create_folders():
    """Create necessary folders if they don't exist"""
    folders = ["generated_tickets", "output_pdf"]
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
    return folders


def get_template_path():
    if getattr(sys, "frozen", False):
        # Running as exe
        return os.path.join(sys._MEIPASS, "Humana Raffle Ticket Template.png")
    else:
        # Running as script
        return "Humana Raffle Ticket Template.png"


def create_folders(generate_images=False):
    """Create necessary folders if they don't exist"""
    folders = ["output_pdf"]
    if generate_images:
        folders.append("generated_tickets")
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
    return folders


def main():
    try:
        generate_images = input("Do you want individual ticket images? (y/n): ").lower() == "y"
        folders = create_folders(generate_images)
        template_path = get_template_path()

        if not os.path.exists(template_path):
            print(f"Error: Template file not found at {template_path}")
            return

        while True:
            try:
                start_number = int(input("Enter starting ticket number: "))
                num_tickets = int(input("Enter number of tickets to generate: "))
                if start_number < 1 or num_tickets < 1:
                    print("Please enter positive numbers only")
                    continue
                break
            except ValueError:
                print("Please enter valid numbers")

        ticket_generator = TicketGenerator(template_path)
        pdf_generator = PDFGenerator()

        pdf_generator.create_pdf(ticket_generator, start_number, num_tickets, generate_images)

        print(f"\nSuccess!")
        print(f"PDF file saved in: {folders[0]}")
        if generate_images:
            print(f"Individual tickets saved in: {folders[-1]}")
        sys.exit(0)

    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
