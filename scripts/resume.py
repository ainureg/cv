"""Render a simple one-column resume and publish its PDF only after layout checks."""
from content import experience_bullets, experience_entries
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
    for job in experience_entries(data):
        bullets = experience_bullets(data, job, 'en')
        jobs.append(
            r'\job{' + link(job['url'], job['company']) + '}{' + tex(job['role'])
            + '}{' + tex(job['period']) + '}\n'
            + '\\begin{itemize}\n'
            + '\n'.join(r'\item ' + tex(bullet) for bullet in bullets)
            + '\n\\end{itemize}\\vspace{1pt}'
        )
    contacts = [link('mailto:' + data['email'], data['email'])]
    contacts.append(link(data['website'], urlsplit(data['website']).netloc + urlsplit(data['website']).path.rstrip('/')))
    contacts.extend(link(contact['url'], contact['label']) for contact in data['contacts'])
    education = '\n'.join(
        r'\educationentry{' + tex(item['school']) + '}{' + tex(item['text'])
        + '}{' + (tex(item['year']) if re.fullmatch(r'\d{4}', item['year']) else '') + '}'
        for item in data['education']
    )
    # The "Exploring next" group is not a claim of existing technical proficiency.
    skills = '\n'.join(
        r'\textbf{' + tex(group['label']) + ':} '
        + ', '.join(tex(item) for item in group['items']) + r'\par\vspace{1pt}'
        for group in data['skills'] if group.get('id') != 'interests'
    )
    values = {key: tex(data[key]) for key in ['name', 'role', 'location', 'about', 'languages']}
    values.update(
        contacts=r'\enspace\textbar\enspace '.join(contacts),
        experience='\n'.join(jobs), education=education, skills=skills,
        training=academic_text(data, 'training'), awards=academic_text(data, 'mathematicsAwards'),
        certificatesLink=link(data['certificatesUrl'], 'Certificates and diplomas · Yandex Disk'),
        publicationTitle=tex(data['researchTitle']),
        publicationVenue=tex(data['publicationVenue']),
        publicationLink=link(data['researchUrl'], 'DOI: ' + data['researchUrl'].removeprefix('https://doi.org/')),
    )
    return Template((ROOT / 'src/resume.tex.template').read_text()).substitute(values)


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


def build_resume(data, root=ROOT / 'build'):
    root = Path(root)
    for command in ['pdflatex', 'pdfinfo']:
        if not shutil.which(command):
            raise RuntimeError(f'{command} is required for PDF generation. See README.md for installation instructions.')
    source = root / 'resume/ainur-karimov-cv.tex'
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_text(render_resume(data))
    build = root / 'resume'
    build.mkdir(parents=True, exist_ok=True)
    for extension in ('aux', 'out', 'toc'):
        (build / f'ainur-karimov-cv.{extension}').unlink(missing_ok=True)
    command = ['pdflatex', '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error',
               '-file-line-error', f'-output-directory={build}', str(source)]
    for _ in range(2):
        result = subprocess.run(command, cwd=source.parent, text=True, capture_output=True)
        if result.returncode:
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
    print(f'Built {destination.relative_to(root)} — 1 page, A4, simple layout')
    return destination
