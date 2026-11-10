# Исходное резюме Twenty Seconds — до появления сайта

Эта ветка `archive/twenty-seconds-original` основана на коммите `5ec67144a15f4051bd4e62dea797c5c2bb1a2bf9`, непосредственно перед первым коммитом сайта `31b599f`.

Исходники `cv_karimov_ainur.tex`, `twentysecondcv.cls` и `photo.jpeg` сохранены без изменений. `cv_karimov_ainur.pdf` — исходный PDF, который находился в рабочей папке до разработки сайта; он мог быть собран из более раннего текста. Для PDF из сохранённого `.tex` выполните сборку ниже. Здесь нет генератора из JSON и файлов сайта.

## Просмотр и сборка

Уже сохранённый PDF: `cv_karimov_ainur.pdf`.

Ubuntu/Debian:

```bash
sudo apt-get install texlive-latex-base texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra texlive-lang-cyrillic lmodern poppler-utils
mkdir -p /tmp/cv-original-build
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/cv-original-build cv_karimov_ainur.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/cv-original-build cv_karimov_ainur.tex
```

Готовый файл: `/tmp/cv-original-build/cv_karimov_ainur.pdf`. Исторический PDF в репозитории не перезаписывается.

Основная версия сайта и простого PDF находится в `main`. Более поздний вариант Twenty Seconds, который умеет брать свежие данные из `content.json`, — в `archive/twenty-seconds`.
