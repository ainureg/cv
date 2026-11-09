"""Build both language versions. Python standard library only."""
from html import escape
from pathlib import Path
import json
from string import Template

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'content.json').read_text())
template = Template((ROOT / 'scripts/page.html').read_text())

COPY = {
    'ru': dict(title='Айнур Каримов — Machine Learning Engineer', navExperience='Опыт', navAbout='Обо мне', navContact='Контакты', location='Казань, Россия', heroLabel='MACHINE LEARNING ENGINEER', contact='Написать мне', download='Резюме PDF', experience='Опыт работы', experienceNote='От статистики к зрению и робототехнике.', skills='Инструменты и интересы', education='Образование', research='Исследования', article='Читать статью', certificates='Сертификаты и дипломы', languages='Языки', elsewhere='За пределами работы', contactTitle='Давайте на связи.', contactText='Обсудить ML, компьютерное зрение или робототехнику — напишите мне.', top='Наверх ↑', source='Исходный код', section='Обо мне', portrait='Айнур Каримов'),
    'en': dict(title='Ainur Karimov — Machine Learning Engineer', navExperience='Experience', navAbout='About', navContact='Contact', location='Kazan, Russia', heroLabel='MACHINE LEARNING ENGINEER', contact='Get in touch', download='Resume PDF', experience='Work experience', experienceNote='From statistics to vision and robotics.', skills='Tools & interests', education='Education', research='Research', article='Read the paper', certificates='Certificates & diplomas', languages='Languages', elsewhere='Beyond work', contactTitle='Let’s connect.', contactText='For conversations about ML, computer vision, or robotics — drop me a line.', top='Back to top ↑', source='Source code', section='About me', portrait='Ainur Karimov')
}

for lang in COPY:
    def local(value):
        return value[lang] if isinstance(value, dict) else value

    def e(value):
        return escape(str(local(value)), quote=True)

    def tags(values):
        return ''.join(f'<span class="tag">{e(v)}</span>' for v in values)

    experience = ''.join(f'''<article class="job">
      <div class="job-date">{e(job['period'])}</div>
      <div class="job-body"><h3><a href="{e(job['url'])}" target="_blank" rel="noopener noreferrer">{e(job['company'])} <span aria-hidden="true">↗︎</span></a></h3>
      <p class="role">{e(job['role'])}</p><p class="job-text">{e(job['text'])}</p>
      <div class="tags">{tags(job['tags'])}</div></div></article>''' for job in data['experience'])
    skills = ''.join(f'<div class="skill-group"><h3>{e(group["label"])}</h3><div class="tags">{tags(group["items"])}</div></div>' for group in data['skills'])
    education = ''.join(f'<article class="education-item"><span class="mono">{e(item["year"])}</span><div><h3>{e(item["school"])}</h3><p>{e(item["text"])}</p></div></article>' for item in data['education'])
    prefix = './' if lang == 'ru' else '../'
    values = {key: escape(value) for key, value in COPY[lang].items()}
    values.update({key: e(data[key]) for key in ['name', 'intro', 'about', 'interests', 'researchText', 'researchUrl', 'certificatesUrl']})
    values.update(lang=lang, prefix=prefix, languageLinks=f'<a href="{prefix}" lang="ru" {"aria-current=\"page\"" if lang == "ru" else ""}>RU</a><span>/</span><a href="{prefix}en/" lang="en" {"aria-current=\"page\"" if lang == "en" else ""}>EN</a>', experienceItems=experience, skillItems=skills, educationItems=education, focus=tags(data['focus']), researchTitle=e(data['research']))
    values['languageList'] = e(data['languages'])
    destination = ROOT / 'site' / ('en/index.html' if lang == 'en' else 'index.html')
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(template.substitute(values))
    print(f'Built {destination.relative_to(ROOT)}')
