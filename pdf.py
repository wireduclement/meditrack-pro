from fpdf import FPDF
from datetime import datetime
import os

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", style="B", size=12)
        self.cell(0, 10, "Pharmacy Invoice", ln=True, align="C")

def generate_invoice_pdf(customer, cart_items, invoice_number, comments):
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    def safe_text(text):
        return text.encode("latin-1", "ignore").decode("latin-1")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    invoices_dir = os.path.join(base_dir, "static", "invoices")
    os.makedirs(invoices_dir, exist_ok=True)

    pdf.cell(200, 10, txt=safe_text(f"Invoice #{invoice_number}"), ln=True, align="C")
    pdf.cell(200, 10, txt=safe_text(f"Date: {datetime.now().strftime('%Y-%m-%d')}"), ln=True, align="C")

    pdf.cell(200, 10, txt=safe_text(f"Customer: {customer['fullname']}"), ln=True)
    pdf.cell(200, 10, txt=safe_text(f"Phone: {customer['contact_info']}"), ln=True)

    pdf.cell(200, 10, txt="Items Purchased:", ln=True)
    for item in cart_items:
        pdf.cell(200, 10, txt=safe_text(f"{item['name']} x {item['quantity']} - GHS{item['total_price']}"), ln=True)

    grand_total = sum(item["total_price"] for item in cart_items)
    pdf.cell(200, 10, txt=safe_text(f"Grand Total: GHS{grand_total}"), ln=True)

    pdf.cell(200, 10, txt=safe_text("Instruction or Comments"), ln=True, align="C")
    pdf.cell(200, 10, txt=safe_text(comments), ln=True, align="C")

    pdf_path = os.path.join(invoices_dir, f"{invoice_number}.pdf")
    pdf.output(pdf_path, "F")
    return pdf_path
