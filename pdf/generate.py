import datetime
import io

from z3c.rml import rml2pdf

RML_TEMPLATE = """<!DOCTYPE document SYSTEM "rml_1_0.dtd">
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


def pad_str(s, n):
    s += ' '
    return s + '_' * (n - len(s))


def generate_txt(invoice):
    s = ['====================================================================']
    for parent in invoice['parent']:
        s.append('{:30}  {}'.format(parent[0], parent[1]))
    s.append(' ')
    max_teacher_width = invoice['max_teacher_width']
    for student_name, classes in invoice['students'].items():
        s.append('{:28}'.format(student_name))
        for class_entry in classes:
            class_name = class_entry[0]
            teacher = class_entry[1]
            class_fee = class_entry[2]
            s.append('  {class_name} {teacher} ${fee:6.2f}'.format(
                class_name=pad_str(class_name, invoice['max_class_width']),
                teacher=pad_str(teacher, max_teacher_width),
                fee=class_fee))
    s.append(' ')
    s.append('Make checks payable to:')
    for teacher, fee in sorted(invoice['payable'].items()):
        s.append('{teacher} ${fee:7.2f}'.format(
            teacher=pad_str(teacher, max_teacher_width),
            fee=fee
        ))
    return s


class MyBytesIO(io.BytesIO):
    """BytesIO wrapper to keep buffer after close() is called."""

    def __init__(self) -> None:
        super().__init__()

    def close(self):
        pass

    def real_close(self):
        io.BytesIO.close(self)


def generate_table_row_rml(elements, style=None):
    style_open = ''
    style_close = ''
    if style is not None:
        style_open = '<para style="{style}">'.format(style=style)
        style_close = '</para>'

    row = '<tr>\n'
    for elt in elements:
        row += '<td>{style_open}{cell}{style_close}</td>\n'.format(
            style_open=style_open,
            style_close=style_close,
            cell=elt)
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

    rml = RML_TEMPLATE.format(parents=parents_rml,
                              students=students_rml,
                              payables=payables_rml,
                              num_classes=num_classes+1,
                              date=now.strftime('%a %b %d, %Y'),
                              filename=filename)
    # print('rml:', rml)

    input_buf = io.StringIO(rml)
    output_buf = MyBytesIO()
    rml2pdf.go(input_buf, outputFileName=output_buf)
    doc = output_buf.getvalue()
    output_buf.real_close()

    return doc
