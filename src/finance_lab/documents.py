"""Deterministic report structure. Full decoded reports are transient, not public."""
from dataclasses import dataclass, replace
import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile
import fitz


def norm(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


def section(text):
    value = norm(text)
    if any(value.startswith(x) for x in ('consolidatedbalancesheet', 'consolidatedstatementoffinancialposition',
                               'consolidatedstatementsoffinancialposition')) or value == 'balancesheets':
        return 'balance'
    if any(value.startswith(x) for x in ('consolidatedstatementofcashflow', 'consolidatedstatementsofcashflow')) \
            or value in ('cashflowstatements', 'cashflowsstatements', 'statementsofcashflows'):
        return 'cashflow'
    if any(value.startswith(x) for x in ('consolidatedstatementsofincome', 'consolidatedstatementofincome',
                               'consolidatedstatementsofoperations', 'consolidatedstatementofoperations',
                               'consolidatedstatementsofcomprehensiveincome', 'consolidatedstatementofcomprehensiveincome')) \
            or value in ('incomestatements', 'statementsofincome','comprehensiveincomestatements'):
        return 'income'
    return None


@dataclass(frozen=True)
class Token:
    text: str
    left: float
    right: float


@dataclass(frozen=True)
class Row:
    locator: str
    text: str
    tokens: tuple
    section: str | None
    group: str
    width: float


def checked_bytes(path, expected_sha):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha:
        raise ValueError('Source hash mismatch: ' + str(path))
    return raw


def read_docx(path, expected_sha):
    raw = checked_bytes(path, expected_sha)
    import io
    ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.testzip() is not None:
            raise ValueError('DOCX CRC failed')
        root = ET.fromstring(archive.read('word/document.xml'))
    body = root.find('w:body', ns)
    rows, active, table_index = [], None, 0
    for child in body:
        if child.tag.endswith('}p'):
            text = ''.join(x.text or '' for x in child.findall('.//w:t', ns)).strip()
            if not text:
                continue
            found = section(text)
            if found is not None:
                active = found
            elif norm(text).startswith(('notestofinancialstatements','notestoconsolidatedfinancialstatements')) \
                    or ('equitystatements' in norm(text) and len(text)<100):
                active = None
        elif child.tag.endswith('}tbl'):
            table_index += 1
            group = 'table:' + str(table_index)
            for row_index, tr in enumerate(child.findall('w:tr', ns), 1):
                tokens, column = [], 0
                for tc in tr.findall('w:tc', ns):
                    text = ' '.join(''.join(x.text or '' for x in p.findall('.//w:t', ns))
                                    for p in tc.findall('w:p', ns)).strip()
                    span = tc.find('w:tcPr/w:gridSpan', ns)
                    size = int(span.attrib['{'+ns['w']+'}val']) if span is not None else 1
                    if text:
                        tokens.append(Token(text, column, column+size))
                    column += size
                text = ' | '.join(t.text for t in tokens)
                rows.append(Row(group+':row:'+str(row_index), text, tuple(tokens), active, group, column))
    return rows


def read_pdf(path, expected_sha):
    raw = checked_bytes(path, expected_sha)
    rows = []
    with fitz.open(stream=raw, filetype='pdf') as doc:
        if doc.needs_pass:
            raise ValueError('Encrypted source unsupported')
        for page_index, page in enumerate(doc, 1):
            text=page.get_text()
            bad=sum(ord(c)<32 and c not in '\n\r\t' for c in text)
            use_ocr=bool(text) and bad/max(1,len(text))>.005
            if use_ocr:
                textpage=page.get_textpage_ocr(dpi=180,full=True)
                words=page.get_text('words',textpage=textpage)
            else:
                words=page.get_text('words')
            words = sorted(words, key=lambda x: ((x[1]+x[3])/2, x[0]))
            bands = []
            for word in words:
                centre = (word[1]+word[3])/2
                if not bands or centre-bands[-1][0] > 2.5:
                    bands.append([centre, [word]])
                else:
                    bands[-1][1].append(word)
            lines = [(y, sorted(items, key=lambda x:x[0])) for y, items in bands]
            # Only a heading near the top establishes the statement's scope.
            headings = [' '.join(w[4] for w in items) for y,items in lines if y<page.rect.height*.28]
            active = next((section(h) for h in headings if len(h)<160 and section(h)), None)
            group = 'page:' + str(page_index)
            for row_index, (y, items) in enumerate(lines, 1):
                tokens = tuple(Token(w[4], w[0], w[2]) for w in items)
                rows.append(Row(group+(':ocr' if use_ocr else '')+':line:'+str(row_index), ' '.join(t.text for t in tokens),
                                tokens, active, group, page.rect.width))
    return main_statement_window(rows)


def main_statement_window(rows):
    """Choose the first bounded three-statement cluster, excluding later notes.

    This is a development-specified structure rule, not supplied gold locators.
    A document lacking a complete cluster keeps no strict statement scope.
    """
    groups={}
    for row in rows:
        groups.setdefault(row.group,[]).append(row)
    eligible=[]
    for group,items in groups.items():
        kind=next((r.section for r in items if r.section),None)
        header=any(len({t.text for t in r.tokens if re.fullmatch(r'20\d{2}',t.text)})>=2
                   for r in items[:25])
        if kind and header:eligible.append((int(group.split(':')[1]),kind))
    bounds=None
    for start,_ in eligible:
        window=[(p,k) for p,k in eligible if start<=p<=start+12]
        seen=set()
        for end,kind in window:
            seen.add(kind)
            if seen=={'income','balance','cashflow'}:
                bounds=(start,end);break
        if bounds:break
    if bounds is None:
        return [replace(row,section=None) for row in rows]
    return [row if bounds[0]<=int(row.group.split(':')[1])<=bounds[1] else replace(row,section=None)
            for row in rows]


def read_document(path, expected_sha):
    if Path(path).suffix.lower() == '.docx':
        return read_docx(path, expected_sha)
    if Path(path).suffix.lower() == '.pdf':
        return read_pdf(path, expected_sha)
    raise ValueError('Unsupported report format')
