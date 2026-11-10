"""Render a twentysecondcv export and publish its PDF only after layout checks."""
from content import experience_bullets
from pathlib import Path
from string import Template
from urllib.parse import urlsplit
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def english(value):
    return value['en'] if isinstance(value, dict) else value


def tex(value):
    """Escape plain text in one pass, without escaping our own replacement macros."""
    replacements = {
        '\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
        '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
        '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
        '\n': ' ', '\r': ' ', '\t': ' ',
    }
    return ''.join(replacements.get(char, char) for char in str(english(value)))


def link(url, label):
    if urlsplit(url).scheme not in {'https', 'http', 'mailto'}:
        raise ValueError(f'Unsupported resume link: {url!r}')
    if any(char.isspace() or ord(char) < 32 or char in '\\{}' for char in url):
        raise ValueError(f'Invalid characters in resume link: {url!r}')
    escaped = ''.join('\\' + char if char in '%&#_$' else char for char in url)
    return r'\href{' + escaped + '}{' + tex(label) + '}'


def academic_text(data, key):
    return '; '.join(
        r'\textbf{' + tex(item['title']) + '}: ' + tex(item['text']).rstrip('.')
        for item in data.get(key, [])
    ) + '.'


def render_resume(data):
    jobs = []
    for job in data['experience']:
        bullets = experience_bullets(data, job, 'en')
        start, end = english(job['period']).split(' — ', 1)
        jobs.append(
            r'\twentyitem{' + tex(start + ' —') + '}{' + tex(end) + '}{' + tex(job['role'])
            + '}{' + link(job['url'], job['company']) + '}{}{\n'
            + '\\begin{itemize}\n'
            + '\n'.join(r'\item ' + tex(bullet) for bullet in bullets)
            + '\n\\end{itemize}}\\\\[5pt]'
        )
    contacts = [link('mailto:' + data['email'], data['email'])]
    contacts.append(link(data['website'], urlsplit(data['website']).netloc + urlsplit(data['website']).path.rstrip('/')))
    contacts.extend(link(contact['url'], contact['label']) for contact in data['contacts'])
    sidebar_rows = [r'\textcolor{mainblue}{\faIcon{map-marker-alt}} & ' + tex(data['location']) + r'\\[4pt]']
    sidebar_rows.extend([
        r'\textcolor{mainblue}{\faIcon{envelope}} & ' + contacts[0] + r'\\[4pt]',
        r'\textcolor{mainblue}{\faIcon{globe}} & ' + contacts[1] + r'\\[4pt]',
    ])
    icons = {'LinkedIn': 'linkedin', 'Telegram': 'telegram', 'GitHub': 'github'}
    for contact in data['contacts']:
        icon = icons.get(contact['label'], 'link')
        sidebar_rows.append(r'\textcolor{mainblue}{\faIcon{' + icon + '}} & ' + link(contact['url'], contact['label']) + r'\\[4pt]')
    education = '\n'.join(
        r'\textbf{' + tex(item['school']) + r'}\\ ' + tex(item['text'])
        + (r'\\ ' + tex(item['year']) if re.fullmatch(r'\d{4}', item['year']) else '') + r'\par\vspace{5pt}' for item in data['education']
    )
    # The "Exploring next" group is not a claim of existing technical proficiency.
    skills = '\n'.join(
        r'\textbf{' + tex(group['label']) + ':} '
        + ', '.join(tex(item) for item in group['items']) + r'\par\vspace{4pt}'
        for group in data['skills'] if group.get('id') != 'interests'
    )
    values = {key: tex(data[key]) for key in ['name', 'role', 'location', 'about', 'languages']}
    values.update(
        contacts=r'\enspace\textbar\enspace '.join(contacts),
        experience='\n'.join(jobs), education=education, skills=skills,
        publicationTitle=tex(data['researchTitle']),
        publicationVenue=tex(data['publicationVenue']),
        sidebarContacts=r'\\[4pt]'.join(contacts),
        contactRows='\n'.join(sidebar_rows),
        training=academic_text(data, 'training'), awards=academic_text(data, 'mathematicsAwards'),
        certificatesLink=link(data['certificatesUrl'], 'Certificates and diplomas · Yandex Disk'),
        publicationLink=link(data['researchUrl'], 'DOI: ' + data['researchUrl'].removeprefix('https://doi.org/')),
    )
    return Template((ROOT / 'scripts/resume.tex.template').read_text()).substitute(values)


def validate_pdf(path, log):
    info = subprocess.run(['pdfinfo', str(path)], text=True, capture_output=True, check=True).stdout
    pages = re.search(r'^Pages:\s+(\d+)', info, re.MULTILINE)
    if not pages or int(pages[1]) != 1:
        count = pages[1] if pages else 'unknown'
        raise ValueError(
            f'Resume has {count} pages; exactly one A4 page is required. '
            'Shorten content.json; the font size will not be reduced. Previous website PDF was kept.'
        )
    size = re.search(r'^Page size:\s+([\d.]+) x ([\d.]+)', info, re.MULTILINE)
    if not size or abs(float(size[1]) - 595.276) > 1 or abs(float(size[2]) - 841.89) > 1:
        raise ValueError('Resume must use portrait A4. Previous website PDF was kept.')
    if re.search(r'Overfull \\[hv]box|Missing character:', log):
        raise ValueError('Resume has overflowing text or missing glyphs. Inspect build/resume/*.log; previous website PDF was kept.')


def build_resume(data, root=ROOT):
    root = Path(root)
    for command in ['pdflatex', 'pdfinfo']:
        if not shutil.which(command):
            raise RuntimeError(f'{command} is required for PDF generation. See README.md, or use --site-only.')
    source = root / 'generated/ainur-karimov-cv.tex'
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(render_resume(data))
    # Export the original class and portrait alongside the generated .tex.
    shutil.copyfile(ROOT / 'twentysecondcv.cls', source.parent / 'twentysecondcv.cls')
    shutil.copyfile(ROOT / 'photo.jpeg', source.parent / 'photo.jpeg')
    build = root / 'build/resume'
    build.mkdir(parents=True, exist_ok=True)
    command = ['pdflatex', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error',
               '-file-line-error', f'-output-directory={build}', str(source)]
    for _ in range(2):
        result = subprocess.run(command, cwd=source.parent, text=True, capture_output=True)
        if result.returncode:
            if 'RESUME-SIDEBAR-OVERFLOW' in result.stdout:
                raise ValueError('Resume sidebar exceeds one A4 page. Shorten content.json; previous website PDF was kept.')
            raise RuntimeError('LaTeX compilation failed; previous website PDF was kept.\n' + result.stdout[-4000:])
    pdf = build / 'ainur-karimov-cv.pdf'
    validate_pdf(pdf, (build / 'ainur-karimov-cv.log').read_text())
    destination = root / 'site/assets/ainur-karimov-cv.pdf'
    destination.parent.mkdir(parents=True, exist_ok=True)
    # Atomic replacement: readers never receive an incomplete or invalid PDF.
    with tempfile.NamedTemporaryFile(dir=destination.parent, suffix='.pdf', delete=False) as temp:
        temporary = Path(temp.name)
    try:
        shutil.copyfile(pdf, temporary)
        temporary.chmod(0o644)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    print(f'Built {source.relative_to(root)}')
    print(f'Built {destination.relative_to(root)} — 1 page, A4, twentysecondcv')
    return destination
