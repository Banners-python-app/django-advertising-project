import io
import os, csv
from django.conf import settings
from django.shortcuts import get_object_or_404, render
from django.http import FileResponse, JsonResponse, HttpResponse
from django.utils import timezone
from .models import InvoiceItem, Invoice
from agency.models import ProductVariant, Product
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import admin
# ReportLab imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT

def download_invoice_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    styles = getSampleStyleSheet()
    
    # --- CUSTOM STYLES ---
    company_name_style = ParagraphStyle('CompanyName', parent=styles['Heading1'], fontSize=22, leading=26, textColor=colors.HexColor("#111827"), fontName="Helvetica-Bold", alignment=TA_CENTER)
    company_sub_style = ParagraphStyle('CompanySub', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor("#374151"), alignment=TA_CENTER)
    bold_body = ParagraphStyle('BoldBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.black, fontName="Helvetica-Bold")
    body_style = ParagraphStyle('InvoiceBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.black)
    
    # Smaller styles for the 9-column table so it fits nicely
    header_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER)
    table_body_style = ParagraphStyle('TableBody', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.black)
    
    # --- QR CODE SETUP ---
    qr_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'shirdi-crown-payment.png')
    qr_image = ""
    if os.path.exists(qr_path):
        qr_image = Image(qr_path, width=120, height=120)

    story = []
    
    # --- 1. HEADER (Added Website Link) ---
    story.append(Paragraph("SHIRDI CROWN ADVERTISING Pvt. Ltd.", company_name_style))
    story.append(Paragraph("CIN: U73100PN2025PTC237545", company_sub_style))
    story.append(Paragraph("Mauli Nagar, Shirdi - 423109, Tal.Rahata, Dist. Ahilyanagar, Maharashtra.", company_sub_style))
    story.append(Paragraph("Prop: Salunke Shankar Ramesh | Mob: 8412088000", company_sub_style))
    story.append(Paragraph("Email: shirdicrownadvertising@gmail.com | Web: shirdihoarding.in | GST NO. 27AB PCS1 316Q 1ZP", company_sub_style))
    story.append(Spacer(1, 20))
    
    # --- 2. BILLING META DATA ---
    customer_name = invoice.customer.company_name if invoice.customer.company_name else invoice.customer.name
    customer_gst = getattr(invoice.customer, 'gst_number', 'Unregistered')
    customer_addr = getattr(invoice.customer, 'address', 'NA')
    
    meta_data = [
        [Paragraph("<b>TO:</b>", body_style), Paragraph(f"<b>Invoice Number:</b> {invoice.id:04d}", body_style)],
        [Paragraph(f"{customer_name}", bold_body), Paragraph(f"<b>Date:</b> {invoice.created_at.strftime('%d %B %Y')}", body_style)],
        [Paragraph(f"GSTIN: {customer_gst}", body_style), Paragraph("", body_style)],
        [Paragraph(f"Addr: {customer_addr}", body_style), Paragraph("", body_style)],
    ]
    meta_table = Table(meta_data, colWidths=[280, 260])
    meta_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 2), ('SPAN', (0, 3), (1, 3))]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # --- 3. CAMPAIGN ITEMS TABLE (Expanded to 9 Columns) ---
    table_data = [
        [
            Paragraph("SN", header_style), 
            Paragraph("Media Description", header_style), 
            Paragraph("HSN", header_style),
            Paragraph("Size", header_style),
            Paragraph("Duration", header_style), 
            Paragraph("Rent", header_style),
            Paragraph("Print", header_style),
            Paragraph("Mount", header_style),
            Paragraph("Total", header_style)
        ]
    ]
    
    calc_subtotal = 0.0
    
    for index, item in enumerate(invoice.items.all(), start=1):
        product_name = item.product_variant.product.name
        start = item.start_date.strftime('%d %b %Y') if item.start_date else 'N/A'
        end = item.end_date.strftime('%d %b %Y') if item.end_date else 'N/A'
        
        # Extract new variant data gracefully
        hsn_code = item.product_variant.hsn_code or "N/A"
        l = item.product_variant.length or 0
        h = item.product_variant.height or 0
        size_str = f"{l}' x {h}'" if (l or h) else "N/A"
        
        base_amt = float(item.amount or 0)
        print_amt = float(item.printing_price or 0)
        mount_amt = float(item.mounting_price or 0)
        
        row_total = base_amt + print_amt + mount_amt
        calc_subtotal += row_total
        
        table_data.append([
            Paragraph(str(index), table_body_style),
            Paragraph(product_name, table_body_style),
            Paragraph(hsn_code, table_body_style),
            Paragraph(size_str, table_body_style),
            Paragraph(f"{start} to {end}", table_body_style),
            Paragraph(f"{base_amt:,.2f}", table_body_style),
            Paragraph(f"{print_amt:,.2f}", table_body_style),
            Paragraph(f"{mount_amt:,.2f}", table_body_style),
            Paragraph(f"{row_total:,.2f}", table_body_style)
        ])
        
    # Finely tuned column widths to exactly match 540 printable points
    item_table = Table(table_data, colWidths=[20, 130, 45, 45, 80, 50, 45, 45, 80])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#374151")), 
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),  
        ('ALIGN', (5, 1), (8, -1), 'RIGHT'), 
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(item_table)
    
    # --- 4. LIVE FINANCIAL SUMMARY ---
    calc_cgst = calc_subtotal * 0.09
    calc_sgst = calc_subtotal * 0.09
    calc_grand_total = calc_subtotal + calc_cgst + calc_sgst
    
    summary_data = [
        ["", Paragraph("TOTAL", bold_body), Paragraph(f"{calc_subtotal:,.2f}", bold_body)],
        ["", Paragraph("CGST @09%", body_style), Paragraph(f"{calc_cgst:,.2f}", body_style)],
        ["", Paragraph("SGST @09%", body_style), Paragraph(f"{calc_sgst:,.2f}", body_style)],
        ["", Paragraph("GRAND TOTAL", bold_body), Paragraph(f"₹ {calc_grand_total:,.2f}", bold_body)]
    ]
    # Aligned perfectly with the new 80-point Total column
    summary_table = Table(summary_data, colWidths=[385, 75, 80])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('GRID', (1, 0), (-1, -1), 0.5, colors.black),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # --- 5. FOOTER ---
    footer_data = [
        [Paragraph("<b>Account Details</b>", bold_body), Paragraph("<b>For- Shirdi Crown Advertising Pvt Ltd</b>", bold_body)],
        [Paragraph("PUNJAB NATIONAL BANK", body_style), Paragraph("Subject to Rahata Jurisdiction")],
        [Paragraph("SHIRDI CROWN ADVERTISING PVT. LTD.", body_style), ""],
        [Paragraph("AC NO. 1597 10210000 0895", body_style), ""],
        [Paragraph("IFSC NO: PUNB0159710", body_style), ""],
        [Paragraph("GST NO. 27AB PCS1 316Q 1ZP", body_style), ""],
        [Spacer(1, 15), ""], 
        [qr_image, ""],      
        [Paragraph("<b>Scan to Pay</b>", body_style) if qr_image else "", Paragraph("Authorized Signatory", bold_body)]
    ]
    
    footer_table = Table(footer_data, colWidths=[300, 240])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),       
        ('ALIGN', (1,0), (1,-1), 'CENTER'),     
        ('VALIGN', (1,-1), (1,-1), 'BOTTOM'),   
    ]))
    story.append(footer_table)
    
    doc.build(story)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f'Shirdi_Crown_Invoice_{invoice.id:04d}.pdf')


