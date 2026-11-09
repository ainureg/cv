# Айнур Каримов · CV

Персональная страница: **https://ainureg.github.io/cv/** · [English](https://ainureg.github.io/cv/en/)

Адаптивный статический сайт на русском и английском, без JavaScript и внешних сервисов. Шрифты, фотография и PDF хранятся в репозитории.

## Как обновлять

1. Отредактировать `content.json`: опыт, навыки, образование, ссылки и тексты на двух языках.
2. Выполнить `python scripts/build.py` (Python 3.13+, без зависимостей).
3. Закоммитить изменения и отправить в `main`. GitHub Actions пересоберёт и опубликует сайт.

Для новых разделов: HTML-шаблон — `scripts/page.html`, генератор — `scripts/build.py`, стили — `site/styles.css`. Готовые страницы находятся в `site/`; их не нужно редактировать вручную. Можно добавлять изображения, проекты и отдельные страницы в эту папку.

## Локальный просмотр

```bash
python scripts/build.py
python -m http.server 8000 --directory site
```

Открыть http://localhost:8000/ или http://localhost:8000/en/.

## GitHub Pages

Одноразовая настройка: **Settings → Pages → Build and deployment → Source → GitHub Actions**.
После включения запустить **Actions → Publish resume → Run workflow**, если первый запуск был до включения Pages.
Дальнейшие изменения в `main` публикуются автоматически.

## PDF

Исходник: `cv_karimov_ainur.tex`, шаблон: `twentysecondcv.cls`. На сайте опубликован PDF, пересобранный из этого исходника. PDF обновляется отдельно от веб-страницы:

```bash
mkdir -p /tmp/cv-build
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/cv-build cv_karimov_ainur.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/cv-build cv_karimov_ainur.tex
cp /tmp/cv-build/cv_karimov_ainur.pdf site/assets/ainur-karimov-cv.pdf
```

Если отсутствует `ClearSans.sty`: `sudo apt install texlive-fonts-extra`.
Inter распространяется по SIL Open Font License, см. `site/assets/Inter-LICENSE.txt`.
