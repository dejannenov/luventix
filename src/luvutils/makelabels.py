from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
#from reportlab.graphics.barcode import code39
from reportlab.graphics.barcode import code128
from reportlab.lib.units import inch
import qrcode
from reportlab.lib.utils import ImageReader
from io import BytesIO
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor, black, red, green, blue
from datetime import date



def draw_QRlabel(c, x, y, number, lines, instructions, col, row, site_id):

    qr_string = site_id + str(number).zfill(5)
    # Text on the left half of the label
    text_x = x + 0.1 * inch
    text_y = y + 0.8 * inch

    lines[2] = qr_string

    """    lines = [
        "Study Luventix-001",
        "Patient Study ID:",
        "US-0001-",
        "the_instruction"
    ]
    instructions = [
        "CONSENT",
        "PTNT FORM",
        "CONTAINER",
        "MED RECS",
        "GIFT CRD",
        "OTHER"
    ]
    """

    if row in (0,1,2):
        lines[3] =  instructions[row]
    elif row in (3,4,5,6,7):
        lines[3] = instructions[3] # Med RECS
    elif row in (8,9):
        lines[3] = instructions[row-4] # Med RECS


    # Font Setup
    font_name = "Inter" # Choose your desired font
    font_name_bold = "Inter-Bold" # Choose your desired font

    # Register the font (if not already registered)
    pdfmetrics.registerFont(TTFont(font_name, 'C:\\Users\\dejan\\Documents\\panaton\\OneDrive\\Personal\\misc-docs\\Dejans Fonts\\Inter-3.19\\Inter Variable\\Inter.ttf'))
    pdfmetrics.registerFont(TTFont(font_name_bold, 'C:\\Users\\dejan\\Documents\\panaton\\OneDrive\\Personal\\misc-docs\\Dejans Fonts\\Inter-3.19\\Inter Hinted for Windows\\Desktop\\Inter-Bold.ttf'))

    # Font Setup
    font_size = 10         # Choose your desired font size

    # Set the font and size for the canvas
    c.setFont(font_name_bold, font_size)

    line_num = 0
    for line in lines:
        if line_num == 0:
            font_size = 9
            text_color = blue
            c.setFont(font_name, font_size)
            c.setFillColor(text_color)
        if line_num == 1:
            font_size = 11
            text_color = black
            c.setFont(font_name, font_size)
            c.setFillColor(text_color)
        if line_num == 2:
            font_size = 9
            text_color = black
            c.setFont(font_name_bold, font_size)
            c.setFillColor(text_color)
        if line_num == 3:
            font_size = 10
            text_color = red
            #text_color = c.setFillColorRGB(1, 0, 0)
            c.setFont(font_name, font_size)
            c.setFillColor(text_color)

        c.drawString(text_x, text_y, line)
        text_y -= 0.2 * inch
        line_num += 1


    # Generate QR code from the third line
    qr_data = lines[2]
    qr = qrcode.make(qr_data)
    qr_width = 1.3125 * inch * 0.8  # 905 of the Half of the label width
    #qr_height = 1 * inch
    qr_height = qr_width # Sqaure QR Code

    # Create a BytesIO object to hold the QR code image data
    img_buffer = BytesIO()
    qr.save(img_buffer, format='PNG')  # Save the QR code to the buffer
    img_buffer.seek(0)  # Reset the buffer position

    qr_image = ImageReader(img_buffer)  # Pass the buffer to ImageReader
    #qr_image = ImageReader(qr)

    # Draw QR code on the right half of the label
    qr_x = x + 1.3125 * inch
    qr_y = y
    c.drawImage(qr_image, qr_x, qr_y, width=qr_width, height=qr_height)


def create_labels(output_filename, instructions, lines, site_id, number_of_labels):
    c = canvas.Canvas(output_filename, pagesize=letter)
    width, height = letter

    margin_x = 0.1875 * 72  # 0.1875 inch left margin
    margin_y = 0.6 * 72     # 0.6 inch top margin
    label_width = 2.625 * 72
    label_height = 1 * 72
    gap_x = 0.125 * 72
    gap_y = 0

    sequence = 0
    for page in range(number_of_labels):
        print(f"Generating label {page + 1} of {number_of_labels}.")
        sequence += 1
        for row in range(10):  # 10 rows
            #print(sequence)
            for col in range(3):  # 3 columns
                x = margin_x + col * (label_width + gap_x)
                y = height - margin_y - (row + 1) * (label_height + gap_y)


                draw_QRlabel(c, x, y, sequence, lines, instructions, col, row, site_id)
        c.showPage()
    c.save()

def main():

    instructions = [
        "CONSENT",
        "PTNT FORM",
        "CONTAINER",
        "MED RECS",
        "GIFT CRD",
        "OTHER"
    ]

    lines = [
        "Study Luventix-001",
        "Patient Study ID:",
        "",
        ""
    ]

    sites = {"rishi": "US-0001-","goldklang": "US-0002-","dixit": "US-0003-","imran": "UK-B-0001-", "yamini":"US-0004-"}
    date_string = date.today().strftime('%Y%m%d')

    create_labels(date_string + "_Luventix_Study_UK_BLIND_0001_labels_1_to_1000.pdf", instructions, lines, sites["imran"], 1000)

if __name__ == '__main__':
    main()