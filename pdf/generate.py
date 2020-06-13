import datetime
import io
import logging
from decimal import Decimal

from z3c.rml import rml2pdf

from model.columns import Column
from model.family import get_parents, get_students

RML_BEGIN_TEMPLATE_PORTRAIT = """<!DOCTYPE document SYSTEM "rml_1_0.dtd">
<document filename="master.pdf" invariant="1">

  <template pagesize="letter" leftMargin="72">
    <pageTemplate id="main" pagesize="letter portrait">
      <pageGraphics>
        <setFont name="Times-Roman" size="24"/>
        <drawString x="35" y="760">{title}</drawString>
        <setFont name="Times-Roman" size="12"/>
        <drawString x="35" y="740">Generated on {date}</drawString>
        <drawString x="35" y="30">{footer}</drawString>
      </pageGraphics>
      <frame id="second" x1="35" y1="45" width="525" height="675"/>
    </pageTemplate>
  </template>
"""

RML_BEGIN_TEMPLATE_LANDSCAPE = """<!DOCTYPE document SYSTEM "rml_1_0.dtd">
<document filename="master.pdf" invariant="1">

  <template pagesize="letter" leftMargin="72">
    <pageTemplate id="main" pagesize="letter landscape">
      <pageGraphics>
        <setFont name="Times-Roman" size="24"/>
        <drawString x="45" y="576">{title}</drawString>
        <setFont name="Times-Roman" size="12"/>
        <drawString x="45" y="556">Generated on {date}</drawString>
        <drawString x="35" y="30">{footer}</drawstring>
      </pageGraphics>
      <frame id="second" x1="45" y1="35" width="705" height="495"/>
    </pageTemplate>
  </template>
"""

RML_STYLESHEET = """\
  <stylesheet>
    <initialize>
      <alias id="style.normal" value="style.Normal"/>
    </initialize>
    <paraStyle name="title" fontName="Times-Bold" fontSize="14" leading="12"
               spaceBefore="10" spaceAfter="10"/>
    <paraStyle name="header" fontName="Times-Roman" fontSize="14" leading="12"
               spaceBefore="12" spaceAfter="12"/>
    <paraStyle name="normal" fontName="Times-Roman" fontSize="10" leading="12"/>
    <paraStyle name="bold" fontName="Times-Bold" fontSize="10" leading="12"/>
    <paraStyle name="medium" fontName="Times-Roman" fontSize="10" leading="12"
               spaceBefore="10"/>
    <paraStyle name="small" fontName="Times-Roman" fontSize="8" leading="12"/>
    <blockTableStyle id="studentsMaster">
      <blockFont name="Times-Roman" size="8" start="0,0" stop="-1,0"/>
      <blockFont name="Times-Roman" size="10" start="0,1" stop="-1,-1"/>
      <blockFont name="Times-Bold" size="10" start="0,-1" stop="-1,-1"/>
      <lineStyle kind="LINEBEFORE" colorName="black" start="1,0" stop="-1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="black" start="0,0" stop="-1,-2"/>
      <blockAlignment start="1,0" stop="-1,-1" value="center"/>
      <blockAlignment start="1,1" stop="-1,-1" value="right"/>
      <blockTopPadding length="0"/>
      <blockBottomPadding length="2"/>
    </blockTableStyle>
    <blockTableStyle id="studentsInvoice">
      <blockFont name="Times-Bold" size="10" start="0,0" stop="-1,0"/>
      <blockFont name="Times-Roman" size="10" start="0,1" stop="-1,-1"/>
      <blockFont name="Times-Bold" size="10" start="0,-1" stop="-1,-1"/>
      <lineStyle kind="LINEBELOW" colorName="black" start="0,0" stop="-1,0"/>
      <lineStyle kind="LINEABOVE" colorName="black" start="0,-1" stop="-1,-1"/>
      <blockAlignment start="-1,0" stop="-1,-1" value="right"/>
      <blockTopPadding length="0"/>
      <blockBottomPadding length="2"/>
    </blockTableStyle>
    <blockTableStyle id="payables">
      <blockAlignment start="-1,0" stop="-1,-1" value="right"/>
      <blockFont name="Times-Roman" size="10"/>
      <blockTopPadding length="0"/>
      <blockBottomPadding length="2"/>
    </blockTableStyle>
    <blockTableStyle id="basic">
      <blockFont name="Times-Roman" size="10"/>
      <blockTopPadding length="0"/>
      <blockBottomPadding length="2"/>
    </blockTableStyle>
  </stylesheet>

  <story>
"""

RML_INVOICE_TEMPLATE = """\
    <para style="title">Parents</para>
    <blockTable alignment="left" style="basic">
      {parents}
    </blockTable>

    <para style="title">Students</para>
    <blockTable alignment="left" style="studentsInvoice">
      {students}
    </blockTable>

    <para style="title">Make checks payable to:</para>
    <blockTable alignment="left" style="payables">
      {payables}
    </blockTable>
"""

RML_NEXT_PAGE = """\
    <nextPage/>
"""
RML_END_TEMPLATE = """\
  </story>

</document>
"""

RML_HORIZONTAL_LINE = """\
<hr width="80%" thickness="1" color="black" spaceAfter="5" spaceBefore="10" align="left"/>
"""

RML_PARAGRAPH_TEMPLATE = '<para style="{style}">{msg}</para>'

RML_MASTER_FAMILY_TEMPLATE = """\
    <keepTogether>
    <para style="header"><b>{last_name}</b>, <font size="10">{parents}</font></para>
    <blockTable alignment="left" style="studentsMaster">
      {students}
    </blockTable>
    </keepTogether>
"""