# ==========================================
# QUOTATION PDF GENERATOR
# ==========================================
def download_quotation_pdf(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30
    )
    styles = getSampleStyleSheet()
    
    company_name_style = ParagraphStyle('CompanyName', parent=styles['Heading1'], fontSize=22, leading=26, textColor=colors.HexColor("#111827"), fontName="Helvetica-Bold", alignment=TA_CENTER)
    company_sub_style = ParagraphStyle('CompanySub', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor("#374151"), alignment=TA_CENTER)
    bold_body = ParagraphStyle('BoldBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.black, fontName="Helvetica-Bold")
    body_style = ParagraphStyle('InvoiceBody', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.black)
    
    # Smaller styles for 9 columns
    header_style = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=8, leading=10, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER)
    table_body_style = ParagraphStyle('TableBody', parent=styles['Normal'], fontSize=8, leading=11, textColor=colors.black)
    
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=24, leading=28, textColor=colors.HexColor("#4f46e5"), fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=15)

    qr_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'shirdi-crown-payment.png')
    qr_image = ""
    if os.path.exists(qr_path):
        qr_image = Image(qr_path, width=120, height=120)

    story = []
    
    # --- 1. HEADER (Added Website Link) ---
    #story.append(Paragraph("QUOTATION", title_style))
    story.append(Paragraph("SHIRDI CROWN ADVERTISING Pvt. Ltd.", company_name_style))
    story.append(Paragraph("Mauli Nagar, Shirdi - 423109, Tal.Rahata, Dist. Ahilyanagar, Maharashtra.", company_sub_style))
    story.append(Paragraph("Prop: Salunke Shankar Ramesh | Mob: 8412088000", company_sub_style))
    story.append(Paragraph("Email: shirdicrownadvertising@gmail.com | Web: shirdihoarding.in | GST NO. 27AB PCS1 316Q 1ZP", company_sub_style))
    story.append(Spacer(1, 20))
    
    # --- 2. META DATA ---
    customer_name = invoice.customer.company_name if invoice.customer.company_name else invoice.customer.name
    customer_gst = getattr(invoice.customer, 'gst_number', 'Unregistered')
    
    meta_data = [
        [Paragraph("<b>PREPARED FOR:</b>", body_style), Paragraph(f"<b>Quotation Ref:</b> QT-{invoice.id:04d}", body_style)],
        [Paragraph(f"{customer_name}", bold_body), Paragraph(f"<b>Valid Until:</b> {(invoice.created_at + timezone.timedelta(days=15)).strftime('%d %B %Y')}", body_style)],
        [Paragraph(f"GSTIN: {customer_gst}", body_style), Paragraph(f"<b>Date:</b> {invoice.created_at.strftime('%d %B %Y')}", body_style)],
    ]
    meta_table = Table(meta_data, colWidths=[280, 260])
    meta_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('BOTTOMPADDING', (0,0), (-1,-1), 2)]))
    story.append(meta_table)
    story.append(Spacer(1, 15))
    
    # --- 3. CAMPAIGN ITEMS TABLE ---
    table_data = [
        [
            Paragraph("SN", header_style), 
            Paragraph("Media Description", header_style), 
            Paragraph("HSN", header_style),
            Paragraph("Size", header_style),
            Paragraph("Duration", header_style), 
            Paragraph("Rent", header_style),
            Paragraph("Print", header_style),
            Paragraph("Mount", header_style),
            Paragraph("Total", header_style)
        ]
    ]
    
    calc_subtotal = 0.0
    
    for index, item in enumerate(invoice.items.all(), start=1):
        product_name = item.product_variant.product.name
        start = item.start_date.strftime('%d %b %Y') if item.start_date else 'N/A'
        end = item.end_date.strftime('%d %b %Y') if item.end_date else 'N/A'
        
        hsn_code = item.product_variant.hsn_code or "N/A"
        l = item.product_variant.length or 0
        h = item.product_variant.height or 0
        size_str = f"{l}' x {h}'" if (l or h) else "N/A"
        
        base_amt = float(item.amount or 0)
        print_amt = float(item.printing_price or 0)
        mount_amt = float(item.mounting_price or 0)
        
        row_total = base_amt + print_amt + mount_amt
        calc_subtotal += row_total
        
        table_data.append([
            Paragraph(str(index), table_body_style), 
            Paragraph(product_name, table_body_style), 
            Paragraph(hsn_code, table_body_style),
            Paragraph(size_str, table_body_style),
            Paragraph(f"{start} to {end}", table_body_style), 
            Paragraph(f"{base_amt:,.2f}", table_body_style),
            Paragraph(f"{print_amt:,.2f}", table_body_style),
            Paragraph(f"{mount_amt:,.2f}", table_body_style),
            Paragraph(f"{row_total:,.2f}", table_body_style)
        ])
        
    item_table = Table(table_data, colWidths=[20, 130, 45, 45, 80, 50, 45, 45, 80])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#374151")),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'), 
        ('ALIGN', (1, 1), (1, -1), 'LEFT'), 
        ('ALIGN', (5, 1), (8, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'), 
        ('TOPPADDING', (0, 0), (-1, -1), 6), 
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    story.append(item_table)
    
    # --- 4. FINANCIAL SUMMARY ---
    calc_cgst = calc_subtotal * 0.09
    calc_sgst = calc_subtotal * 0.09
    calc_grand_total = calc_subtotal + calc_cgst + calc_sgst
    
    summary_data = [
        ["", Paragraph("TOTAL", bold_body), Paragraph(f"{calc_subtotal:,.2f}", bold_body)],
        ["", Paragraph("CGST @09%", body_style), Paragraph(f"{calc_cgst:,.2f}", body_style)],
        ["", Paragraph("SGST @09%", body_style), Paragraph(f"{calc_sgst:,.2f}", body_style)],
        ["", Paragraph("GRAND TOTAL", bold_body), Paragraph(f"₹ {calc_grand_total:,.2f}", bold_body)]
    ]
    summary_table = Table(summary_data, colWidths=[385, 75, 80])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'), 
        ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
        ('GRID', (1, 0), (-1, -1), 0.5, colors.black), 
        ('TOPPADDING', (0, 0), (-1, -1), 6), 
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 30))
    
    # --- 5. QUOTATION FOOTER & QR CODE ---
    footer_note = Paragraph("<i>Note: This is a quotation, not an invoice. Pricing is valid for 15 days from the date of issue. Availability of hoarding spaces is subject to confirmation at the time of booking.</i>", body_style)
    
    story.append(footer_note)
    story.append(Spacer(1, 20))
    
    if qr_image:
        qr_table = Table([[qr_image], [Paragraph("<b>Scan to Pay</b>", body_style)]], colWidths=[540])
        qr_table.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'LEFT')]))
        story.append(qr_table)
    
    doc.build(story)
    buffer.seek(0)
    
    return FileResponse(buffer, as_attachment=True, filename=f'Shirdi_Crown_Quotation_QT{invoice.id:04d}.pdf')

