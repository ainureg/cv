"""Build the bilingual site and one-page PDF from a shared JSON source."""
from content import experience_bullets, experience_entries, presentations
from html import escape
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from resume import build_resume
from string import Template
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]

def build_site(data, output_root=ROOT):
    template = Template((ROOT / 'scripts/page.html').read_text())

    COPY = {
        'ru': dict(navExperience='Опыт', navAbout='Обо мне', navContact='Контакты', contact='Написать мне', download='Резюме PDF', experience='Опыт работы', experienceNote='От статистики к зрению и робототехнике.', skills='Инструменты и интересы', education='Образование', research='Исследования', article='Читать статью', certificates='Сертификаты и дипломы', languages='Языки', elsewhere='За пределами работы', contactTitle='Давайте на связи.', contactText='Обсудить ML, компьютерное зрение или робототехнику — напишите мне.', top='Наверх ↑', source='Исходный код', section='Обо мне'),
        'en': dict(navExperience='Experience', navAbout='About', navContact='Contact', contact='Get in touch', download='Résumé · PDF', experience='Work experience', experienceNote='From statistics to vision and robotics.', skills='Tools & interests', education='Education', research='Research', article='Read the paper', certificates='Certificates & diplomas', languages='Languages', elsewhere='Beyond work', contactTitle='Let’s connect.', contactText='For conversations about ML, computer vision, or robotics — drop me a line.', top='Back to top ↑', source='Source code', section='About me')
    }

    COPY['en'].update(navProjects='Selected work', projects='A closer look.', projectsNote='Three projects. Different problems. One engineering mindset.', experience='Where I’ve worked', experienceNote='Experience since 2017', contribution='My contribution', projectContext='The project', workflow='Workflow sketch', explore='Explore the work', coauthor='Research co-author', copyEmail='Copy email', copied='Email copied', printResume='Print this page', details='More about the role', profile='Profile', cityView='Camera view', projectionHint='Move the point on the road', groundView='Ground plane', skills='Working toolkit', research='Published research', contactTitle='Have something interesting?', contactText='Computer vision, medical imaging, or robotics. Let’s talk.')
    COPY['ru'].update(navProjects='Проекты', projects='Ближе к делу.', projectsNote='Три проекта. Разные задачи. Инженерный подход.', experience='Где я работал', experienceNote='Опыт с 2017 года', contribution='Мой вклад', projectContext='О проекте', workflow='Схема работы', explore='Посмотреть проекты', coauthor='Соавтор исследования', copyEmail='Скопировать email', copied='Email скопирован', printResume='Распечатать страницу', details='Подробнее о роли', profile='Профиль', cityView='Вид с камеры', projectionHint='Перемещайте точку на дороге', groundView='Вид сверху', skills='Рабочие инструменты', research='Научная публикация', contactTitle='Есть интересная задача?', contactText='Компьютерное зрение, медицинские изображения или робототехника. Давайте обсудим.')
    COPY['en'].update(training='Additional training', mathematicsAwards='Mathematics awards', academicBackground='Training and mathematics awards')
    COPY['ru'].update(training='Дополнительное обучение', mathematicsAwards='Математические достижения', academicBackground='Обучение и математические достижения')

    # Keep /en/ working for existing links; English is canonical at the root.
    PAGES = [('en', 'index.html', './'), ('ru', 'ru/index.html', '../'), ('en', 'en/index.html', '../')]
    for lang, filename, prefix in PAGES:
        def local(value):
            return value[lang] if isinstance(value, dict) else value

        def e(value):
            return escape(str(local(value)), quote=True)

        def tags(values):
            return ''.join(f'<span class="tag">{e(v)}</span>' for v in values)

        def links(values):
            return ''.join(f'<a class="project-link" href="{e(link["url"])}" target="_blank" rel="noopener noreferrer">{e(link["label"])} <span aria-hidden="true">↗︎</span></a>' for link in values)

        def presentation_notes(ids, full_title=False):
            notes = []
            for event in presentations(data, ids):
                label = 'Conference presentation' if lang == 'en' else 'Выступление на форуме'
                link_label = 'Forum programme' if lang == 'en' else 'Программа форума'
                description = event['title'] if full_title else event['statement']
                notes.append(f'<div class="presentation-note"><p class="presentation-label">{e(label)} · {e(event["event"])} {e(event["year"])} · {e(event["location"])}</p><p>{e(description)}</p><a class="text-link" href="{e(event["url"])}" target="_blank" rel="noopener noreferrer">{e(link_label)} ↗︎</a></div>')
            return ''.join(notes)

        def company_logo(job):
            if not job.get('logo'):
                return ''
            return f'<span class="company-logo" data-theme="{e(data['companies'][job['companyId']].get('logoTheme', 'light'))}"><img src="{prefix}{e(job["logo"])}" alt="" aria-hidden="true" width="72" height="28" loading="lazy"></span>'

        experience = ''.join(f'''<li class="job"><div class="job-date">{e(job['period'])}</div>
          <details><summary><span class="job-company">{company_logo(job)}<span>{e(job['company'])}</span></span><span class="role">{e(job['role'])}</span><span class="expand-mark" aria-hidden="true">+</span></summary>
          <div class="job-detail"><ul class="job-bullets">{''.join(f'<li>{e(bullet)}</li>' for bullet in experience_bullets(data, job, lang))}</ul><div class="tags">{tags(job['tags'])}</div><a class="text-link" href="{e(job['url'])}" target="_blank" rel="noopener noreferrer">{e(job['company'])} ↗︎</a></div></details></li>''' for job in experience_entries(data))
        selectors = []
        panels = []
        for index, project in enumerate(data['projects']):
            pid = project['id']
            selected = index == 0
            selectors.append(f'''<button type="button" role="tab" id="tab-{pid}" aria-controls="case-{pid}" aria-selected="{str(selected).lower()}" tabindex="{0 if selected else -1}" data-case="{pid}"><span class="case-number">0{index + 1}</span><span><strong>{e(project['title'])}</strong><small>{e(project['category'])}</small></span><span class="case-arrow" aria-hidden="true">↗︎</span></button>''')
            step_list = local(project['steps'])
            steps = ''.join(f'<li><span>0{i + 1}</span>{e(step)}</li>' for i, step in enumerate(step_list))
            visual = (ROOT / 'scripts' / 'visuals' / f'{pid}.svg').read_text()
            view_control = f'<div class="view-control" role="group" aria-label="{e(COPY[lang]["workflow"])}"><button type="button" aria-pressed="true" data-view="camera">{e(COPY[lang]["cityView"])}</button><button type="button" aria-pressed="false" data-view="ground">{e(COPY[lang]["groundView"])}</button></div>' if pid == 'citysoft' else ''
            projection = f'<div class="projection-controls"><span>{e(COPY[lang]["projectionHint"])}</span><label>x <input type="range" min="0" max="100" value="45" data-axis="x" aria-label="x"></label><label>y <input type="range" min="0" max="100" value="55" data-axis="y" aria-label="y"></label><output class="projection-readout"></output></div>' if pid == 'citysoft' else ''
            panels.append(f'''<article class="case-panel" role="tabpanel" id="case-{pid}" aria-labelledby="tab-{pid}" tabindex="0"{'' if selected else ' hidden'}>
            <div class="case-visual visual-{pid}"><div class="visual-topline"><span>{e(COPY[lang]['workflow'])}</span><span class="visual-coordinates" aria-hidden="true">0{index+1} / {e(project['category'])}</span></div>{visual}{view_control}{projection}<ol class="pipeline">{steps}</ol></div>
            <div class="case-content"><p class="eyebrow">{e(project['context'])}</p><h3>{e(project['subtitle'])}</h3><div class="case-columns"><div><h4>{e(COPY[lang]['contribution'])}</h4><p>{e(project['contribution'])}</p></div><div><h4>{e(COPY[lang]['projectContext'])}</h4><p>{e(project['contextText'])}</p></div></div>{presentation_notes(project.get("presentationIds", []))}<div class="case-bottom"><div class="tags">{tags(project['tags'])}</div><div class="project-links">{links(project['links'])}</div></div></div></article>''')
        projects = '<div class="case-tabs" role="tablist" aria-orientation="vertical" aria-label="' + e(COPY[lang]['projects']) + '">' + ''.join(selectors) + '</div><div class="case-stage">' + ''.join(panels) + '</div>'
        skills = ''.join(f'<div class="skill-group"><h3>{e(group["label"])}</h3><div class="tags">{tags(group["items"])}</div></div>' for group in data['skills'])
        education = ''.join(f'<article class="education-item"><span class="mono">{e(item["year"])}</span><div><h3>{e(item["school"])}</h3><p>{e(item["text"])}</p></div></article>' for item in data['education'])
        def academic_items(items):
            result = []
            for item in items:
                title = e(item['title'])
                if item.get('url'):
                    title = f'<a href="{e(item["url"])}" target="_blank" rel="noopener noreferrer">{title} ↗︎</a>'
                result.append(f'<li><strong>{title}</strong><span>{e(item["text"])}</span></li>')
            return ''.join(result)
        language_links = []
        for code, url in [('en', prefix), ('ru', prefix + 'ru/')]:
            current = ' aria-current="page"' if code == lang else ''
            language_links.append(f'<a href="{url}" lang="{code}" hreflang="{code}"{current}>{code.upper()}</a>')
        values = {key: escape(value) for key, value in COPY[lang].items()}
        values.update({key: e(data[key]) for key in ['name', 'intro', 'about', 'interests', 'researchText', 'researchUrl', 'certificatesUrl', 'orcid', 'researchTitle', 'publicationVenue', 'email']})
        values.update(lang=lang, prefix=prefix, languageLinks='<span>/</span>'.join(language_links), experienceItems=experience, projectItems=projects, skillItems=skills, educationItems=education, focus=tags(data['focus']))
        values.update({contact['label'].lower() + 'Url': e(contact['url']) for contact in data['contacts']})
        values['portrait'] = e(data['name'])
        values['portraitPath'] = e(data['portrait'])
        values['portraitUrl'] = e(urljoin(data['website'], data['portrait']))
        values['siteUrl'] = e(data['website'])
        values['russianUrl'] = e(urljoin(data['website'], 'ru/'))
        values['sourceUrl'] = e(data['sourceUrl'])
        values['heroLabel'] = e(data['role'])
        values['title'] = e(data['name']) + ' — ' + e(data['role'])
        values['location'] = e(data['location'])
        values['copyFailed'] = ('Скопируйте адрес: ' if lang == 'ru' else 'Copy this address: ') + e(data['email'])
        values['researchPresentations'] = presentation_notes([event['id'] for event in data.get('presentations', [])], full_title=True)
        values['languageList'] = e(data['languages'])
        values['trainingItems'] = academic_items(data['training'])
        values['mathematicsAwardItems'] = academic_items(data['mathematicsAwards'])
        values['canonical'] = urljoin(data['website'], 'ru/') if lang == 'ru' else data['website']
        destination = Path(output_root) / 'site' / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        markup = template.substitute(values)
        arrow = '<svg class="external-arrow" viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M4 12 12 4M4 4h8v8"/></svg>'
        destination.write_text(markup.replace('↗︎', arrow))
        print(f'Built {destination.relative_to(output_root)}')


