"""Resolve shared facts used by both website and PDF renderers."""


def presentations(data, ids):
    by_id = {item['id']: item for item in data.get('presentations', [])}
    return [by_id[item_id] for item_id in ids]


def experience_bullets(data, job, language):
    return list(job['bullets'][language]) + [
        item['statement'][language]
        for item in presentations(data, job.get('presentationIds', []))
    ]


def experience_entries(data):
    for job in data['experience']:
        company = data['companies'][job['companyId']]
        yield {**job, 'company': company['name'], 'url': company['url'], 'logo': company.get('logo')}