# ==========================================
# RESTORED API HELPER (Required for JS)
# ==========================================
def get_variant_price(request, variant_id):
    try:
        variant = ProductVariant.objects.get(id=variant_id)
        return JsonResponse({
            'success': True, 
            'price': variant.offline_price or 0,
            #'print_price': variant.printing_price or 0,
            #'mount_price': variant.mounting_price or 0
        })
    except ProductVariant.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'price': 0,
            #'print_price': 0,
            #'mount_price': 0
        })
    
@staff_member_required
def admin_report_dashboard(request):
    # If the admin clicks a download button, it sends a POST request
    if request.method == 'POST':
        report_type = request.POST.get('report_type')

        # 1. GENERATE INVENTORY STATUS REPORT
        if report_type == 'inventory':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="inventory_status.csv"'
            writer = csv.writer(response)
            
            # Write Header Row
            writer.writerow(['Product Name', 'Category', 'Location', 'Current Status'])

            products = Product.objects.all()
            for p in products:
                status = 'Booked' if p.is_currently_booked else 'Available'
                cat_name = p.category.name if p.category else 'No Category'
                writer.writerow([p.name, cat_name, p.location_address, status])
                
            return response

        # 2. GENERATE SALES & BOOKING REPORT (Date Filtered)
        elif report_type == 'sales':
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')

            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_to_{end_date}.csv"'
            writer = csv.writer(response)
            
            # Write Header Row
            writer.writerow(['Invoice ID', 'Client Name', 'Product', 'Booking Start', 'Booking End', 'Rent Base', 'Print Cost', 'Mount Cost', 'Total Revenue'])

            # Filter InvoiceItems by the selected dates
            items = InvoiceItem.objects.all()
            if start_date:
                items = items.filter(start_date__gte=start_date)
            if end_date:
                items = items.filter(start_date__lte=end_date)

            for item in items:
                client = item.invoice.client_name if item.invoice else 'Unknown'
                product = item.product_variant.product.name if item.product_variant else 'Deleted Product'
                
                rent = float(item.amount or 0)
                print_cost = float(item.printing_price or 0)
                mount_cost = float(item.mounting_price or 0)
                total = rent + print_cost + mount_cost
                
                writer.writerow([
                    item.invoice.invoice_number if item.invoice else '',
                    client,
                    product,
                    item.start_date,
                    item.end_date,
                    rent,
                    print_cost,
                    mount_cost,
                    total
                ])
                
            return response

    # If it's a GET request, just show the HTML page
    context = admin.site.each_context(request)
    context['title'] = 'System Reports'
    return render(request, 'admin/reports_dashboard.html', context)