def build_all(content_path=ROOT / 'content.json', output_root=ROOT):
    """Prepare a complete matching HTML/PDF bundle before replacing local outputs."""
    content_path, output_root = Path(content_path), Path(output_root)
    source = content_path.read_bytes()
    data = json.loads(source)
    output_root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.cv-build-', dir=output_root) as directory:
        stage = Path(directory)
        shutil.copytree(ROOT / 'site', stage / 'site')
        for company in data['companies'].values():
            if company.get('logo') and not (stage / 'site' / company['logo']).is_file():
                raise ValueError(f'Missing company logo: {company["logo"]}')
        build_resume(data, root=stage)
        build_site(data, output_root=stage)
        manifest = {
            'built_at': datetime.now(timezone.utc).isoformat(),
            'content_sha256': hashlib.sha256(source).hexdigest(),
            'pdf_pages': 1,
            'files': {
                name: hashlib.sha256((stage / 'site' / name).read_bytes()).hexdigest()
                for name in ['index.html', 'ru/index.html', 'en/index.html', 'assets/ainur-karimov-cv.pdf']
            },
        }
        (stage / 'site/build.json').write_text(json.dumps(manifest, indent=2) + '\n')
        if content_path.read_bytes() != source:
            raise ValueError('content.json changed during the build. Run the build again; existing outputs were kept.')
        # Save the standalone source for inspection; it is never an input to the build.
        (output_root / 'generated').mkdir(exist_ok=True)
        shutil.copyfile(stage / 'generated/ainur-karimov-cv.tex', output_root / 'generated/ainur-karimov-cv.tex')
        previous = stage / 'previous-site'
        destination = output_root / 'site'
        if destination.exists():
            destination.rename(previous)
        try:
            (stage / 'site').rename(destination)
        except OSError:
            if previous.exists():
                previous.rename(destination)
            raise
    print('Website and one-page PDF built together from content.json.')
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Build the site and its matching one-page English PDF from content.json.")
    parser.parse_args()
    build_all()


if __name__ == '__main__':
    main()