logger = logging.getLogger(f'classinvoices.{__name__}')


def generate_master_rml_for_family(family, class_map, rml_file):
    # Set of all last names in family. Normally just one.
    last_names = set()

    # Create list of parent first names
    parents = []
    for parent in family['parents']:
        last_names.add(parent[Column.LAST_NAME].strip())
        parents.append(parent[Column.FIRST_NAME].strip())
    parents_rml = ', '.join(sorted(parents))

    # Create map of teacher name to column number
    teacher_map = {}
    columns = ['']
    num_cols = 1
    for student in family['students']:
        for class_name in student[Column.CLASSES]:
            teacher, fee = class_map[class_name]
            if not teacher:
                continue
            if teacher not in teacher_map:
                words = teacher.strip().split()
                teacher_wrapped = words[0].strip() + '\n' + ' '.join(words[1:]).strip()
                columns.append(teacher_wrapped)
                teacher_map[teacher] = num_cols
                num_cols += 1

    # Create student class table rows
    students_rml = generate_table_row_rml(columns)
    totals = ['Total'] + [Decimal(0.00)] * (len(columns) - 1)
    for student in family['students']:
        row = [''] * len(columns)
        row[0] = student[Column.FIRST_NAME].strip()
        for class_name in student[Column.CLASSES]:
            teacher, fee = class_map[class_name]
            if not teacher:
                continue
            col = teacher_map[teacher.strip()]
            if not row[col]:
                row[col] = fee
            else:
                row[col] += fee
            totals[col] += fee
        students_rml += generate_table_row_rml(row)
    students_rml += generate_table_row_rml(totals)

    # Format the data collected above into RML
    rml = RML_MASTER_FAMILY_TEMPLATE.format(last_name=', '.join(sorted(last_names)),
                                            parents=parents_rml,
                                            students=students_rml)
    rml_file.write(rml)


def generate_master(families, class_map, term, output_file):
    rml = io.StringIO()
    start_rml(rml,
              template=RML_BEGIN_TEMPLATE_PORTRAIT,
              title='Class Enrollment Master List',
              term=term,
              footer='Page <pageNumber/>')
    for family in families.values():
        if get_students(family):
            generate_master_rml_for_family(family, class_map, rml)
    finish_rml(rml)
    # logger.debug('rml: %s', rml.getvalue())
    rml.seek(0)
    rml2pdf.go(rml, outputFileName=output_file)


def create_invoice_object(family, class_map, note):
    """Create an invoice object from a family object.
    Formats names and emails, collates classes by teacher, and sums
    class fees by teacher."""
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
    invoice['note'] = note
    for student in students:
        name = student[Column.LAST_NAME] + ', ' + student[Column.FIRST_NAME]
        invoice['students'][name] = []
        for class_name in student[Column.CLASSES]:
            teacher, fee = class_map[class_name]
            # Ensure fee has two digits after the decimal:
            fee += Decimal('0.00')
            invoice['students'][name].append([class_name, teacher, fee])
            invoice['total'] += fee
            try:
                payable[teacher] += fee
            except KeyError:
                payable[teacher] = fee
    invoice['payable'] = payable
    return invoice


def generate_one_invoice(family, class_map, note, term, output_file):
    rml = io.StringIO()
    start_rml(rml,
              template=RML_BEGIN_TEMPLATE_PORTRAIT,
              title='Class Enrollment Invoice',
              term=term)
    invoice = create_invoice_object(family, class_map, note)
    generate_invoice_page_rml(invoice, rml)
    finish_rml(rml)
    rml.seek(0)
    rml2pdf.go(rml, outputFileName=output_file)


def generate_invoices(progress, families, class_map, note, term, output_file):
    rml = io.StringIO()
    start_rml(rml,
              template=RML_BEGIN_TEMPLATE_PORTRAIT,
              title='Class Enrollment Invoice',
              term=term)
    for n, family in enumerate(families.values()):
        if progress.WasCancelled():
            break
        msg = "Please wait...\n\n" \
              f"Generating invoice for family: {family['last_name']}"
        # logger.debug(f'updating progress {n}: {msg}')
        progress.Update(n, newmsg=msg)
        students = get_students(family)
        if students:
            logger.debug(f'processing {len(students)} students in family {n}: {family["last_name"]}')
            invoice = create_invoice_object(family, class_map, note)
            generate_invoice_page_rml(invoice, rml)
    finish_rml(rml)
    # logger.debug('rml: %s', rml.getvalue())
    rml.seek(0)
    rml2pdf.go(rml, outputFileName=output_file)


def start_rml(rml_file, template, title, term, footer=''):
    if term:
        term = f' ({term})'
    else:
        term = ''
    now = datetime.datetime.now()
    rml_file.write(template.format(date=now.strftime('%a %b %d, %Y'),
                                   footer=footer,
                                   title=title + term))
    rml_file.write(RML_STYLESHEET)


def finish_rml(rml_file):
    rml_file.write(RML_END_TEMPLATE)


def generate_invoice_page_rml(invoice, rml_file):
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
        if fee:
            payables_rml += generate_table_row_rml([teacher, '$' + str(fee)])

    rml = RML_INVOICE_TEMPLATE.format(parents=parents_rml,
                                      students=students_rml,
                                      payables=payables_rml,
                                      note=invoice['note'],
                                      num_classes=num_classes + 1,
                                      filename='invoice.pdf')
    rml_file.write(rml)

    # Add note to RML
    rml_file.write(RML_HORIZONTAL_LINE)
    for line in invoice['note'].split('\n'):
        rml_file.write(RML_PARAGRAPH_TEMPLATE.format(style='medium', msg=line))
    rml_file.write(RML_NEXT_PAGE)


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
