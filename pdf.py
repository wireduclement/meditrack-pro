from fpdf import FPDF
from datetime import datetime
import os

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", style="B", size=12)
        self.cell(0, 10, "Pharmacy Invoice", ln=True, align="C")
        
    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", style="I", size=8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, "C")

def generate_invoice_pdf(customer, cart_items, invoice_number, comments):
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    def safe_text(text):
        return text.encode("latin-1", "ignore").decode("latin-1")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    invoices_dir = os.path.join(base_dir, "static", "invoices")
    os.makedirs(invoices_dir, exist_ok=True)

    # Header Information
    pdf.cell(200, 10, txt=safe_text(f"Invoice #{invoice_number}"), ln=True, align="C")
    pdf.cell(200, 10, txt=safe_text(f"Date: {datetime.now().strftime('%Y-%m-%d')}"), ln=True, align="C")
    pdf.ln(5)

    # Customer Information
    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(30, 10, txt="Customer:", border=0)
    pdf.set_font("Arial", size=10)
    pdf.cell(160, 10, txt=safe_text(customer['fullname']), ln=True, border=0)
    
    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(30, 10, txt="Phone:", border=0)
    pdf.set_font("Arial", size=10)
    pdf.cell(160, 10, txt=safe_text(customer['contact_info']), ln=True, border=0)
    pdf.ln(5)

    # Items Purchased Table
    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(200, 10, txt="Items Purchased:", ln=True)
    
    # Table Headers
    col_widths = [10, 80, 30, 30, 40]
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(col_widths[0], 10, txt="No.", border=1, fill=True)
    pdf.cell(col_widths[1], 10, txt="Item Name", border=1, fill=True)
    pdf.cell(col_widths[2], 10, txt="Qty", border=1, fill=True, align="C")
    pdf.cell(col_widths[3], 10, txt="Unit Price", border=1, fill=True, align="R")
    pdf.cell(col_widths[4], 10, txt="Total", border=1, fill=True, align="R")
    pdf.ln()

    # Table Data
    pdf.set_font("Arial", size=10)
    for i, item in enumerate(cart_items, 1):
        unit_price = item['total_price'] / item['quantity'] if item['quantity'] > 0 else 0
        
        pdf.cell(col_widths[0], 10, txt=str(i), border=1)
        pdf.cell(col_widths[1], 10, txt=safe_text(item['name']), border=1)
        pdf.cell(col_widths[2], 10, txt=str(item['quantity']), border=1, align="C")
        pdf.cell(col_widths[3], 10, txt=f"GHS {unit_price:.2f}", border=1, align="R")
        pdf.cell(col_widths[4], 10, txt=f"GHS {item['total_price']:.2f}", border=1, align="R")
        pdf.ln()

    # Grand Total
    grand_total = sum(item["total_price"] for item in cart_items)
    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(col_widths[0] + col_widths[1] + col_widths[2] + col_widths[3], 10, 
             txt="Grand Total:", border=1, align="R")
    pdf.cell(col_widths[4], 10, txt=f"GHS {grand_total:.2f}", border=1, align="R")
    pdf.ln(15)

    # Comments Section
    pdf.set_font("Arial", style="B", size=10)
    pdf.cell(200, 10, txt="Instructions or Comments:", ln=True)
    pdf.set_font("Arial", size=10)
    
    # Draw a box for comments
    pdf.rect(10, pdf.get_y(), 190, 30)
    pdf.set_xy(12, pdf.get_y() + 5)
    pdf.multi_cell(186, 5, txt=safe_text(comments))
    
    # Thank you message
    pdf.ln(35)
    pdf.cell(200, 10, txt="Thank you for your patronage!", ln=True, align="C")

    pdf_path = os.path.join(invoices_dir, f"{invoice_number}.pdf")
    pdf.output(pdf_path, "F")
    return pdf_path