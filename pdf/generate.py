import datetime
import io
import logging
import traceback
from decimal import Decimal

import wx
from z3c.rml import rml2pdf

import app_config
from model.columns import Column
from model.family import get_parents, get_students
from pdf.my_bytes_io import MyBytesIO

INVOICE_RML_TEMPLATE = """<!DOCTYPE document SYSTEM "rml_1_0.dtd">
<document filename="invoice.pdf" invariant="1">

  <template pagesize="letter" leftMargin="72">
    <pageTemplate id="main" pagesize="letter portrait">
      <pageGraphics>
        <setFont name="Times-Roman" size="24"/>
        <drawString x="35" y="760">Class Enrollment Invoice</drawString>
        <setFont name="Times-Roman" size="12"/>
        <drawString x="35" y="740">Generated on {date}</drawString>
      </pageGraphics>
      <frame id="second" x1="35" y1="45" width="525" height="675"/>
    </pageTemplate>
  </template>

  <stylesheet>
    <initialize>
      <alias id="style.normal" value="style.Normal"/>
    </initialize>
    <paraStyle name="title" fontName="Times-Bold" fontSize="16" leading="12"
               spaceBefore="12" spaceAfter="12"/>
    <paraStyle name="bold" fontName="Times-Bold" fontSize="10" leading="12"/>
    <paraStyle name="normal" fontName="Times-Roman" fontSize="10" leading="12"/>
    <blockTableStyle id="students">
      <blockFont name="Times-Bold" size="12" start="0,0" stop="-1,0"/>
      <blockFont name="Times-Roman" size="10" start="0,1" stop="-1,-1"/>
      <blockFont name="Times-Bold" size="10" start="0,-1" stop="-1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="black" start="0,0" stop="-1,0"/>
      <lineStyle kind="LINEABOVE" colorName="black" start="0,-1" stop="-1,-1"/>
      <blockAlignment start="-1,0" stop="-1,-1" value="right"/>
    </blockTableStyle>
    <blockTableStyle id="payables">
      <blockAlignment start="-1,0" stop="-1,-1" value="right"/>
    </blockTableStyle>
  </stylesheet>

  <story>
    <para style="title">Parents</para>
    <blockTable alignment="left">
      {parents}
    </blockTable>

    <para style="title">Students</para>
    <blockTable alignment="left" style="students">
      {students}
    </blockTable>

    <para style="title">Make checks payable to:</para>
    <blockTable alignment="left" style="payables">
      {payables}
    </blockTable>

  </story>

</document>
"""
PARAGRAPH_TEMPLATE = '<para style="{style}">{msg}</para>'

logging.basicConfig()
logger = logging.getLogger(app_config.APP_NAME)
logger.setLevel(logging.INFO)


def pad_str(s, n):
    s += ' '
    return s + '_' * (n - len(s))


def generate_invoices(families, class_map, progress):
    try:
        for n, family in enumerate(families.values()):
            if progress.WasCancelled():
                break
            msg = "Please wait...\n\n" \
                f"Generating invoice for family: {family['last_name']}"
            wx.CallAfter(progress.Update, n, newmsg=msg)
            if get_students(family):
                with open(f'invoice{n + 1:03}.pdf', 'wb') as f:
                    f.write(create_invoice(family, class_map))
    except Exception as e:
        error_msg = "Error while generating invoices: " + str(e)
        traceback.print_exc()
    wx.CallAfter(progress.EndModal, 0)
    wx.CallAfter(progress.Destroy)


def generate_table_row_rml(elements, style=None):
    style_open = ''
    style_close = ''
    if style is not None:
        style_open = f'<para style="{style}">'
        style_close = '</para>'

    row = '<tr>\n'
    for elt in elements:
        row += f'<td>{style_open}{elt}{style_close}</td>\n'
    row += '</tr>\n'
    return row


def generate(invoice, filename):
    now = datetime.datetime.now()

    parents_rml = ''
    for parent in invoice['parent']:
        parents_rml += generate_table_row_rml(parent)

    column_headers = ['Student', 'Class', 'Instructor', 'Fee']
    students_rml = generate_table_row_rml(column_headers)
    num_classes = 0
    for student_name, classes in invoice['students'].items():
        for class_entry in classes:
            students_rml += generate_table_row_rml([student_name]
                                                   + class_entry[:-1]
                                                   + ['$' + str(class_entry[-1])])
            student_name = ''  # Only print student on first row
            num_classes += 1
    students_rml += generate_table_row_rml(['Total',
                                            '',
                                            '',
                                            '$' + str(invoice['total'])])

    payables_rml = ''
    for teacher, fee in sorted(invoice['payable'].items()):
        payables_rml += generate_table_row_rml([teacher, '$' + str(fee)])

    rml = INVOICE_RML_TEMPLATE.format(parents=parents_rml,
                                      students=students_rml,
                                      payables=payables_rml,
                                      num_classes=num_classes + 1,
                                      date=now.strftime('%a %b %d, %Y'),
                                      filename=filename)
    # print('rml:', rml)

    input_buf = io.StringIO(rml)
    output_buf = MyBytesIO()
    rml2pdf.go(input_buf, outputFileName=output_buf)
    doc = output_buf.getvalue()
    output_buf.real_close()

    return doc


def create_invoice(family, class_map):
    invoice = {}
    parents = get_parents(family)
    students = get_students(family)
    invoice['parent'] = []
    for parent in parents:
        invoice['parent'].append([
            parent[Column.LAST_NAME] + ', ' + parent[Column.FIRST_NAME],
            parent[Column.EMAIL]])
    payable = {}
    invoice['students'] = {}
    invoice['total'] = Decimal(0.00)
    for student in students:
        name = student[Column.LAST_NAME] + ', ' + student[Column.FIRST_NAME]
        invoice['students'][name] = []
        for class_name in student[Column.CLASSES]:
            teacher, fee = class_map[class_name]
            invoice['students'][name].append([class_name, teacher, fee])
            invoice['total'] += fee
            try:
                payable[teacher] += fee
            except KeyError:
                payable[teacher] = fee
    invoice['payable'] = payable
    return generate(invoice, 'invoice.pdf')
